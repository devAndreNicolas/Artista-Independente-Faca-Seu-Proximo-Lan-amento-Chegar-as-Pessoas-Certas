from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .epub import compile_epub
from .rag import build_index, search

ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(prog="pista", description="Oficina local do ebook PISTA")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index", help="indexa as fontes locais")
    p_search = sub.add_parser("search", help="recupera passagens relevantes")
    p_search.add_argument("query")
    p_search.add_argument("--top", type=int, default=6)
    sub.add_parser("compile", help="gera EPUB 3")
    sub.add_parser("check", help="confere ordem dos capítulos e referências locais")
    args = parser.parse_args()
    if args.command == "index":
        print(f"{build_index(ROOT, ROOT / 'data' / 'index.json')} passagens indexadas")
    elif args.command == "search":
        for score, doc in search(ROOT, args.query, args.top):
            print(f"\n[{score:.2f}] {doc['source']} — {doc['section']}\n{doc['text'][:1400]}")
    elif args.command == "compile":
        print(compile_epub(ROOT, ROOT / "build" / "pista.epub"))
    elif args.command == "check":
        chapters = sorted((ROOT / "manuscript").glob("*.md"))
        for p in chapters:
            content = p.read_text(encoding="utf-8")
            if not content.startswith("# "):
                raise SystemExit(f"Título H1 ausente: {p.name}")
            print(f"OK {p.name}: {len(content.split())} palavras")
        print(f"{len(chapters)} capítulo(s) encontrados")


if __name__ == "__main__":
    main()
