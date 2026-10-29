"""RAG lexical local: divisão por seção, índice BM25 pequeno e citações."""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

TOKEN_RE = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)


def tokens(text: str) -> list[str]:
    return [t.casefold() for t in TOKEN_RE.findall(text)]


def split_markdown(path: Path, root: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    title = "Início"
    buf: list[str] = []
    chunks: list[dict] = []

    def flush() -> None:
        body = "\n".join(buf).strip()
        if body:
            chunks.append({"source": path.relative_to(root).as_posix(), "section": title,
                           "text": body, "tokens": tokens(title + " " + body)})

    for line in text.splitlines():
        if line.startswith("#"):
            flush()
            buf.clear()
            title = line.lstrip("# ").strip()
        else:
            buf.append(line)
            if sum(len(x) for x in buf) > 2400:
                flush()
                buf.clear()
    flush()
    return chunks


def build_index(root: Path, output: Path) -> int:
    docs: list[dict] = []
    for path in sorted((root / "sources").rglob("*")):
        if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
            docs.extend(split_markdown(path, root))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(docs, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(docs)


def search(root: Path, query: str, limit: int = 6) -> list[tuple[float, dict]]:
    path = root / "data" / "index.json"
    if not path.exists():
        raise FileNotFoundError("Índice ausente. Rode `pista index` primeiro.")
    docs = json.loads(path.read_text(encoding="utf-8"))
    q = tokens(query)
    if not q or not docs:
        return []
    avgdl = sum(len(d["tokens"]) for d in docs) / len(docs)
    df = Counter(term for d in docs for term in set(d["tokens"]))
    scored = []
    for doc in docs:
        freq = Counter(doc["tokens"])
        dl = len(doc["tokens"])
        score = 0.0
        for term in q:
            f = freq[term]
            if f:
                idf = math.log(1 + (len(docs) - df[term] + 0.5) / (df[term] + 0.5))
                score += idf * (f * 2.2) / (f + 1.2 * (0.25 + 0.75 * dl / avgdl))
        if score:
            scored.append((score, doc))
    return sorted(scored, key=lambda item: item[0], reverse=True)[:limit]
