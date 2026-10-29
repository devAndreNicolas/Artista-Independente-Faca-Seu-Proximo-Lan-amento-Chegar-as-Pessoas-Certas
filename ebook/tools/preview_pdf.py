"""Renderiza cada página real do PDF em PNG para inspeção visual."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import pymupdf
except ImportError as exc:
    raise SystemExit("Instale PyMuPDF no Python ativo: python -m pip install PyMuPDF") from exc


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python tools/preview_pdf.py <arquivo.pdf> <pasta-de-saída>")
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    for stale in output.glob("page-*.png"):
        stale.unlink()
    document = pymupdf.open(source)
    for index, page in enumerate(document, 1):
        target = output / f"page-{index:02}.png"
        page.get_pixmap(dpi=180, alpha=False).save(target)
        print(target)
    document.close()


if __name__ == "__main__":
    main()
