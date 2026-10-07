"""
Tests for Zero-Extraction Semantic & Lexical Search inside .czip archives.
"""

import tempfile
from pathlib import Path
from cognitive_zip.format.writer import CognitiveZipWriter
from cognitive_zip.format.reader import CognitiveZipReader


def test_zero_extraction_semantic_query():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        source_dir = tmp_path / "codebase"
        source_dir.mkdir()

        (source_dir / "payment.py").write_text(
            "class StripeWebhookHandler:\n    def handle_payment_intent_succeeded(self, event):\n        print('Payment confirmed')\n",
            encoding="utf-8",
        )
        (source_dir / "database.py").write_text(
            "def get_postgres_connection():\n    return create_engine('postgresql://user:pass@localhost:5432/app_db')\n",
            encoding="utf-8",
        )
        (source_dir / "security.py").write_text(
            "JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 60\nSECRET_KEY = 'supersecret'\n",
            encoding="utf-8",
        )

        czip_path = tmp_path / "codebase.czip"

        writer = CognitiveZipWriter()
        writer.pack_directory(str(source_dir), str(czip_path))

        reader = CognitiveZipReader(str(czip_path))

        # Query 1: Payment webhook
        results_payment = reader.query("stripe payment webhook", top_k=2)
        assert len(results_payment) > 0
        assert results_payment[0].file_path == "payment.py"
        snippet = results_payment[0].best_snippet.lower()
        assert "stripe" in snippet or "payment" in snippet or "webhook" in snippet

        # Query 2: Token expiration
        results_jwt = reader.query("token expire minutes", top_k=2)
        assert len(results_jwt) > 0
        assert results_jwt[0].file_path == "security.py"
        assert "EXPIRE_MINUTES" in results_jwt[0].best_snippet

        # Query 3: Database port
        results_db = reader.query("postgres connection 5432", top_k=2)
        assert len(results_db) > 0
        assert results_db[0].file_path == "database.py"
