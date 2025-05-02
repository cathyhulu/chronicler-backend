"""
Module for managing sentence transformer models with ONNX support,
providing efficient embedding generation with multi-worker support.
"""

from pathlib import Path
from typing import Optional

from fastapi import BackgroundTasks, Depends
from sentence_transformers import (
    SentenceTransformer,
    export_dynamic_quantized_onnx_model,
)

from chronicler_backend.embeddings.manager import ModelManager
from chronicler_backend.utils.constants import (
    DEFAULT_MODEL_NAME,
    DEFAULT_QUANTIZATION,
    DEFAULT_QUANTIZED_DIR,
)
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


def export_quantized_model(
    output_dir: str = str(DEFAULT_QUANTIZED_DIR),
    model_name: str = DEFAULT_MODEL_NAME,
    quantization_config: str = DEFAULT_QUANTIZATION,
) -> str:
    """
    Export a dynamically quantized ONNX model.

    Args:
        output_dir: Directory to save the quantized model
        model_name: Name of the model to quantize
        quantization_config: Configuration for quantization, auto-determined if None

    Returns:
        Path to the exported model
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 1. First load the model with standard PyTorch backend
    model = SentenceTransformer(model_name)

    # 2. Save the base model files to the output directory
    model.save(output_dir)

    # 3. Now load with ONNX backend and export the quantized model
    try:
        onnx_model = SentenceTransformer(model_name, backend="onnx")

        # Export the quantized model directly to the output directory
        export_dynamic_quantized_onnx_model(
            model=onnx_model,
            model_name_or_path=output_dir,
            quantization_config=quantization_config,
        )

        # Verify the export was successful
        logger.info(f"Successfully exported quantized model to {output_dir}")
        for item in output_path.glob("**/*"):
            logger.debug(f"  {item}")

        return output_dir
    except Exception as e:
        logger.error(f"Error exporting quantized model: {e}")
        # Make sure to return the original model path for fallback
        return output_dir


async def get_model_manager() -> ModelManager:
    """
    FastAPI dependency for getting the ModelManager instance.

    Returns:
        ModelManager: Singleton instance of the ModelManager
    """
    return ModelManager()


def load_model_in_background(
    background_tasks: BackgroundTasks,
    model_manager: ModelManager = Depends(get_model_manager),
    model_path: Optional[str] = None,
    quantized: bool = True,
    backend: str = "onnx",
) -> None:
    """
    Schedule model loading as a background task.

    Args:
        background_tasks: FastAPI BackgroundTasks object
        model_manager: ModelManager instance
        model_path: Path to the model
        quantized: Whether to use a quantized model
        backend: Backend to use
    """
    background_tasks.add_task(
        model_manager.load_model, model_path=model_path, quantized=quantized, backend=backend
    )


def load_model_on_startup() -> None:
    """
    Function to be called during app startup to preload the model.
    """
    model_manager = ModelManager()
    model_manager.load_model()
