"""
Constant values for convenience

Attributes:
    ROOT_DIR (Path): The root directory of the project.
    VECTOR_DIMENSION (int): The dimension of the vector embeddings.
    TRUNCATE_DESCRIPTION_LENGTH (int): The maximum length of the description
        before truncation for vector conversion.
    DEFAULT_MODEL_NAME (str): The default name of the model to be used.
    DEFAULT_MODEL_DIR (Path): The default directory for storing models.
    DEFAULT_QUANTIZED_DIR (Path): The default directory for storing
        quantized models.
    DEFAULT_QUANTIZATION (str): The default quantization method to be used.
"""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]

VECTOR_DIMENSION = 384
TRUNCATE_DESCRIPTION_LENGTH = 200

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"
DEFAULT_MODEL_DIR = Path(os.environ.get("MODEL_DIR", "./models"))
DEFAULT_QUANTIZED_DIR = DEFAULT_MODEL_DIR / "quantized-model"
DEFAULT_QUANTIZATION = "avx2"
