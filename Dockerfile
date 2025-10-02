# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    openjdk-21-jdk \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir colorama pytest

# Make scripts executable
RUN chmod +x scripts/*.sh

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/tools/playgame.py", "--help"]
