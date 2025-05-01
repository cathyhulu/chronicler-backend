"""
Constant values for convenience

Attributes:
    ROOT_DIR (Path): The root directory of the project.
    VECTOR_DIMENSION (int): The dimension of the vector embeddings.
    TRUNCATE_DESCRIPTION_LENGTH (int): The maximum length of the description
        before truncation for vector conversion.
"""

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]

VECTOR_DIMENSION = 384
TRUNCATE_DESCRIPTION_LENGTH = 200
