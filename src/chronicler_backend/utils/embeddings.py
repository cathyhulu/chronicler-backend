"""
Module for managing sentence transformer models with ONNX support,
providing efficient embedding generation with multi-worker support.
"""

from pathlib import Path
from typing import List, Optional

from sentence_transformers import (
    SentenceTransformer,
    export_dynamic_quantized_onnx_model,
)

from chronicler_backend.utils.constants import (
    DEFAULT_MODEL_NAME,
    DEFAULT_QUANTIZATION,
    DEFAULT_QUANTIZED_DIR,
    TRUNCATE_DESCRIPTION_LENGTH,
)
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


class ModelManager:
    """
    Singleton manager for sentence transformer models that supports
    efficient memory usage across multiple FastAPI workers.
    """

    def __init__(self) -> None:
        self._model: Optional[SentenceTransformer] = None

    def load_model(
        self, model_path: Optional[str] = None, quantized: bool = True, backend: str = "onnx"
    ) -> None:
        """
        Load the sentence transformer model with ONNX backend.

        Args:
            model_path: Path to the model, defaults to DEFAULT_QUANTIZED_DIR
            quantized: Whether to use a quantized model
            backend: Backend to use, defaults to "onnx"
        """
        if self._model is not None:
            return

        if model_path is None:
            model_path = str(DEFAULT_QUANTIZED_DIR if quantized else DEFAULT_MODEL_NAME)

        try:
            # For ONNX models, we need to specify the file path relative to the model directory
            if quantized and backend == "onnx":
                # Point to the exact ONNX file in the onnx subdirectory
                model_kwargs = {
                    "file_name": "onnx/model_quint8_avx2.onnx",
                    "provider": "CPUExecutionProvider",
                }
                self._model = SentenceTransformer(
                    model_path, backend=backend, model_kwargs=model_kwargs
                )
                logger.info(f"Loaded quantized model from {model_path}")
            else:
                self._model = SentenceTransformer(model_path, backend=backend)
                logger.info(f"Loaded standard model ({backend = }) from {model_path}")
        except Exception as e:
            # Log the error and fall back to the non-quantized model
            logger.error(
                f"Error loading model with {backend = }: {e}. Falling back to standard model."
            )
            self._model = SentenceTransformer(DEFAULT_MODEL_NAME)

    def get_model(self) -> SentenceTransformer:
        """Get the loaded model or load it if not already loaded."""
        if self._model is None:
            self.load_model()
        return self._model

    def encode(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.

        Args:
            text: Input text to encode

        Returns:
            Vector embedding as a list of floats
        """
        model = self.get_model()
        return model.encode(text).tolist()

    def prepare_node_text(
        self, name: str, node_type: str, date_range: str = "", description: str = ""
    ) -> str:
        """
        Prepare text for embedding by concatenating node properties.
        Truncates the description to avoid exceeding token limits.

        Args:
            name: Node name
            node_type: Node type
            date_range: Date range string
            description: Full description (will be truncated if needed)

        Returns:
            Concatenated text ready for embedding
        """
        # Simple truncation strategy - could be improved with smarter tokenization
        main_text = f"{name} {node_type} {date_range}".strip()
        remaining_length = TRUNCATE_DESCRIPTION_LENGTH - len(main_text.split())

        # Simple word-based truncation (approximation)
        if description:
            desc_words = description.split()
            if len(desc_words) > remaining_length:
                description = " ".join(desc_words[:remaining_length])

        return f"{main_text} {description}".strip()


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


# Create an instance of ModelManager
# TODO: REMOVE AFTER MIGRATION TO CELERY WORKER
model_manager = ModelManager()
