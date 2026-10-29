"""EPUB 3 refluível; usa apenas biblioteca padrão para funcionar offline."""
from __future__ import annotations

import html
import uuid
import zipfile
from pathlib import Path

from .design import PALETTE
from .markdown import to_xhtml

TITLE = "Artista Independente: Faça Seu Próximo Lançamento Chegar às Pessoas Certas"
CSS = """
body { font-family: Georgia, serif; line-height: 1.68; margin: 6%; color: $INK; }
h1, h2, h3 { font-family: sans-serif; line-height: 1.16; color: $PLUM; }
h1 { font-size: 2em; margin: 0 0 1.1em; }
h2 { font-size: 1.35em; margin: 1.8em 0 .65em; border-left: .22em solid $CORAL; padding-left: .55em; }
h3 { font-size: 1.08em; margin: 1.45em 0 .5em; color: $TEAL; }
p { margin: 0 0 1.05em; }
blockquote { margin: 1.4em 0; padding: .65em 1em .1em; border-left: .25em solid $CORAL; background: $LILAC; color: $PLUM; }
li { margin: .48em 0; padding-left: .15em; }
figure { margin: 1.3em 0; }
figure img { display: block; max-width: 100%; height: auto; }
table { border-collapse: collapse; width: 100%; font-size: .88em; margin: 1.1em 0 1.4em; }
th, td { border-bottom: 1px solid $LINE; padding: .62em .55em; text-align: left; vertical-align: top; }
th { color: $PAPER; background: $PLUM; font-family: sans-serif; }
tr:nth-child(even) td { background: $PAPER_ALT; }
a { color: $CORAL; text-decoration: underline; }
.callout { margin: 1.4em 0; padding: .8em 1em .15em; background: $PAPER_ALT; border-left: .3em solid $CORAL; }
.cover { margin: 7% 3%; text-align: left; }
.cover-art { display: block; width: 100%; margin: 1em auto 1.2em; }
.cover h1 { font-size: 2.35em; line-height: 1.08; margin: .4em 0; }
.cover-kicker { color: $CORAL; font: bold .78em sans-serif; letter-spacing: .14em; }
.cover-tagline { color: $TEAL; font: 1.05em sans-serif; }
nav ol { list-style: none; padding: 0; }
nav li { margin: .8em 0; padding: .65em .8em; background: #f3edf4; border-left: .25em solid #ec6856; }
"""
for _token, _value in PALETTE.items():
    CSS = CSS.replace("$" + _token.upper(), _value)

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
        '<item id="cover-art" href="images/soundmark.svg" media-type="image/svg+xml" properties="cover-image"/>',
        '<item id="pista-map" href="images/pista-map.svg" media-type="image/svg+xml"/>',
        '<item id="trilha" href="images/trilha.svg" media-type="image/svg+xml"/>',
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
                 '<p class="cover-kicker">GUIA DE LANÇAMENTO MUSICAL</p><img class="cover-art" src="images/soundmark.svg" alt="Disco ameixa com anéis coral e dourados"/><h1>' + html.escape(TITLE) +
                 '</h1><p class="cover-tagline">Um passo possível de cada vez.</p><p>Projeto PISTA</p></div></body></html>')
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
        zf.write(root / "assets" / "cover.svg", "EPUB/images/soundmark.svg")
        zf.write(root / "assets" / "pista-map.svg", "EPUB/images/pista-map.svg")
        zf.write(root / "assets" / "trilha.svg", "EPUB/images/trilha.svg")
        for filename, _, body in pages:
            xhtml = ('<?xml version="1.0" encoding="utf-8"?>'
                     '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pt-BR"><head><title>Capítulo</title>'
                     '<link rel="stylesheet" type="text/css" href="style/book.css"/></head><body>' + body + '</body></html>')
            zf.writestr("EPUB/" + filename, xhtml)
    return output
