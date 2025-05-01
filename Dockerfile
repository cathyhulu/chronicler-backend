# Stage 1: Builder
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and .python-version first to leverage Docker caching
COPY pyproject.toml .python-version ./

# Copy source code
COPY . .

# Environment variables
ARG ENV=production
ENV ENV=${ENV}
ENV PYTHONPATH="/app:/app/src:${PYTHONPATH}"
ARG MODEL_DIR=/app/model_weights
ENV MODEL_DIR=${MODEL_DIR}

RUN echo "Building for environment: [${ENV}]"

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    if [ "${ENV}" = "development" ] || [ "${ENV}" = "local" ]; then \
    echo "Installing development dependencies" && \
    uv pip install --no-cache-dir -e .[dev,test]; \
    else \
    echo "Installing production dependencies" && \
    uv pip install --no-cache-dir -e .; \
    fi

# Create MODEL_DIR if it doesn't exist
RUN mkdir -p ${MODEL_DIR}

# Download model
RUN echo "Downloading model to ${MODEL_DIR}/quantized-model" && \
    . /app/.venv/bin/activate && \
    uv run scripts/download_model.py --output-dir ${MODEL_DIR}/quantized-model \
    --verbose

# Give permissions to the model directory
RUN chmod -R 755 ${MODEL_DIR}

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application - conditionally use --reload
CMD ["sh", "-c", ". /app/.venv/bin/activate && \
    if [ \"${ENV}\" = \"development\" ] || [ \"${ENV}\" = \"local\" ]; then \
    echo \"Starting in development mode with hot reload\"; \
    uvicorn src.chronicler_backend.main:app --host 0.0.0.0 --port 8000 --reload; \
    else \
    echo \"Starting in production mode\"; \
    uvicorn src.chronicler_backend.main:app --host 0.0.0.0 --port 8000; \
    fi"]