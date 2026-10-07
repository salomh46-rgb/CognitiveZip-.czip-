#!/usr/bin/env python3
"""
Full Autonomous Demonstration of CognitiveZip (.czip).
Simulates a real-world multi-file enterprise codebase, packs it into .czip,
and demonstrates sub-millisecond zero-extraction AI queries & MCP tool calls.
"""

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from cognitive_zip.format.writer import CognitiveZipWriter
from cognitive_zip.format.reader import CognitiveZipReader
from cognitive_zip.mcp.server import handle_tool_call

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner():
    print(f"""
{CYAN}   _____                   _ _   _           ______ _       {RESET}
{CYAN}  / ____|                 (_) | (_)         |___  /(_)      {RESET}
{MAGENTA} | |     ___   __ _ _ __  _| |_ ___   _____    / /  _ _ __  {RESET}
{MAGENTA} | |    / _ \\ / _` | '_ \\| | __| \\ \\ / / _ \\  / /  | | '_ \\ {RESET}
{CYAN} | |___| (_) | (_| | | | | | |_| |\\ V /  __/ / /__ | | |_) |{RESET}
{CYAN}  \\_____\\___/ \\__, |_| |_|_|\\__|_| \\_/ \\___|/_____||_| .__/ {RESET}
{CYAN}               __/ |                                  | |    {RESET}
{CYAN}              |___/     {BOLD}Zero-Extraction Semantic Archiver{RESET}   {CYAN}|_|    {RESET}
{BOLD}          For Human Developers & Autonomous AI Coding Agents{RESET}
----------------------------------------------------------------------
""")


def create_sample_enterprise_codebase(base_dir: Path):
    """Generates realistic enterprise codebase files."""
    (base_dir / "src" / "auth").mkdir(parents=True, exist_ok=True)
    (base_dir / "src" / "db").mkdir(parents=True, exist_ok=True)
    (base_dir / "src" / "payments").mkdir(parents=True, exist_ok=True)
    (base_dir / "src" / "ai").mkdir(parents=True, exist_ok=True)

    # 1. Auth service
    (base_dir / "src" / "auth" / "jwt_service.py").write_text(
        """# JWT Security & Auth Tokens
import jwt
from datetime import datetime, timedelta

JWT_SECRET_KEY = "super-secret-vault-key-2026"
ACCESS_TOKEN_EXPIRE_MINUTES = 120  # Token yaroqlilik muddati 2 soat
ALGORITHM = "HS256"

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
""",
        encoding="utf-8",
    )

    # 2. Database service
    (base_dir / "src" / "db" / "postgres_pool.py").write_text(
        """# PostgreSQL Enterprise Connection Pool
import asyncpg

POSTGRES_HOST = "62.171.143.55"
POSTGRES_PORT = 5432
POSTGRES_DB = "dentamed_production_db"
POSTGRES_POOL_SIZE = 25

async def get_connection_pool():
    return await asyncpg.create_pool(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        database=POSTGRES_DB,
        min_size=5,
        max_size=POSTGRES_POOL_SIZE,
    )
""",
        encoding="utf-8",
    )

    # 3. Fintech & Payments
    (base_dir / "src" / "payments" / "uzum_payme_webhook.py").write_text(
        """# Fintech Uzbekistan: Payme, Click & Uzum Webhook Processor
import hmac
import hashlib

PAYME_MERCHANT_KEY = "uz_payme_secret_8899"
CLICK_SECRET_KEY = "uz_click_secret_4422"

def verify_payme_signature(header_auth: str) -> bool:
    # 100x Tiyn to So'm conversion & idempotency check
    return header_auth.startswith("Basic ")

def process_click_prepare_checkout(click_trans_id: str, amount_tiyin: int):
    amount_som = amount_tiyin / 100
    print(f"Click to'lovi qabul qilindi: {amount_som} UZS")
    return {"error": 0, "status": "CONFIRMED"}
""",
        encoding="utf-8",
    )

    # 4. AI Router
    (base_dir / "src" / "ai" / "agent_router.py").write_text(
        """# Sub-100ms Autonomous AI Intent Router
from typing import Dict

ROUTER_INTENTS = ["billing", "appointment_booking", "technical_support"]

def route_user_query(query: str) -> str:
    # Non-autoregressive System 1 classifier
    if "narx" in query or "to'lov" in query:
        return "billing"
    return "general_support"
""",
        encoding="utf-8",
    )


def run_demo():
    print_banner()

    temp_workspace = Path("./demo_workspace_temp").resolve()
    temp_workspace.mkdir(exist_ok=True)
    src_dir = temp_workspace / "enterprise_backend"
    src_dir.mkdir(exist_ok=True)

    try:
        # Step 1: Create sample codebase
        print(f"{BOLD}{YELLOW}[1-BOSQICH] REAL ENTERPRISE LOYIHA TUZILMASI YARATILMOQDA...{RESET}")
        create_sample_enterprise_codebase(src_dir)
        print(f"  ✓ 4 ta asosiy arxitektura moduli tayyorlandi (auth, db, payments, ai)\n")

        # Step 2: Pack into .czip
        czip_file = temp_workspace / "backend_production.czip"
        print(f"{BOLD}{YELLOW}[2-BOSQICH] LOYIHA .czip FORMATIGA SIQILMOQDA (Zstandard/Deflate + Embedded Index)...{RESET}")
        t0 = time.time()
        writer = CognitiveZipWriter()
        stats = writer.pack_directory(str(src_dir), str(czip_file))
        pack_time = (time.time() - t0) * 1000

        print(f"  ✓ {GREEN}Muvaffaqiyatli arxivlandi! ({pack_time:.1f}ms){RESET}")
        print(f"  • Asl hajm: {stats['uncompressed_bytes']} bytes -> Siqilgan hajm: {stats['archive_bytes']} bytes")
        print(f"  • Siqilish nisbati: {GREEN}{stats['compression_ratio_pct']}% tejaldi{RESET}")
        print(f"  • Kognitiv indeksga kiritilgan atamalar: {stats['indexed_terms']} ta\n")

        # Step 3: Zero-Extraction Semantic Queries
        print(f"{BOLD}{YELLOW}[3-BOSQICH] 0-EXTRACTION KOGNITIV QIDIRUV (ARXIVNI OCHMASDAN TURIB!)...{RESET}")
        reader = CognitiveZipReader(str(czip_file))

        queries = [
            ("JWT token muddati qayerda?", "token expire minutes jwt"),
            ("Payme va Click to'lov webhooklari qaysi faylda?", "payme click webhook tiyin"),
            ("PostgreSQL ulanish porti va IP manzili qayerda?", "postgres host port 5432 asyncpg"),
        ]

        for q_title, q_search in queries:
            print(f"{CYAN}❓ SAVOL:{RESET} {BOLD}{q_title}{RESET}")
            t_start = time.time()
            results = reader.query(q_search, top_k=1)
            latency_ms = (time.time() - t_start) * 1000

            if results:
                best = results[0]
                print(f"   {GREEN}🎯 TOPILDI ({latency_ms:.2f} millisekundda!):{RESET} {BOLD}{best.file_path}:{best.line_number}{RESET}")
                print(f"   {MAGENTA}↳ Kod parchasi:{RESET} {best.best_snippet.strip()}")
            print()

        # Step 4: AI Agent MCP Tool Call Simulation
        print(f"{BOLD}{YELLOW}[4-BOSQICH] AI AGENT MCP VOSITASI SIMULYATSIYASI (Claude / Antigravity Agent)...{RESET}")
        print(f"  AI agent `czip_read_file` orqali to'g'ridan-to'g'ri xotiradan 'jwt_service.py' ni o'qimoqda...")

        mcp_result = handle_tool_call(
            "czip_read_file",
            {"archive_path": str(czip_file), "file_path": "src/auth/jwt_service.py"},
        )
        print(f"  ✓ AI agent olgan matn hajmi: {len(mcp_result.get('content', ''))} belgi (Diskka bitta ham fayl yozilmadi!)")

        print(f"\n{BOLD}{GREEN}=== 🎯 KOGNITIV ARXIVATOR TO'LIQ ISBOTLANDI! DASTURCHI VA AI UCHUN MUTLAQ INQILOB! ==={RESET}\n")

    finally:
        # Cleanup temp directory
        if temp_workspace.exists():
            shutil.rmtree(temp_workspace, ignore_errors=True)


if __name__ == "__main__":
    run_demo()
