# Water Quality Monitoring App - Dockerfile
# Supports both RPI and CPS versions via VERSION_TYPE env var

FROM python:3.13-slim

# Working directory
WORKDIR /app

# Docker container environment
ENV DOCKER_CONTAINER=true

# Install system packages
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js (for Reflex frontend)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

# Copy requirements first (for better caching)
# Use ARG to choose which requirements file
ARG VERSION_TYPE=RPI
COPY requirements*.txt ./

# Install Python dependencies based on version type
RUN if [ "$VERSION_TYPE" = "CPS" ]; then \
        pip install --no-cache-dir -r requirements.cps.txt; \
    else \
        pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy project files
COPY water_app/ ./water_app/
COPY rxconfig.py .

# Copy .env files
COPY .env.rpi .env.cps ./

# Create .env based on VERSION_TYPE
RUN if [ "$VERSION_TYPE" = "CPS" ]; then \
        cp .env.cps .env; \
    else \
        cp .env.rpi .env; \
    fi

# Initialize Reflex
RUN reflex init --loglevel debug || true

# Expose ports (different for RPI vs CPS)
EXPOSE 13000 13001 13100 13101

# Run app
CMD ["reflex", "run", "--env", "prod", "--backend-host", "0.0.0.0"]
