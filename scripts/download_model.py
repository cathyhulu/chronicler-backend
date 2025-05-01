#!/usr/bin/env python3
"""
Script to download and quantize the sentence transformer model.
"""
import argparse
import sys
from pathlib import Path

from chronicler_backend.utils.embeddings import (
    DEFAULT_MODEL_NAME,
    DEFAULT_QUANTIZED_DIR,
    export_quantized_model,
)
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


def main():
    """Download and quantize the model."""
    parser = argparse.ArgumentParser(
        description="Download and quantize a sentence transformer model for Chronicler"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_NAME,
        help=f"Model name to download (default: {DEFAULT_MODEL_NAME})",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_QUANTIZED_DIR),
        help=f"Output directory for the quantized model (default: {DEFAULT_QUANTIZED_DIR})",
    )
    parser.add_argument(
        "--force", action="store_true", help="Force download even if the model already exists"
    )

    args = parser.parse_args()
    output_path = Path(args.output_dir)

    if output_path.exists() and list(output_path.glob("**/*.onnx")) and not args.force:
        logger.info(f"Model already exists at {output_path}. Use --force to redownload.")
        sys.exit(0)

    logger.info(f"Downloading and quantizing model {args.model} to {output_path}")
    try:
        export_quantized_model(output_dir=args.output_dir, model_name=args.model)
        logger.info("Model download and quantization complete!")
    except Exception as e:
        logger.error(f"Error downloading/quantizing model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
