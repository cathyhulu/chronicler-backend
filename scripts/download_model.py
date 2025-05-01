#!/usr/bin/env python3
"""
Script to download and quantize the sentence transformer model.
"""
import argparse
import os
import sys
from pathlib import Path

from chronicler_backend.utils.constants import (
    DEFAULT_MODEL_NAME,
    DEFAULT_QUANTIZED_DIR,
)
from chronicler_backend.utils.embeddings import export_quantized_model
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
    parser.add_argument("--verbose", action="store_true", help="Print verbose output for debugging")

    args = parser.parse_args()
    output_path = Path(args.output_dir)

    # Print information for debugging
    if args.verbose:
        logger.debug(f"Model name: {args.model}")
        logger.debug(f"Output directory: {output_path}")
        logger.debug(f"Force download: {args.force}")
        logger.debug(f"Environment variables: MODEL_DIR={os.environ.get('MODEL_DIR', 'Not set')}")
        logger.debug(f"Current working directory: {os.getcwd()}")

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    if (
        output_path.exists()
        and list(output_path.glob("**/*.onnx"))
        and list(output_path.glob("**/config.json"))
        and not args.force
    ):
        logger.info(f"Model already exists at {output_path}. Use --force to redownload.")
        sys.exit(0)

    logger.info(f"Downloading and quantizing model {args.model} to {output_path}")

    try:
        export_quantized_model(output_dir=str(args.output_dir), model_name=args.model)
        logger.debug("Model download and quantization complete!")

        # List directory contents to verify
        if args.verbose:
            logger.debug("Directory contents:")
            for item in output_path.glob("**/*"):
                logger.debug(f"  {item}")
    except Exception as e:
        logger.error(f"Error downloading/quantizing model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
