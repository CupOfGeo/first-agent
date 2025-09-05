FROM python:3.13-slim

# Build arguments for customization
ARG AGENT_NAME=court-cal-agent
ARG AGENT_USER=court-agent
ARG AGENT_DIR=/app

WORKDIR ${AGENT_DIR}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcalcli \
    && rm -rf /var/lib/apt/lists/*

# Copy only what's needed (rest excluded by .dockerignore)
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --frozen

# Default entrypoint - use uv to run with proper environment
ENTRYPOINT ["uv", "run"]

# Default command - specify your agent's main file
CMD ["court-cal-agent/cal.py"]
