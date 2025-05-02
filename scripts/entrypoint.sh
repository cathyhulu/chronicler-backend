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


# Launch the application based on the environment
if [ "${ENV}" = "development" ] || [ "${ENV}" = "local" ]; then
    echo "Starting in development mode with hot reload"
    exec uvicorn src.chronicler_backend.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Starting in production mode"
    exec uvicorn src.chronicler_backend.main:app --host 0.0.0.0 --port 8000
fi