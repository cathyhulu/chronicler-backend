# Stage 1: Builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy ALL project metadata files first
COPY pyproject.toml .python-version README.md ./
# If you have any other metadata files (like LICENSE, MANIFEST.in) add them here

# Create src directory structure (if your project needs it)
RUN mkdir -p src

# Create virtual environment
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate

# Copy application code
COPY . .

# Now install dependencies after all files are copied
ARG ENV=production
RUN . /app/.venv/bin/activate && \
    if [ "${ENV}" = "development" ] || [ "${ENV}" = "local" ]; then \
    echo "Installing development dependencies" && \
    uv pip install --no-cache-dir .[dev,test]; \
    else \
    echo "Installing production dependencies" && \
    uv pip install --no-cache-dir .; \
    fi

# Stage 2: Final image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ARG ENV=production
ENV ENV=${ENV}
ENV PYTHONPATH="/app:/app/src:${PYTHONPATH}"
ARG MODEL_DIR=/app/model_weights
ENV MODEL_DIR=${MODEL_DIR}
ENV PATH="/app/.venv/bin:${PATH}"

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy only necessary files from builder stage
COPY --from=builder /app/src /app/src
COPY --from=builder /app/scripts /app/scripts
COPY --from=builder /app/pyproject.toml /app/
COPY --from=builder /app/.python-version /app/
COPY --from=builder /app/README.md /app/

# Create MODEL_DIR if it doesn't exist
RUN mkdir -p ${MODEL_DIR}

# Make entrypoint script executable
RUN chmod +x /app/scripts/entrypoint.sh

# Reduce image size by cleaning up
RUN find /app/.venv -name "*.pyc" -delete && \
    find /app/.venv -name "__pycache__" -delete

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use the entrypoint script
ENTRYPOINT ["/app/scripts/entrypoint.sh"]