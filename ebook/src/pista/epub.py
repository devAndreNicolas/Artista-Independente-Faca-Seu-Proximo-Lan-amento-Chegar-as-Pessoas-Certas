"""Compilador EPUB 3 mínimo, sem dependência externa."""
from __future__ import annotations

import html
import re
import zipfile
from pathlib import Path


def markdown_to_xhtml(text: str, title: str) -> str:
    out: list[str] = []
    paragraph: list[str] = []
    in_list = False

    def flush() -> None:
        if paragraph:
            out.append("<p>" + " ".join(paragraph) + "</p>")
            paragraph.clear()

    for line in text.splitlines():
        s = line.strip()
        if not s:
            flush()
            if in_list:
                out.append("</ul>"); in_list = False
            continue
        if s.startswith("#"):
            flush()
            if in_list:
                out.append("</ul>"); in_list = False
            level = min(len(s) - len(s.lstrip("#")), 3)
            heading = html.escape(s.lstrip("# "))
            if level > 1:
                out.append(f"<h{level}>{heading}</h{level}>")
        elif s.startswith("- ") or re.match(r"\d+\. ", s):
            flush()
            if not in_list:
                out.append("<ul>"); in_list = True
            item = re.sub(r"^(?:- |\d+\. )", "", s)
            out.append(f"<li>{inline(item)}</li>")
        else:
            if in_list:
                out.append("</ul>"); in_list = False
            paragraph.append(inline(s))
    flush()
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def inline(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    return escaped


def compile_epub(root: Path, output: Path) -> Path:
    chapters = sorted((root / "manuscript").glob("*.md"))
    if not chapters:
        raise ValueError("Nenhum capítulo Markdown encontrado em manuscript/.")
    output.parent.mkdir(parents=True, exist_ok=True)
    uid = "urn:pista:artista-independente"
    nav = []
    pages = []
    for i, path in enumerate(chapters, 1):
        title = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        filename = f"chapter-{i:02}.xhtml"
        body = markdown_to_xhtml(path.read_text(encoding="utf-8"), title)
        pages.append((filename, title, body))
        nav.append(f'<li><a href="{filename}">{html.escape(title)}</a></li>')
    with zipfile.ZipFile(output, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>''')
        manifest = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>']
        spine = []
        for i, (filename, _, _) in enumerate(pages, 1):
            manifest.append(f'<item id="c{i}" href="{filename}" media-type="application/xhtml+xml"/>')
            spine.append(f'<itemref idref="c{i}"/>')
        z.writestr("EPUB/nav.xhtml", '<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><head><title>Sumário</title></head><body><nav epub:type="toc"><h1>Sumário</h1><ol>' + ''.join(nav) + '</ol></nav></body></html>')
        z.writestr("EPUB/package.opf", '<?xml version="1.0" encoding="utf-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid" xml:lang="pt-BR"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="uid">' + uid + '</dc:identifier><dc:title>Artista Independente: Faça Seu Próximo Lançamento Chegar às Pessoas Certas</dc:title><dc:language>pt-BR</dc:language><dc:creator>Projeto PISTA</dc:creator></metadata><manifest>' + ''.join(manifest) + '</manifest><spine>' + ''.join(spine) + '</spine></package>')
        for filename, _, body in pages:
            z.writestr("EPUB/" + filename, '<?xml version="1.0" encoding="utf-8"?>\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pt-BR"><head><title>Capítulo</title><style>body{font-family:serif;line-height:1.55;margin:8%}h1,h2{font-family:sans-serif;line-height:1.2}li{margin:.45em 0}</style></head><body>' + body + '</body></html>')
    return output
