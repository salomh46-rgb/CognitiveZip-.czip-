#!/usr/bin/env python3
"""
CognitiveZip CLI Interface.
Command-line utility for packing, zero-extraction querying, reading, and serving .czip archives.
"""

import argparse
import sys
import time
from cognitive_zip.format.writer import CognitiveZipWriter
from cognitive_zip.format.reader import CognitiveZipReader
from cognitive_zip.mcp.server import run_mcp_server

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


BANNER = f"""
{CYAN}   _____                   _ _   _           ______ _       {RESET}
{CYAN}  / ____|                 (_) | (_)         |___  /(_)      {RESET}
{MAGENTA} | |     ___   __ _ _ __  _| |_ ___   _____    / /  _ _ __  {RESET}
{MAGENTA} | |    / _ \\ / _` | '_ \\| | __| \\ \\ / / _ \\  / /  | | '_ \\ {RESET}
{CYAN} | |___| (_) | (_| | | | | | |_| |\\ V /  __/ / /__ | | |_) |{RESET}
{CYAN}  \\_____\\___/ \\__, |_| |_|_|\\__|_| \\_/ \\___|/_____||_| .__/ {RESET}
{CYAN}               __/ |                                  | |    {RESET}
{CYAN}              |___/     {BOLD}Zero-Extraction Semantic Archiver{RESET}   {CYAN}|_|    {RESET}
"""


def cmd_pack(args):
    print(BANNER)
    print(f"{YELLOW}⏳ '{args.directory}' papkasi CognitiveZip formatiga siqilmoqda...{RESET}")
    start = time.time()
    writer = CognitiveZipWriter(compression_level=args.level)
    stats = writer.pack_directory(args.directory, args.output)
    elapsed = time.time() - start

    orig_mb = stats["uncompressed_bytes"] / (1024 * 1024)
    arch_mb = stats["archive_bytes"] / (1024 * 1024)

    print(f"\n{GREEN}✅ Muvaffaqiyatli arxivlandi! ({elapsed:.2f} soniya){RESET}")
    print(f"  • Chiqish fayli: {BOLD}{stats['archive_path']}{RESET}")
    print(f"  • Fayllar soni: {stats['total_files']} ta")
    print(f"  • Asl hajm: {orig_mb:.2f} MB -> Siqilgan hajm: {arch_mb:.2f} MB")
    print(f"  • Siqilish nisbati: {GREEN}{stats['compression_ratio_pct']}% tejandi{RESET}")
    print(f"  • Indekslangan semantik atamalar: {stats['indexed_terms']} ta\n")


def cmd_query(args):
    start = time.time()
    reader = CognitiveZipReader(args.archive)
    results = reader.query(args.query, top_k=args.limit)
    elapsed = (time.time() - start) * 1000  # in ms

    print(f"\n{BOLD}{CYAN}🔍 KOGNITIV QIDIRUV NATIJASI ({elapsed:.1f}ms - 0-Extraction):{RESET}")
    print(f"Arxiv: {args.archive} | So'rov: {BOLD}'{args.query}'{RESET}\n")

    if not results:
        print(f"{YELLOW}Mos keluvchi fayllar topilmadi.{RESET}")
        return

    for idx, r in enumerate(results, 1):
        print(f"{BOLD}{GREEN}#{idx} {r.file_path}{RESET} {DIM}(Relevance: {r.relevance_score:.2f}, Satr: {r.line_number}){RESET}")
        if r.best_snippet:
            print(f"   {CYAN}↳ [{r.line_number}]:{RESET} {r.best_snippet}")
        print()


def cmd_cat(args):
    reader = CognitiveZipReader(args.archive)
    try:
        content = reader.read_text(args.file)
        print(content)
    except FileNotFoundError:
        print(f"{RED}Xatolik: '{args.file}' arxivida topilmadi.{RESET}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    reader = CognitiveZipReader(args.archive)
    files = reader.list_files()
    print(f"\n{BOLD}{CYAN}📂 ARXIV TARKIBI ({len(files)} ta fayl):{RESET}")
    for f in files:
        meta = reader.file_table[f]
        orig_kb = meta["orig_size"] / 1024
        comp_kb = meta["comp_size"] / 1024
        print(f"  • {f:<40} {orig_kb:>7.1f} KB -> {comp_kb:>7.1f} KB")
    print()


def cmd_extract(args):
    reader = CognitiveZipReader(args.archive)
    print(f"{YELLOW}⏳ Arxiv to'liq ochilmoqda: {args.dest}...{RESET}")
    count = reader.extract_all(args.dest)
    print(f"{GREEN}✅ {count} ta fayl muvaffaqiyatli yoyildi: {args.dest}{RESET}")


def main():
    parser = argparse.ArgumentParser(
        description="CognitiveZip: Zero-Extraction Semantic Archiver for Humans & AI Agents",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # pack
    p_pack = subparsers.add_parser("pack", help="Pack directory into .czip archive")
    p_pack.add_argument("directory", help="Source folder path")
    p_pack.add_argument("-o", "--output", required=True, help="Output .czip file path")
    p_pack.add_argument("-l", "--level", type=int, default=6, help="Compression level (1-9)")
    p_pack.set_defaults(func=cmd_pack)

    # query
    p_query = subparsers.add_parser("query", help="Zero-extraction natural language query")
    p_query.add_argument("archive", help="Path to .czip archive")
    p_query.add_argument("query", help="Search query or question")
    p_query.add_argument("-k", "--limit", type=int, default=5, help="Top matches limit")
    p_query.set_defaults(func=cmd_query)

    # cat
    p_cat = subparsers.add_parser("cat", help="Print single file content without extracting archive")
    p_cat.add_argument("archive", help="Path to .czip archive")
    p_cat.add_argument("file", help="Relative file path inside archive")
    p_cat.set_defaults(func=cmd_cat)

    # list
    p_list = subparsers.add_parser("list", help="List files in archive")
    p_list.add_argument("archive", help="Path to .czip archive")
    p_list.set_defaults(func=cmd_list)

    # extract
    p_ext = subparsers.add_parser("extract", help="Extract all files")
    p_ext.add_argument("archive", help="Path to .czip archive")
    p_ext.add_argument("dest", nargs="?", default=".", help="Destination folder")
    p_ext.set_defaults(func=cmd_extract)

    # mcp
    p_mcp = subparsers.add_parser("mcp", help="Run MCP server mode for AI agents")
    p_mcp.set_defaults(func=lambda args: run_mcp_server())

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
