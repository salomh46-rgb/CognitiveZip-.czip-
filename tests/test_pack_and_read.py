"""
Tests for CognitiveZip packing, footer validation, and individual file reads.
"""

import tempfile
from pathlib import Path
from cognitive_zip.format.writer import CognitiveZipWriter
from cognitive_zip.format.reader import CognitiveZipReader


def test_pack_and_read_lifecycle():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        source_dir = tmp_path / "my_project"
        source_dir.mkdir()

        # Create dummy project files
        (source_dir / "main.py").write_text("print('Hello CognitiveZip')", encoding="utf-8")
        (source_dir / "config.json").write_text('{"db_port": 5432, "env": "prod"}', encoding="utf-8")
        sub_dir = source_dir / "services"
        sub_dir.mkdir()
        (sub_dir / "auth.py").write_text("def verify_jwt_token(token):\n    pass", encoding="utf-8")

        output_czip = tmp_path / "project.czip"

        # Pack
        writer = CognitiveZipWriter()
        stats = writer.pack_directory(str(source_dir), str(output_czip))

        assert stats["total_files"] == 3
        assert output_czip.exists()

        # Read back without extracting
        reader = CognitiveZipReader(str(output_czip))
        files = reader.list_files()
        assert "main.py" in files
        assert "config.json" in files
        assert "services/auth.py" in files

        # Read content directly from archive
        main_content = reader.read_text("main.py")
        assert "print('Hello CognitiveZip')" in main_content

        auth_content = reader.read_text("services/auth.py")
        assert "verify_jwt_token" in auth_content
