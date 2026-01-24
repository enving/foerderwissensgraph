# Use official Playwright image (includes Python + Browsers + System Deps)
# This avoids building/installing browsers on the small VPS
FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

WORKDIR /app

# Install basic tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install dependencies (Playwright is already in base image, so we skip it if in requirements)
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

EXPOSE 5001

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uvicorn", "src.api.search_api:app", "--host", "0.0.0.0", "--port", "5001", "--proxy-headers"]
