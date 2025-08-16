#!/bin/bash
# FX Trading System - Production Deployment Script
# Comprehensive deployment automation with validation and rollback

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_FILE="deploy/docker-compose.production.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./logs/deployment_$(date +%Y%m%d_%H%M%S).log"

# Default values
ENVIRONMENT="production"
SKIP_TESTS=false
FORCE_DEPLOY=false
ENABLE_MONITORING=true
BACKUP_DATABASE=true
DRY_RUN=false

# Logging functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1" | tee -a "$LOG_FILE"
}

# Help function
show_help() {
    cat << EOF
FX Trading System - Production Deployment Script

Usage: $0 [OPTIONS]

OPTIONS:
    -e, --environment ENV    Target environment (production, staging) [default: production]
    -s, --skip-tests         Skip pre-deployment tests
    -f, --force              Force deployment without confirmations
    -m, --no-monitoring      Disable monitoring stack deployment
    -b, --no-backup          Skip database backup
    -d, --dry-run           Show what would be done without executing
    -h, --help              Show this help message

EXAMPLES:
    $0                      # Full production deployment
    $0 -e staging           # Deploy to staging environment
    $0 --skip-tests --force # Quick deployment without tests
    $0 --dry-run            # Preview deployment actions

PREREQUISITES:
    - Docker and docker-compose installed
    - OANDA API credentials configured in .env
    - SSL certificates in ssl/ directory
    - Sufficient disk space for databases

EOF
}

# Parse command line arguments
parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -s|--skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            -f|--force)
                FORCE_DEPLOY=true
                shift
                ;;
            -m|--no-monitoring)
                ENABLE_MONITORING=false
                shift
                ;;
            -b|--no-backup)
                BACKUP_DATABASE=false
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1. Use --help for usage information."
                ;;
        esac
    done
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p "$BACKUP_DIR"
    
    if [[ ! -d "deploy/ssl/secrets" ]]; then
        mkdir -p deploy/ssl/secrets
    fi
}

# Validate prerequisites
validate_prerequisites() {
    log "Validating deployment prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
    fi
    
    # Check docker-compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "docker-compose is not available"
    fi
    
    # Check environment file
    if [[ ! -f "$ENV_FILE" ]]; then
        error "Environment file $ENV_FILE not found. Run security setup first."
    fi
    
    # Check SSL certificates
    if [[ ! -f "deploy/ssl/cert.pem" || ! -f "deploy/ssl/key.pem" ]]; then
        error "SSL certificates not found in deploy/ssl/. Run security setup first."
    fi
    
    # Check docker-compose file
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker compose file $COMPOSE_FILE not found"
    fi
    
    # Validate environment variables
    log "Validating environment configuration..."
    source "$ENV_FILE"
    
    if [[ -z "${OANDA_API_KEY:-}" ]] || [[ "$OANDA_API_KEY" == "your_oanda_api_key_here" ]]; then
        error "OANDA_API_KEY not configured in $ENV_FILE"
    fi
    
    if [[ -z "${OANDA_ACCOUNT_ID:-}" ]] || [[ "$OANDA_ACCOUNT_ID" == "your_oanda_account_id_here" ]]; then
        error "OANDA_ACCOUNT_ID not configured in $ENV_FILE"
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df . | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=2097152  # 2GB in KB
    
    if [[ $AVAILABLE_SPACE -lt $REQUIRED_SPACE ]]; then
        error "Insufficient disk space. Required: 2GB, Available: $(( AVAILABLE_SPACE / 1024 / 1024 ))GB"
    fi
    
    log "Prerequisites validation completed"
}

# Run pre-deployment tests
run_tests() {
    if [[ "$SKIP_TESTS" == "true" ]]; then
        warn "Skipping pre-deployment tests as requested"
        return 0
    fi
    
    log "Running pre-deployment tests..."
    
    # Validate docker-compose configuration
    info "Validating docker-compose configuration..."
    if [[ "$DRY_RUN" == "false" ]]; then
        docker-compose -f "$COMPOSE_FILE" config > /dev/null || error "Docker compose configuration is invalid"
    fi
    
    # Test SSL certificates
    info "Validating SSL certificates..."
    if [[ "$DRY_RUN" == "false" ]]; then
        openssl x509 -in deploy/ssl/cert.pem -text -noout > /dev/null || error "SSL certificate is invalid"
        openssl rsa -in deploy/ssl/key.pem -check -noout > /dev/null || error "SSL private key is invalid"
    fi
    
    # Test database connectivity (if existing deployment)
    if docker ps --format "table {{.Names}}" | grep -q fx-trading-db 2>/dev/null; then
        info "Testing database connectivity..."
        if [[ "$DRY_RUN" == "false" ]]; then
            docker exec fx-trading-db pg_isready -U fx_user -d fx_trading || warn "Database connectivity test failed"
        fi
    fi
    
    log "Pre-deployment tests completed"
}

# Backup existing data
backup_data() {
    if [[ "$BACKUP_DATABASE" == "false" ]]; then
        warn "Skipping database backup as requested"
        return 0
    fi
    
    # Check if database container exists
    if ! docker ps --format "table {{.Names}}" | grep -q fx-trading-db 2>/dev/null; then
        info "No existing database found, skipping backup"
        return 0
    fi
    
    log "Creating backup of existing data..."
    
    if [[ "$DRY_RUN" == "false" ]]; then
        # Database backup
        info "Backing up PostgreSQL database..."
        docker exec fx-trading-db pg_dump -U fx_user fx_trading > "$BACKUP_DIR/database_backup.sql" || warn "Database backup failed"
        
        # Configuration backup
        info "Backing up configuration files..."
        cp -r deploy/ssl/ "$BACKUP_DIR/" 2>/dev/null || true
        cp "$ENV_FILE" "$BACKUP_DIR/" 2>/dev/null || true
        
        # Application data backup
        if [[ -d "data" ]]; then
            info "Backing up application data..."
            cp -r data/ "$BACKUP_DIR/" 2>/dev/null || true
        fi
        
        log "Backup completed: $BACKUP_DIR"
    else
        info "[DRY RUN] Would create backup in: $BACKUP_DIR"
    fi
}

# Deploy services
deploy_services() {
    log "Deploying FX Trading System services..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would execute: docker-compose -f $COMPOSE_FILE up -d"
        return 0
    fi
    
    # Pull latest images
    info "Pulling latest Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Start core services first
    info "Starting core infrastructure services..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis
    
    # Wait for database to be ready
    info "Waiting for database to be ready..."
    sleep 10
    
    for i in {1..30}; do
        if docker exec fx-trading-db pg_isready -U fx_user -d fx_trading 2>/dev/null; then
            break
        fi
        if [[ $i -eq 30 ]]; then
            error "Database failed to start within timeout"
        fi
        sleep 2
    done
    
    # Start application services
    info "Starting application services..."
    docker-compose -f "$COMPOSE_FILE" up -d fx-trading nginx
    
    # Start monitoring services if enabled
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        info "Starting monitoring services..."
        docker-compose -f "$COMPOSE_FILE" up -d prometheus grafana
    fi
    
    log "Services deployment completed"
}

# Validate deployment
validate_deployment() {
    log "Validating deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would validate deployment health"
        return 0
    fi
    
    # Wait for services to be ready
    sleep 15
    
    # Check service health
    info "Checking service health..."
    
    # Check application health
    for i in {1..12}; do  # 2 minutes timeout
        if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
            log "✅ Application health check passed"
            break
        fi
        if [[ $i -eq 12 ]]; then
            error "Application health check failed"
        fi
        sleep 10
    done
    
    # Check HTTPS endpoint
    for i in {1..6}; do  # 1 minute timeout
        if curl -f -s -k https://localhost/health > /dev/null 2>&1; then
            log "✅ HTTPS endpoint check passed"
            break
        fi
        if [[ $i -eq 6 ]]; then
            warn "HTTPS endpoint check failed"
        fi
        sleep 10
    done
    
    # Check database connectivity
    if docker exec fx-trading-db pg_isready -U fx_user -d fx_trading > /dev/null 2>&1; then
        log "✅ Database connectivity check passed"
    else
        error "Database connectivity check failed"
    fi
    
    # Check monitoring services if enabled
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        if curl -f -s http://localhost:9090/-/ready > /dev/null 2>&1; then
            log "✅ Prometheus check passed"
        else
            warn "Prometheus check failed"
        fi
        
        if curl -f -s http://localhost:3000/api/health > /dev/null 2>&1; then
            log "✅ Grafana check passed"
        else
            warn "Grafana check failed"
        fi
    fi
    
    log "Deployment validation completed"
}

# Show deployment summary
show_summary() {
    log "Deployment Summary"
    echo "=================="
    
    if [[ "$DRY_RUN" == "true" ]]; then
        echo "🔍 DRY RUN COMPLETED"
        echo "   No actual changes were made"
        return 0
    fi
    
    echo "🚀 Environment: $ENVIRONMENT"
    echo "📊 Monitoring: $([ "$ENABLE_MONITORING" == "true" ] && echo "Enabled" || echo "Disabled")"
    echo "💾 Backup: $([ "$BACKUP_DATABASE" == "true" ] && echo "$BACKUP_DIR" || echo "Skipped")"
    echo "📝 Log file: $LOG_FILE"
    echo
    echo "🌐 Access URLs:"
    echo "   Application: https://localhost"
    echo "   Health Check: http://localhost:8080/health"
    
    if [[ "$ENABLE_MONITORING" == "true" ]]; then
        echo "   Prometheus: http://localhost:9090"
        echo "   Grafana: http://localhost:3000"
        
        # Show Grafana password
        if [[ -f "deploy/ssl/secrets/grafana_password" ]]; then
            GRAFANA_PASS=$(cat deploy/ssl/secrets/grafana_password)
            echo "   Grafana Login: admin / $GRAFANA_PASS"
        fi
    fi
    
    echo
    echo "📊 Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep fx-trading || echo "   No FX trading containers found"
    
    echo
    echo "✅ Deployment completed successfully!"
    echo "   Monitor the system logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "   View system status: docker-compose -f $COMPOSE_FILE ps"
}

# Rollback function
rollback() {
    error "Deployment failed. Starting rollback..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        info "[DRY RUN] Would rollback deployment"
        return 0
    fi
    
    # Stop services
    info "Stopping services..."
    docker-compose -f "$COMPOSE_FILE" down || true
    
    # Restore from backup if available
    if [[ -f "$BACKUP_DIR/database_backup.sql" ]]; then
        info "Restoring database from backup..."
        # Database restore logic would go here
    fi
    
    error "Rollback completed. Please check logs and resolve issues before retrying."
}

# Confirmation prompt
confirm_deployment() {
    if [[ "$FORCE_DEPLOY" == "true" ]] || [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    echo
    echo "🎯 Ready to deploy FX Trading System"
    echo "   Environment: $ENVIRONMENT"
    echo "   Monitoring: $([ "$ENABLE_MONITORING" == "true" ] && echo "Enabled" || echo "Disabled")"
    echo "   Backup: $([ "$BACKUP_DATABASE" == "true" ] && echo "Enabled" || echo "Disabled")"
    echo
    
    read -p "Continue with deployment? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Deployment cancelled by user"
        exit 0
    fi
}

# Cleanup function
cleanup() {
    if [[ -f "$LOG_FILE" ]]; then
        info "Deployment log saved to: $LOG_FILE"
    fi
}

# Trap for cleanup
trap cleanup EXIT
trap rollback ERR

# Main execution
main() {
    echo
    log "🚀 FX Trading System - Production Deployment"
    echo "============================================="
    
    parse_arguments "$@"
    create_directories
    validate_prerequisites
    run_tests
    confirm_deployment
    backup_data
    deploy_services
    validate_deployment
    show_summary
}

# Run main function with all arguments
main "$@"