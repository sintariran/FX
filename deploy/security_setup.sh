#!/bin/bash
# FX Trading System - Security Setup Script
# Sets up SSL certificates, secrets, and security configurations

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SSL_DIR="./ssl"
SECRETS_DIR="./secrets"
ENV_FILE=".env"
DOMAIN_NAME="${DOMAIN_NAME:-fx-trading.local}"

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
    exit 1
}

# Generate random string
generate_random_string() {
    local length=${1:-32}
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Create directories
create_directories() {
    log "Creating security directories..."
    mkdir -p "$SSL_DIR"
    mkdir -p "$SECRETS_DIR"
    mkdir -p "./logs"
    mkdir -p "./data"
    
    # Set appropriate permissions
    chmod 700 "$SECRETS_DIR"
    chmod 755 "$SSL_DIR"
}

# Generate SSL certificates
generate_ssl_certificates() {
    log "Generating SSL certificates..."
    
    if [[ -f "$SSL_DIR/cert.pem" && -f "$SSL_DIR/key.pem" ]]; then
        warn "SSL certificates already exist. Skipping generation."
        return 0
    fi
    
    # Create OpenSSL configuration
    cat > "$SSL_DIR/openssl.conf" << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C=JP
ST=Tokyo
L=Tokyo
O=FX Trading System
OU=IT Department
CN=$DOMAIN_NAME

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN_NAME
DNS.2 = localhost
DNS.3 = fx-trading
IP.1 = 127.0.0.1
IP.2 = ::1
EOF
    
    # Generate private key
    openssl genpkey -algorithm RSA -out "$SSL_DIR/key.pem" -pkcs8 -aes256 \
        -pass pass:$(generate_random_string 16) 2>/dev/null || \
    openssl genpkey -algorithm RSA -out "$SSL_DIR/key.pem" -pkcs8
    
    # Generate certificate signing request
    openssl req -new -key "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.csr" \
        -config "$SSL_DIR/openssl.conf"
    
    # Generate self-signed certificate (valid for 1 year)
    openssl x509 -req -in "$SSL_DIR/cert.csr" -signkey "$SSL_DIR/key.pem" \
        -out "$SSL_DIR/cert.pem" -days 365 \
        -extensions v3_req -extfile "$SSL_DIR/openssl.conf"
    
    # Set appropriate permissions
    chmod 600 "$SSL_DIR/key.pem"
    chmod 644 "$SSL_DIR/cert.pem"
    
    # Clean up
    rm -f "$SSL_DIR/cert.csr" "$SSL_DIR/openssl.conf"
    
    log "SSL certificates generated successfully"
    log "Certificate: $SSL_DIR/cert.pem"
    log "Private key: $SSL_DIR/key.pem"
    
    # Display certificate information
    echo
    log "Certificate information:"
    openssl x509 -in "$SSL_DIR/cert.pem" -text -noout | grep -A 1 "Subject:"
    openssl x509 -in "$SSL_DIR/cert.pem" -text -noout | grep -A 1 "Not After"
}

# Generate application secrets
generate_secrets() {
    log "Generating application secrets..."
    
    # Database password
    if [[ ! -f "$SECRETS_DIR/db_password" ]]; then
        generate_random_string 24 > "$SECRETS_DIR/db_password"
        log "Database password generated"
    fi
    
    # Redis password
    if [[ ! -f "$SECRETS_DIR/redis_password" ]]; then
        generate_random_string 24 > "$SECRETS_DIR/redis_password"
        log "Redis password generated"
    fi
    
    # Encryption key (32 characters for AES-256)
    if [[ ! -f "$SECRETS_DIR/encryption_key" ]]; then
        generate_random_string 32 > "$SECRETS_DIR/encryption_key"
        log "Encryption key generated"
    fi
    
    # JWT secret
    if [[ ! -f "$SECRETS_DIR/jwt_secret" ]]; then
        generate_random_string 64 > "$SECRETS_DIR/jwt_secret"
        log "JWT secret generated"
    fi
    
    # Grafana password
    if [[ ! -f "$SECRETS_DIR/grafana_password" ]]; then
        generate_random_string 16 > "$SECRETS_DIR/grafana_password"
        log "Grafana password generated"
    fi
    
    # Set appropriate permissions
    chmod 600 "$SECRETS_DIR"/*
}

# Create environment file
create_environment_file() {
    log "Creating environment file..."
    
    if [[ -f "$ENV_FILE" ]]; then
        warn "Environment file already exists. Creating backup..."
        cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%s)"
    fi
    
    # Read generated secrets
    local db_password=$(cat "$SECRETS_DIR/db_password")
    local redis_password=$(cat "$SECRETS_DIR/redis_password")
    local encryption_key=$(cat "$SECRETS_DIR/encryption_key")
    local jwt_secret=$(cat "$SECRETS_DIR/jwt_secret")
    local grafana_password=$(cat "$SECRETS_DIR/grafana_password")
    
    cat > "$ENV_FILE" << EOF
# FX Trading System - Production Environment Configuration
# Generated on $(date)

# Environment
ENVIRONMENT=production

# Database Configuration
DB_HOST=postgres
DB_PORT=5432
DB_NAME=fx_trading
DB_USER=fx_user
DB_PASSWORD=$db_password

# Redis Configuration
REDIS_PASSWORD=$redis_password

# OANDA API Configuration (FILL IN YOUR VALUES)
OANDA_API_KEY=your_oanda_api_key_here
OANDA_ACCOUNT_ID=your_oanda_account_id_here
OANDA_ENV=practice

# Security Configuration
ENCRYPTION_KEY=$encryption_key
JWT_SECRET=$jwt_secret
SSL_CERT_PATH=/app/ssl/cert.pem
SSL_KEY_PATH=/app/ssl/key.pem

# Trading Configuration
TRADING_INITIAL_BALANCE=1000000
TRADING_MAX_POSITIONS=5
TRADING_MAX_EXPOSURE=500000
TRADING_MAX_DAILY_LOSS=50000
TRADING_MAX_DRAWDOWN=0.05
TRADING_MAX_RISK_PER_TRADE=0.02
TRADING_ALLOWED_SYMBOLS=USDJPY,EURJPY,EURUSD

# Performance Configuration
PERF_NUM_WORKERS=6
PERF_RESPONSE_TARGET_MS=19.0
PERF_MEMORY_LIMIT_MB=1024

# Monitoring Configuration
LOG_LEVEL=INFO
LOG_FILE_PATH=/app/logs/fx_trading.log
ALERT_EMAIL=admin@example.com
SLACK_WEBHOOK_URL=

# Monitoring Passwords
GRAFANA_PASSWORD=$grafana_password

# Alert Thresholds
ALERT_RESPONSE_TIME_MS=50.0
ALERT_ERROR_RATE_PERCENT=5.0
ALERT_MEMORY_USAGE_PERCENT=80.0
ALERT_CPU_USAGE_PERCENT=80.0
ALERT_DRAWDOWN_PERCENT=3.0
EOF
    
    # Set appropriate permissions
    chmod 600 "$ENV_FILE"
    
    log "Environment file created: $ENV_FILE"
    warn "IMPORTANT: Update OANDA_API_KEY and OANDA_ACCOUNT_ID with your actual values!"
}

# Setup file permissions
setup_permissions() {
    log "Setting up file permissions..."
    
    # SSL directory
    find "$SSL_DIR" -type f -name "*.pem" -exec chmod 600 {} \;
    
    # Secrets directory
    find "$SECRETS_DIR" -type f -exec chmod 600 {} \;
    
    # Logs directory (writable by container)
    chmod 755 ./logs
    
    # Data directory (writable by container)
    chmod 755 ./data
    
    log "File permissions configured"
}

# Validate environment
validate_environment() {
    log "Validating environment..."
    
    # Check if Docker is available
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        warn "docker-compose not found, checking for 'docker compose'"
        if ! docker compose version &> /dev/null; then
            error "Neither docker-compose nor 'docker compose' is available"
        fi
    fi
    
    # Check if OpenSSL is available
    if ! command -v openssl &> /dev/null; then
        error "OpenSSL is not installed or not in PATH"
    fi
    
    log "Environment validation passed"
}

# Generate security documentation
generate_documentation() {
    log "Generating security documentation..."
    
    cat > "SECURITY_README.md" << EOF
# FX Trading System - Security Configuration

## Generated Files

### SSL Certificates
- \`ssl/cert.pem\` - SSL certificate (self-signed, valid for 1 year)
- \`ssl/key.pem\` - Private key

### Secrets
- \`secrets/db_password\` - PostgreSQL database password
- \`secrets/redis_password\` - Redis password
- \`secrets/encryption_key\` - Application encryption key (AES-256)
- \`secrets/jwt_secret\` - JWT signing secret
- \`secrets/grafana_password\` - Grafana admin password

### Environment Configuration
- \`.env\` - Main environment configuration file

## Important Security Notes

1. **SSL Certificates**: The generated certificates are self-signed. For production use, obtain certificates from a trusted CA.

2. **Secret Management**: All generated secrets are stored in the \`secrets/\` directory with restrictive permissions (600).

3. **Environment Variables**: The \`.env\` file contains sensitive information and should never be committed to version control.

4. **OANDA API**: Update the OANDA_API_KEY and OANDA_ACCOUNT_ID in the \`.env\` file with your actual credentials.

5. **Firewall**: Ensure your firewall only allows necessary ports (80, 443, and monitoring ports if needed).

## Production Recommendations

1. Use proper SSL certificates from a trusted CA
2. Enable firewall and restrict access to monitoring ports
3. Regularly rotate secrets and passwords
4. Monitor access logs for suspicious activity
5. Keep the system updated with security patches

## Quick Start

1. Update OANDA credentials in \`.env\`
2. Run: \`docker-compose -f deploy/docker-compose.production.yml up -d\`
3. Access: https://localhost (or your domain)
4. Monitor: http://localhost:3000 (Grafana, admin/[generated_password])

Generated on: $(date)
EOF
    
    log "Security documentation created: SECURITY_README.md"
}

# Main execution
main() {
    echo
    log "🔐 FX Trading System - Security Setup"
    echo "======================================"
    echo
    
    validate_environment
    create_directories
    generate_ssl_certificates
    generate_secrets
    create_environment_file
    setup_permissions
    generate_documentation
    
    echo
    log "✅ Security setup completed successfully!"
    echo
    log "📋 Next steps:"
    echo "   1. Review and update .env file with your OANDA credentials"
    echo "   2. For production, replace self-signed certificates with CA-signed ones"
    echo "   3. Run: docker-compose -f deploy/docker-compose.production.yml up -d"
    echo "   4. Read SECURITY_README.md for important security information"
    echo
    
    # Display access information
    log "🔑 Generated passwords:"
    echo "   Database: $(cat "$SECRETS_DIR/db_password")"
    echo "   Redis: $(cat "$SECRETS_DIR/redis_password")"
    echo "   Grafana: admin / $(cat "$SECRETS_DIR/grafana_password")"
    echo
    warn "Store these passwords securely and remove them from terminal history!"
}

# Run main function
main "$@"