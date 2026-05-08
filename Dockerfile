# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies (Java needed to run JVM-based sample bots)
RUN apt-get update && apt-get install -y --no-install-recommends \
    openjdk-21-jdk \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching) by copying only the
# files needed for dependency resolution.
COPY pyproject.toml README.md ./

# Install the project with the test extras so `make test` works inside
# the container. Analysis tooling (pandas/numpy/scipy/matplotlib/seaborn)
# is intentionally NOT installed here to keep the runtime image small;
# install with [analysis] locally for those workflows.
RUN pip install --no-cache-dir --root-user-action=ignore --upgrade pip \
    && pip install --no-cache-dir --root-user-action=ignore ".[test]"

# Now copy the rest of the source tree.
COPY . .

# Make scripts executable
RUN chmod +x scripts/*.sh

# Set PYTHONPATH so engine/bot modules resolve when invoked via subprocess.
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/tools/playgame.py", "--help"]
