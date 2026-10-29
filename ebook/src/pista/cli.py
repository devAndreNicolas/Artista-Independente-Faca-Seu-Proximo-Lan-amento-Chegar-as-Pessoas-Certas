from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .epub import compile_epub
from .pdf import compile_pdf
from .rag import build_index, search
from .checks import validate_manuscript

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
    p_compile = sub.add_parser("compile", help="gera EPUB, PDF ou ambos")
    p_compile.add_argument("--format", choices=("epub", "pdf", "all"), default="all")
    sub.add_parser("check", help="confere ordem dos capítulos e referências locais")
    args = parser.parse_args()
    if args.command == "index":
        print(f"{build_index(ROOT, ROOT / 'data' / 'index.json')} passagens indexadas")
    elif args.command == "search":
        for score, doc in search(ROOT, args.query, args.top):
            print(f"\n[{score:.2f}] {doc['source']} — {doc['section']}\n{doc['text'][:1400]}")
    elif args.command == "compile":
        errors = validate_manuscript(ROOT)
        if errors:
            raise SystemExit("Manuscrito reprovado pelo SDD:\n- " + "\n- ".join(errors))
        if args.format in ("epub", "all"):
            print(compile_epub(ROOT, ROOT / "build" / "pista.epub"))
        if args.format in ("pdf", "all"):
            print(compile_pdf(ROOT, ROOT / "build" / "pista.pdf"))
    elif args.command == "check":
        errors = validate_manuscript(ROOT)
        if errors:
            raise SystemExit("Manuscrito reprovado pelo SDD:\n- " + "\n- ".join(errors))
        for p in sorted((ROOT / "manuscript").glob("*.md")):
            print(f"OK {p.name}: {len(p.read_text(encoding='utf-8').split())} palavras")
        print("Manuscrito conforme aos critérios editoriais.")


if __name__ == "__main__":
    main()
