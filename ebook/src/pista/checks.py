"""Critérios editoriais e integridade do manuscrito definidos pelo SDD."""
from __future__ import annotations

import re
import tomllib
from pathlib import Path
from urllib.parse import urlparse

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def validate_manuscript(root: Path) -> list[str]:
    spec_path = root / "editorial" / "acceptance.toml"
    if not spec_path.exists():
        return ["Critérios ausentes: editorial/acceptance.toml"]
    spec = tomllib.loads(spec_path.read_text(encoding="utf-8"))
    chapter_specs = spec.get("chapter", [])
    expected = [item["file"] for item in chapter_specs]
    actual = [p.name for p in sorted((root / "manuscript").glob("*.md"))]
    errors: list[str] = []
    if actual != expected:
        errors.append(f"Ordem/arquivos de capítulos divergentes. Esperado: {expected}; encontrado: {actual}")
    minimum_words = spec.get("rules", {}).get("minimum_words_per_chapter", 0)
    for item in chapter_specs:
        path = root / "manuscript" / item["file"]
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("# "):
            errors.append(f"{item['file']}: título H1 ausente no início.")
        words = len(text.split())
        if words < minimum_words:
            errors.append(f"{item['file']}: {words} palavras; mínimo editorial {minimum_words}.")
        folded = text.casefold()
        for required in item.get("required", []):
            if required.casefold() not in folded:
                errors.append(f"{item['file']}: critério de cobertura ausente: {required!r}.")
        for target in LINK_RE.findall(text):
            parsed = urlparse(target)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                continue
            local = (path.parent / target.split("#", 1)[0]).resolve()
            if not local.exists():
                errors.append(f"{item['file']}: link local inexistente: {target}")
    return errors
