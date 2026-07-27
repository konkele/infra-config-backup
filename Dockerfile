FROM python:3.13-alpine

# System dependencies
RUN apk add --no-cache \
    git \
    openssh-client \
    ca-certificates

# Create a dedicated non-root runtime user
RUN addgroup -S appuser && \
    adduser -S -G appuser -u 10001 appuser

WORKDIR /app

# Copy source code
COPY src/ src/

# Install dependencies first (better caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Default config mount point (Kubernetes-friendly convention)
RUN mkdir -p /config && \
    chown -R appuser:appuser /app /config

# Runtime configuration
ENV CONFIG_FILE=/config/config.yaml

# Ensure logs are immediately visible in containers
ENV PYTHONUNBUFFERED=1

# Run as non-root
USER 10001:10001

ENTRYPOINT ["infra-config-backup"]