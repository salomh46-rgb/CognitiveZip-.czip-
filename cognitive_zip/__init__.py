"""
CognitiveZip (.czip) v1.0
Zero-Extraction Semantic Archiver for Humans & AI Agents.
"""

from .format.writer import CognitiveZipWriter
from .format.reader import CognitiveZipReader
from .index.semantic_index import CognitiveIndex, SearchResult

__version__ = "1.0.0"

__all__ = [
    "CognitiveZipWriter",
    "CognitiveZipReader",
    "CognitiveIndex",
    "SearchResult",
]
