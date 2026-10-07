"""
CognitiveZip Writer (.czip Archiver).
Packs directories into block-compressed chunks with an embedded cognitive semantic index.
"""

import json
import os
import zlib
from pathlib import Path
from typing import Dict, List, Optional
from cognitive_zip.format.spec import MAGIC_HEADER, MAGIC_FOOTER, FOOTER_STRUCT
from cognitive_zip.index.semantic_index import CognitiveIndex


class CognitiveZipWriter:
    """
    Creates .czip archives featuring random-access file entries and semantic footers.
    """

    def __init__(self, compression_level: int = 6):
        self.compression_level = compression_level
        self.index = CognitiveIndex()
        # file_path -> {offset, compressed_size, uncompressed_size, crc32}
        self.file_table: Dict[str, dict] = {}

    def pack_directory(self, source_dir: str, output_czip_path: str) -> dict:
        """
        Packs an entire directory tree into a single .czip file.
        Returns archive metadata statistics.
        """
        src = Path(source_dir).resolve()
        if not src.exists() or not src.is_dir():
            raise ValueError(f"Source directory does not exist: {source_dir}")

        out_path = Path(output_czip_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        total_uncompressed = 0
        total_files = 0

        with open(out_path, "wb") as f_out:
            # 1. Write Header Magic
            f_out.write(MAGIC_HEADER)
            current_offset = len(MAGIC_HEADER)

            # 2. Iterate and compress files
            for root, _, files in os.walk(src):
                for file_name in files:
                    file_path = Path(root) / file_name
                    rel_path = file_path.relative_to(src).as_posix()

                    try:
                        with open(file_path, "rb") as f_in:
                            content = f_in.read()
                    except Exception:
                        continue  # Skip unreadable files

                    uncompressed_len = len(content)
                    total_uncompressed += uncompressed_len
                    file_crc = zlib.crc32(content) & 0xFFFFFFFF

                    # Compress with DEFLATE (zlib)
                    compressed_data = zlib.compress(content, level=self.compression_level)
                    compressed_len = len(compressed_data)

                    # Record in file table
                    self.file_table[rel_path] = {
                        "offset": current_offset,
                        "comp_size": compressed_len,
                        "orig_size": uncompressed_len,
                        "crc32": file_crc,
                    }

                    # Feed into semantic index if likely text/code
                    if uncompressed_len < 5 * 1024 * 1024:  # under 5MB
                        self.index.add_document(rel_path, content)

                    # Write compressed file chunk
                    f_out.write(compressed_data)
                    current_offset += compressed_len
                    total_files += 1

            # 3. Finalize semantic index
            self.index.finalize()

            # 4. Serialize Index Section
            index_payload = {
                "file_table": self.file_table,
                "semantic_index": self.index.to_dict(),
            }
            raw_index_bytes = json.dumps(index_payload, ensure_ascii=False).encode("utf-8")
            compressed_index = zlib.compress(raw_index_bytes, level=self.compression_level)

            index_offset = current_offset
            index_comp_size = len(compressed_index)
            index_crc = zlib.crc32(compressed_index) & 0xFFFFFFFF

            # Write compressed index
            f_out.write(compressed_index)

            # 5. Write 28-byte Footer
            # [index_offset: 8B][index_size: 8B][crc32: 4B][MAGIC_FOOTER: 8B]
            footer_bytes = FOOTER_STRUCT.pack(index_offset, index_comp_size, index_crc, MAGIC_FOOTER)
            f_out.write(footer_bytes)

        total_archive_size = out_path.stat().st_size
        ratio = (1.0 - (total_archive_size / max(1, total_uncompressed))) * 100.0

        return {
            "archive_path": str(out_path),
            "total_files": total_files,
            "uncompressed_bytes": total_uncompressed,
            "archive_bytes": total_archive_size,
            "compression_ratio_pct": round(ratio, 2),
            "indexed_terms": len(self.index.inverted_index),
        }
