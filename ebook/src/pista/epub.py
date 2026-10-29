"""EPUB 3 refluível; usa apenas biblioteca padrão para funcionar offline."""
from __future__ import annotations

import html
import uuid
import zipfile
from pathlib import Path

from .markdown import to_xhtml

TITLE = "Artista Independente: Faça Seu Próximo Lançamento Chegar às Pessoas Certas"
CSS = """
body { font-family: serif; line-height: 1.6; margin: 7%; color: #252a27; }
h1, h2, h3 { font-family: sans-serif; line-height: 1.2; color: #173b32; }
h1 { margin: 0 0 1.2em; }
p { margin: 0 0 1em; }
blockquote { margin: 1.2em 0; padding: .2em 0 .2em 1em; border-left: 3px solid #c18b54; }
li { margin: .35em 0; }
table { border-collapse: collapse; width: 100%; font-size: .9em; }
th, td { border-bottom: 1px solid #d9ded9; padding: .5em; text-align: left; vertical-align: top; }
th { color: #173b32; }
a { color: #245c4c; }
.cover { margin: 22% 8%; text-align: left; }
.cover h1 { font-size: 2.2em; }
.cover p { color: #59645d; }
"""


def compile_epub(root: Path, output: Path) -> Path:
    chapters = sorted((root / "manuscript").glob("*.md"))
    if not chapters:
        raise ValueError("Nenhum capítulo Markdown encontrado em manuscript/.")
    output.parent.mkdir(parents=True, exist_ok=True)
    identifier = "urn:uuid:" + str(uuid.uuid5(uuid.NAMESPACE_URL, TITLE))
    pages = []
    nav = []
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="css" href="style/book.css" media-type="text/css"/>',
        '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>',
    ]
    spine = ['<itemref idref="cover"/>']
    for i, path in enumerate(chapters, 1):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        filename = f"chapter-{i:02}.xhtml"
        pages.append((filename, title, to_xhtml(text)))
        nav.append(f'<li><a href="{filename}">{html.escape(title)}</a></li>')
        manifest.append(f'<item id="chapter{i}" href="{filename}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="chapter{i}"/>')
    nav_doc = ('<?xml version="1.0" encoding="utf-8"?>'
               '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="pt-BR">'
               '<head><title>Sumário</title><link rel="stylesheet" type="text/css" href="style/book.css"/></head>'
               '<body><nav epub:type="toc" id="toc"><h1>Conteúdo</h1><ol>' + ''.join(nav) + '</ol></nav></body></html>')
    cover_doc = ('<?xml version="1.0" encoding="utf-8"?>'
                 '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pt-BR"><head><title>Capa</title>'
                 '<link rel="stylesheet" type="text/css" href="style/book.css"/></head><body><div class="cover">'
                 '<p>GUIA PRÁTICO</p><h1>' + html.escape(TITLE) +
                 '</h1><p>Um passo possível de cada vez.</p><p>Projeto PISTA</p></div></body></html>')
    package = ('<?xml version="1.0" encoding="utf-8"?>'
               '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="pt-BR">'
               '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/">'
               f'<dc:identifier id="bookid">{identifier}</dc:identifier><dc:title>{html.escape(TITLE)}</dc:title>'
               '<dc:language>pt-BR</dc:language><dc:creator>Projeto PISTA</dc:creator>'
               '<dc:description>Guia prático e direto para planejar, lançar e aprender com um single independente.</dc:description>'
               '<meta property="dcterms:modified">2026-10-28T00:00:00Z</meta></metadata><manifest>' + ''.join(manifest) +
               '</manifest><spine>' + ''.join(spine) + '</spine></package>')
    with zipfile.ZipFile(output, "w") as zf:
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", '<?xml version="1.0" encoding="utf-8"?><container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="EPUB/package.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        zf.writestr("EPUB/package.opf", package)
        zf.writestr("EPUB/nav.xhtml", nav_doc)
        zf.writestr("EPUB/cover.xhtml", cover_doc)
        zf.writestr("EPUB/style/book.css", CSS)
        for filename, _, body in pages:
            xhtml = ('<?xml version="1.0" encoding="utf-8"?>'
                     '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pt-BR"><head><title>Capítulo</title>'
                     '<link rel="stylesheet" type="text/css" href="style/book.css"/></head><body>' + body + '</body></html>')
            zf.writestr("EPUB/" + filename, xhtml)
    return output
