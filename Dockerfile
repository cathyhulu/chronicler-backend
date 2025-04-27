FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and .python-version first to leverage Docker caching
COPY pyproject.toml .python-version ./

# Copy the entire src directory 
COPY src/ ./src/
COPY README.md ./

RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install --no-cache-dir -e .[dev,test]

# Final image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Make sure we use the virtualenv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"

# Copy source code
COPY . .

# Expose port
EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["uvicorn", "src.chronicler_backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]