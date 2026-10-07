"""
Tests for CognitiveZip AI Agent MCP tool integration.
"""

import tempfile
from pathlib import Path
from cognitive_zip.format.writer import CognitiveZipWriter
from cognitive_zip.mcp.server import handle_tool_call


def test_mcp_tool_calls():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        source_dir = tmp_path / "app"
        source_dir.mkdir()

        (source_dir / "index.js").write_text("const express = require('express');", encoding="utf-8")
        czip_path = tmp_path / "app.czip"

        writer = CognitiveZipWriter()
        writer.pack_directory(str(source_dir), str(czip_path))

        # 1. Test czip_list_files
        list_res = handle_tool_call("czip_list_files", {"archive_path": str(czip_path)})
        assert "files" in list_res
        assert "index.js" in list_res["files"]

        # 2. Test czip_search
        search_res = handle_tool_call("czip_search", {"archive_path": str(czip_path), "query": "express server"})
        assert "matches" in search_res
        assert len(search_res["matches"]) > 0
        assert search_res["matches"][0]["file_path"] == "index.js"

        # 3. Test czip_read_file
        read_res = handle_tool_call("czip_read_file", {"archive_path": str(czip_path), "file_path": "index.js"})
        assert "content" in read_res
        assert "require('express')" in read_res["content"]
