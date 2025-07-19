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
)
from chronicler_backend.utils.logging import get_logger

logger = get_logger(__name__)


class SingletonMeta(type):
    """Metaclass for implementing the Singleton pattern."""

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            logger.info(f"Creating new singleton instance of {cls.__name__}")
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ModelManager(metaclass=SingletonMeta):
    """
    Manager for sentence transformer models that supports
    efficient memory usage across multiple FastAPI workers.
    """

    def __init__(self) -> None:
        self._model: Optional[SentenceTransformer] = None

    def load_model(
        self,
        model_path: Optional[str] = None,
        quantized: bool = True,
        backend: str = "onnx",
        verbose: bool = False,
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

        if verbose:
            logger.info(f"Current working directory: {Path.cwd()}")
            logger.info(f"Loading model from {model_path} with backend {backend}")
            logger.info(f"Quantized: {quantized}")
            logger.info(f"Model path: {model_path}")
            logger.info(f"Directory contents for {model_path}:")

        try:
            for item in Path(model_path).iterdir():
                logger.info(f"  {item}")

            if quantized and backend == "onnx":
                # Try to find the ONNX model file
                model_dir = Path(model_path)
                onnx_files = list(model_dir.glob("**/*.onnx"))

                if onnx_files:
                    # Use the first ONNX file found
                    relative_path = onnx_files[0].relative_to(model_dir)
                    model_kwargs = {
                        "file_name": str(relative_path),
                        "provider": "CPUExecutionProvider",
                    }
                    self._model = SentenceTransformer(
                        model_path, backend=backend, model_kwargs=model_kwargs
                    )
                else:
                    # No ONNX files found, fall back to standard model
                    logger.error(
                        f"No ONNX model files in {model_path}. Falling back to standard model."
                    )
                    self._model = SentenceTransformer(DEFAULT_MODEL_NAME)
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
        Truncates the description based on token count to avoid exceeding token limits.

        Args:
            name: Node name
            node_type: Node type
            date_range: Date range string
            description: Full description (will be truncated if needed)

        Returns:
            Concatenated text ready for embedding
        """
        # Get the model and its tokenizer
        model = self.get_model()
        tokenizer = model.tokenizer
        max_seq_length = model.max_seq_length

        # Concatenate the core metadata that must be included
        main_text = f"{name} {node_type} {date_range}".strip()

        # First check token count of main text
        main_tokens = tokenizer(main_text, return_attention_mask=False, return_token_type_ids=False)
        main_token_count = len(main_tokens["input_ids"])

        # Calculate remaining token capacity for description
        remaining_tokens = (
            max_seq_length - main_token_count - 3
        )  # Reserve a few tokens for padding/special tokens

        # Truncate description if needed based on token count
        truncated_description = description
        if description and remaining_tokens > 0:
            # Tokenize description without truncation
            desc_tokens = tokenizer(
                description, return_attention_mask=False, return_token_type_ids=False
            )
            desc_token_count = len(desc_tokens["input_ids"])

            # If description exceeds remaining token capacity, truncate it
            if desc_token_count > remaining_tokens:
                logger.info(
                    f"Truncating description from {desc_token_count} to {remaining_tokens} tokens"
                )
                # Simple truncation by percentage - a more sophisticated approach would be better
                truncation_ratio = remaining_tokens / desc_token_count
                truncation_word_count = int(len(description.split()) * truncation_ratio)
                truncated_description = " ".join(description.split()[:truncation_word_count])

                # Verify we didn't exceed token count after truncation
                verification_tokens = tokenizer(
                    truncated_description, return_attention_mask=False, return_token_type_ids=False
                )
                if len(verification_tokens["input_ids"]) > remaining_tokens:
                    # If still too long, truncate more aggressively
                    truncated_description = " ".join(
                        truncated_description.split()[: truncation_word_count - 10]
                    )

        # Return the combined text
        return f"{main_text} {truncated_description}".strip()


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
