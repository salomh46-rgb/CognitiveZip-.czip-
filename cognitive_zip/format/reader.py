"""
CognitiveZip Reader Engine (.czip Decompressor & Query Engine).
Enables random-access individual file reads and instant semantic queries
without decompressing the entire archive.
"""

import json
import os
import zlib
from pathlib import Path
from typing import Dict, List, Optional
from cognitive_zip.format.spec import MAGIC_HEADER, MAGIC_FOOTER, FOOTER_STRUCT, FOOTER_SIZE
from cognitive_zip.index.semantic_index import CognitiveIndex, SearchResult


class CognitiveZipReader:
    """
    Random-access reader and semantic query engine for .czip archives.
    """

    def __init__(self, archive_path: str):
        self.archive_path = Path(archive_path).resolve()
        if not self.archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        self.file_table: Dict[str, dict] = {}
        self.index: Optional[CognitiveIndex] = None

        self._load_header_and_footer()

    def _load_header_and_footer(self) -> None:
        """Reads header magic and jumps straight to the 28-byte footer."""
        file_size = self.archive_path.stat().st_size
        if file_size < len(MAGIC_HEADER) + FOOTER_SIZE:
            raise ValueError("File is too small to be a valid .czip archive")

        with open(self.archive_path, "rb") as f:
            # 1. Verify Header
            header = f.read(len(MAGIC_HEADER))
            if header != MAGIC_HEADER:
                raise ValueError("Corrupt or invalid CognitiveZip header magic")

            # 2. Seek to Footer (last 28 bytes)
            f.seek(file_size - FOOTER_SIZE)
            footer_bytes = f.read(FOOTER_SIZE)
            (
                index_offset,
                index_comp_size,
                expected_crc,
                end_magic,
            ) = FOOTER_STRUCT.unpack(footer_bytes)

            if end_magic != MAGIC_FOOTER:
                raise ValueError("Corrupt or invalid CognitiveZip footer magic")

            # 3. Read only the compressed index block (Zero-Extraction of data files)
            f.seek(index_offset)
            compressed_index = f.read(index_comp_size)

            actual_crc = zlib.crc32(compressed_index) & 0xFFFFFFFF
            if actual_crc != expected_crc:
                raise ValueError("CRC32 mismatch in archive index block")

            raw_index_bytes = zlib.decompress(compressed_index)
            index_payload = json.loads(raw_index_bytes.decode("utf-8"))

            self.file_table = index_payload.get("file_table", {})
            self.index = CognitiveIndex.from_dict(index_payload.get("semantic_index", {}))

    def list_files(self) -> List[str]:
        """Returns list of relative file paths contained in the archive."""
        return sorted(list(self.file_table.keys()))

    def query(self, search_text: str, top_k: int = 5) -> List[SearchResult]:
        """
        Executes zero-extraction semantic query directly against embedded index.
        """
        if not self.index:
            return []
        return self.index.search(search_text, top_k=top_k)

    def read_file(self, file_path: str) -> bytes:
        """
        Selectively decompresses ONLY the requested file into memory.
        Does not touch the disk or extract other files.
        """
        # Normalize path
        normalized = file_path.replace("\\", "/").lstrip("/")
        meta = self.file_table.get(normalized)
        if not meta:
            # Try fuzzy match
            matching = [p for p in self.file_table if p.endswith(normalized)]
            if matching:
                meta = self.file_table[matching[0]]
            else:
                raise FileNotFoundError(f"File '{file_path}' not found in .czip archive")

        offset = meta["offset"]
        comp_size = meta["comp_size"]
        expected_crc = meta["crc32"]

        with open(self.archive_path, "rb") as f:
            f.seek(offset)
            compressed_chunk = f.read(comp_size)

        content = zlib.decompress(compressed_chunk)
        actual_crc = zlib.crc32(content) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"Integrity check failed: CRC32 mismatch for {file_path}")

        return content

    def read_text(self, file_path: str, encoding: str = "utf-8") -> str:
        """Selectively reads and decodes a text file directly from compressed storage."""
        raw_bytes = self.read_file(file_path)
        return raw_bytes.decode(encoding, errors="replace")

    def extract_all(self, destination_dir: str) -> int:
        """Extracts all files to destination directory."""
        dest = Path(destination_dir).resolve()
        dest.mkdir(parents=True, exist_ok=True)
        count = 0

        for file_path in self.list_files():
            content = self.read_file(file_path)
            target = dest / file_path
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "wb") as f:
                f.write(content)
            count += 1

        return count
