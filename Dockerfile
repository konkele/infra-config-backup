FROM python:3.13-alpine

# System dependencies
RUN apk add --no-cache \
    git \
    openssh-client \
    ca-certificates

WORKDIR /app

# Copy source code
COPY src/ src/

# Install dependencies first (better caching)
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Default config mount point (Kubernetes-friendly convention)
RUN mkdir -p /config

# Runtime configuration
ENV CONFIG_FILE=/config/config.yaml

# Ensure logs are immediately visible in containers
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["infra-config-backup"]