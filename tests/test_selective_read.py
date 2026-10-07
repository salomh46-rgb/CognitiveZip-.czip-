"""
Tests for Selective Single-File Decompression (Zero-Extraction proof).
"""

import tempfile
from pathlib import Path
import pytest
from cognitive_zip.format.writer import CognitiveZipWriter
from cognitive_zip.format.reader import CognitiveZipReader


def test_selective_decompression():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        source_dir = tmp_path / "repo"
        source_dir.mkdir()

        # Create 10 files
        for i in range(10):
            (source_dir / f"module_{i}.py").write_text(f"# Logic for module {i}\ndef run_{i}(): return {i * 10}", encoding="utf-8")

        czip_path = tmp_path / "repo.czip"
        writer = CognitiveZipWriter()
        writer.pack_directory(str(source_dir), str(czip_path))

        reader = CognitiveZipReader(str(czip_path))

        # Selectively read only module_7.py
        content_7 = reader.read_text("module_7.py")
        assert "def run_7(): return 70" in content_7

        # Reading non-existent file must raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            reader.read_file("non_existent_file.py")
