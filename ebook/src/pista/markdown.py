"""Subset Markdown do manuscrito, compartilhado pelos dois formatos."""
from __future__ import annotations

import html
import re


def inline(text: str) -> str:
    value = html.escape(text, quote=False)
    value = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"\*(.+?)\*", r"<i>\1</i>", value)
    return value


def parse_markdown(text: str) -> list[dict]:
    lines = text.splitlines()
    blocks: list[dict] = []
    para: list[str] = []
    list_kind: str | None = None
    items: list[str] = []
    quote: list[str] = []

    def flush_para() -> None:
        if para:
            blocks.append({"type": "p", "text": inline(" ".join(x.strip() for x in para))})
            para.clear()

    def flush_list() -> None:
        nonlocal list_kind
        if items:
            blocks.append({"type": list_kind or "ul", "items": [inline(x) for x in items]})
            items.clear()
        list_kind = None

    def flush_quote() -> None:
        if quote:
            blocks.append({"type": "quote", "text": inline(" ".join(x.strip() for x in quote))})
            quote.clear()

    i = 0
    while i < len(lines):
        raw = lines[i]
        s = raw.strip()
        if not s:
            flush_para(); flush_list(); flush_quote(); i += 1; continue
        image_match = re.fullmatch(r"!\[([^\]]*)\]\(([^)]+)\)", s)
        if image_match:
            flush_para(); flush_list(); flush_quote()
            blocks.append({"type": "image", "alt": image_match.group(1), "src": image_match.group(2)})
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            flush_para(); flush_list(); flush_quote()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [cell.strip() for cell in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
                    rows.append([inline(cell) for cell in cells])
                i += 1
            if rows:
                blocks.append({"type": "table", "rows": rows})
            continue
        if s.startswith("#"):
            flush_para(); flush_list(); flush_quote()
            level = min(len(s) - len(s.lstrip("#")), 3)
            blocks.append({"type": "h", "level": level, "text": inline(s.lstrip("# "))})
        elif s.startswith("> "):
            flush_para(); flush_list(); quote.append(s[2:])
        elif re.match(r"^[-*] ", s):
            flush_para(); flush_quote()
            if list_kind not in (None, "ul"):
                flush_list()
            list_kind = "ul"
            items.append(re.sub(r"^[-*] ", "", s))
        elif re.match(r"^\d+[.)] ", s):
            flush_para(); flush_quote()
            if list_kind not in (None, "ol"):
                flush_list()
            list_kind = "ol"
            items.append(re.sub(r"^\d+[.)] ", "", s))
        elif re.fullmatch(r"-{3,}|\*{3,}", s):
            flush_para(); flush_list(); flush_quote()
            blocks.append({"type": "hr"})
        else:
            flush_list(); flush_quote(); para.append(s)
        i += 1
    flush_para(); flush_list(); flush_quote()
    return blocks


def to_xhtml(text: str) -> str:
    result = []
    for block in parse_markdown(text):
        kind = block["type"]
        if kind == "h":
            result.append(f'<h{block["level"]}>{block["text"]}</h{block["level"]}>')
        elif kind == "p":
            if re.match(r"<b>(Faça|Entrega|Observe):</b>", block["text"]):
                result.append(f'<aside class="callout"><p>{block["text"]}</p></aside>')
            else:
                result.append(f'<p>{block["text"]}</p>')
        elif kind == "quote":
            result.append(f'<blockquote><p>{block["text"]}</p></blockquote>')
        elif kind in ("ul", "ol"):
            extra = ' class="idea-list"' if kind == "ol" and len(block["items"]) == 20 else ""
            result.append(f"<{kind}{extra}>" + "".join(f"<li>{item}</li>" for item in block["items"]) + f"</{kind}>")
        elif kind == "table":
            rows = []
            for r, cells in enumerate(block["rows"]):
                tag = "th" if r == 0 else "td"
                rows.append("<tr>" + "".join(f"<{tag}>{cell}</{tag}>" for cell in cells) + "</tr>")
            result.append("<table><tbody>" + "".join(rows) + "</tbody></table>")
        elif kind == "hr":
            result.append("<hr />")
        elif kind == "image":
            source = block["src"].replace("../assets/", "images/")
            result.append(f'<figure><img src="{html.escape(source, quote=True)}" alt="{html.escape(block["alt"], quote=True)}" /></figure>')
    return "\n".join(result)
