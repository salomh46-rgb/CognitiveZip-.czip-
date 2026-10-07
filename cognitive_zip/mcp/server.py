"""
Model Context Protocol (MCP) Server for CognitiveZip.
Equips AI agents (Claude, Cursor, Antigravity) with zero-extraction .czip reading capabilities.
"""

import json
import sys
from cognitive_zip.format.reader import CognitiveZipReader


def handle_tool_call(tool_name: str, arguments: dict) -> dict:
    archive_path = arguments.get("archive_path")
    if not archive_path:
        return {"error": "Missing required argument 'archive_path'"}

    try:
        reader = CognitiveZipReader(archive_path)

        if tool_name == "czip_search":
            query = arguments.get("query", "")
            top_k = int(arguments.get("top_k", 5))
            results = reader.query(query, top_k=top_k)
            return {
                "archive": archive_path,
                "matches": [
                    {
                        "file_path": r.file_path,
                        "line_number": r.line_number,
                        "relevance_score": r.relevance_score,
                        "snippet": r.best_snippet,
                    }
                    for r in results
                ],
            }

        elif tool_name == "czip_read_file":
            file_path = arguments.get("file_path", "")
            if not file_path:
                return {"error": "Missing required argument 'file_path'"}
            content_text = reader.read_text(file_path)
            return {
                "archive": archive_path,
                "file_path": file_path,
                "content": content_text,
            }

        elif tool_name == "czip_list_files":
            files = reader.list_files()
            return {
                "archive": archive_path,
                "total_files": len(files),
                "files": files,
            }

        else:
            return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        return {"error": str(e)}


def run_mcp_server():
    """Runs a lightweight stdio JSON-RPC loop for agent tool calling."""
    if sys.stdout.encoding != 'utf-8':
        try:
            sys.stdout.reconfigure(encoding='utf-8')
        except Exception:
            pass

    # Read lines from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})

            if method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "czip_search",
                                "description": "Search inside a .czip archive using natural language without extracting it.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "archive_path": {"type": "string"},
                                        "query": {"type": "string"},
                                        "top_k": {"type": "integer", "default": 5},
                                    },
                                    "required": ["archive_path", "query"],
                                },
                            },
                            {
                                "name": "czip_read_file",
                                "description": "Read file content directly from inside a .czip archive without extracting to disk.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "archive_path": {"type": "string"},
                                        "file_path": {"type": "string"},
                                    },
                                    "required": ["archive_path", "file_path"],
                                },
                            },
                            {
                                "name": "czip_list_files",
                                "description": "List all files contained in a .czip archive.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "archive_path": {"type": "string"},
                                    },
                                    "required": ["archive_path"],
                                },
                            },
                        ]
                    },
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result_payload = handle_tool_call(tool_name, arguments)
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result_payload, ensure_ascii=False)}]},
                }
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}

            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_mcp_server()
