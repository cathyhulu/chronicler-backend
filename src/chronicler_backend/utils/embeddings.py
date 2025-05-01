"""
Module for managing sentence transformer models with ONNX support,
providing efficient embedding generation with multi-worker support.
"""

from functools import lru_cache
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


class ModelManager:
    """
    Singleton manager for sentence transformer models that supports
    efficient memory usage across multiple FastAPI workers.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._model = None
        return cls._instance

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

        self._model = SentenceTransformer(model_path, backend=backend)

    def get_model(self) -> SentenceTransformer:
        """Get the loaded model or load it if not already loaded."""
        if self._model is None:
            self.load_model()
        return self._model

    @lru_cache(maxsize=1024)
    def encode(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text.
        Uses lru_cache to avoid recomputing embeddings for the same text.

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

    # Load the model with ONNX backend
    model = SentenceTransformer(model_name, backend="onnx")

    # Export the quantized model with the config
    export_dynamic_quantized_onnx_model(
        model=model,
        model_name_or_path=output_dir,
        quantization_config=quantization_config,
    )

    return output_dir


# Create a singleton instance
model_manager = ModelManager()
