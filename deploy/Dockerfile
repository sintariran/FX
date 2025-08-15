# FX Trading System - Production Dockerfile
# Multi-stage build for optimal production image

# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (we'll create this)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim as production

# Create non-root user for security
RUN groupadd -r fxtrading && useradd -r -g fxtrading fxtrading

# Set working directory
WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /home/fxtrading/.local

# Copy application code
COPY src/ ./src/
COPY deploy/ ./deploy/

# Set ownership to non-root user
RUN chown -R fxtrading:fxtrading /app

# Switch to non-root user
USER fxtrading

# Add user's local bin to PATH
ENV PATH=/home/fxtrading/.local/bin:$PATH

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Expose port
EXPOSE 8080

# Default command
CMD ["python", "-m", "src.integration.unified_trading_system"]