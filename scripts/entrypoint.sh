#!/bin/bash
set -e

# Activate the virtual environment
. /app/.venv/bin/activate

# Set default model directory if not provided
MODEL_DIR=${MODEL_DIR:-/app/model_weights}
QUANTIZED_MODEL_DIR="${MODEL_DIR}/quantized-model"

# Create model directory if it doesn't exist
mkdir -p ${MODEL_DIR}

# Download quantized model if it doesn't exist
uv run scripts/download_model.py --output-dir ${QUANTIZED_MODEL_DIR} --verbose

# Set FastAPI configuration from environment variables
# These come from .env via docker-compose.yml
HOST=${FASTAPI_HOST:-0.0.0.0}
PORT=${FASTAPI_PORT:-8000}
WORKERS=${FASTAPI_WORKERS:-4}
WORKER_TIMEOUT=${FASTAPI_WORKER_TIMEOUT:-60}
DEBUG=${FASTAPI_DEBUG:-false}
RELOAD=${FASTAPI_RELOAD:-false}

# Launch the application based on the environment
if [ "${ENV}" = "development" ] || [ "${ENV}" = "local" ]; then
    echo "Starting in development mode with hot reload"
    exec uvicorn src.chronicler_backend.main:app --host ${HOST} --port ${PORT} --reload 
else
    echo "Starting in production mode with ${WORKERS} workers"
    exec gunicorn src.chronicler_backend.main:app -w ${WORKERS} -k uvicorn.workers.UvicornWorker \
        --timeout ${WORKER_TIMEOUT} -b ${HOST}:${PORT}
fi