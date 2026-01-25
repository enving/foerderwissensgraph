# Use official Playwright image (includes Python + Browsers + System Deps)
FROM mcr.microsoft.com/playwright/python:v1.41.2-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install basic system tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Add non-root user
RUN useradd -m -u 1000 graph && \
    mkdir -p /app/data /app/logs /app/docs && \
    chown -R graph:graph /app

# Install Python dependencies separately to cache layers
COPY requirements/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download de_core_news_sm

# Switch to non-root user
USER graph

# Copy application source code
COPY --chown=graph:graph src/ ./src/
COPY --chown=graph:graph config/ ./config/
COPY --chown=graph:graph docs/ ./docs/
COPY --chown=graph:graph scripts/ ./scripts/

EXPOSE 5001

# Command to run the application
CMD ["uvicorn", "src.api.search_api:app", "--host", "0.0.0.0", "--port", "5001", "--proxy-headers"]
