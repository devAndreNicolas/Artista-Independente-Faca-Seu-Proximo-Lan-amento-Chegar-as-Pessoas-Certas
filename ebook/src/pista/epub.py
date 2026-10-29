"""EPUB 3 refluível; usa apenas biblioteca padrão para funcionar offline."""
from __future__ import annotations

import html
import uuid
import zipfile
from pathlib import Path

from .design import CHAPTER_ART, PALETTE
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
.idea-list { padding-left: 2.2em; }
.idea-list li { background: $PAPER_ALT; border-left: .2em solid $CORAL; padding: .65em .8em; margin: .55em 0; break-inside: avoid; }
.check { list-style: none; margin-left: -1.2em; }
.checkbox { color: $TEAL; font-size: 1.15em; }
figure { margin: 1.3em 0; }
figure img { display: block; max-width: 100%; height: auto; }
table { border-collapse: collapse; width: 100%; font-size: .88em; margin: 1.1em 0 1.4em; }
th, td { border-bottom: 1px solid $LINE; padding: .62em .55em; text-align: left; vertical-align: top; }
th { color: $PAPER; background: $PLUM; font-family: sans-serif; }
tr:nth-child(even) td { background: $PAPER_ALT; }
a { color: $CORAL; text-decoration: underline; }
.callout { margin: 1.4em 0; padding: .8em 1em .15em; background: $PAPER_ALT; border-left: .3em solid $CORAL; }
.cover { margin: 0; text-align: left; }
.cover-art { display: block; width: 100%; margin: 0 auto 1em; }
.cover h1 { font-size: 2.35em; line-height: 1.08; margin: .4em 0; }
.cover-copy { padding: 1em 6%; background: $PLUM; color: $PAPER; }
.cover-copy h1, .cover-copy p { color: $PAPER; }
.chapter-art { display: block; width: 100%; height: auto; margin: 0 0 1.4em; }
.chapter-label { color: $CORAL; font: bold .78em sans-serif; letter-spacing: .1em; margin: .7em 0 1.1em; }
.route img { display: block; width: 100%; margin: 0 0 1.2em; }
.route ol { padding-left: 1.3em; }
.route li { margin: .8em 0; }
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
        '<item id="cover-art" href="images/studio-cover.jpg" media-type="image/jpeg" properties="cover-image"/>',
        '<item id="roadmap-art" href="images/studio-roadmap.jpg" media-type="image/jpeg"/>',
        '<item id="chapter-art-a" href="images/studio-chapter.jpg" media-type="image/jpeg"/>',
        '<item id="chapter-art-b" href="images/roadmap-chapter.jpg" media-type="image/jpeg"/>',
        '<item id="chapter-art-c" href="images/recording-chapter.jpg" media-type="image/jpeg"/>',
        '<item id="chapter-art-d" href="images/review-chapter.jpg" media-type="image/jpeg"/>',
        '<item id="roadmap" href="roadmap.xhtml" media-type="application/xhtml+xml"/>',
        '<item id="pista-map" href="images/pista-map.svg" media-type="image/svg+xml"/>',
        '<item id="trilha" href="images/trilha.svg" media-type="image/svg+xml"/>',
    ]
    spine = ['<itemref idref="cover"/>', '<itemref idref="roadmap"/>']
    nav.append('<li><a href="roadmap.xhtml">O caminho: cinco movimentos</a></li>')
    for i, path in enumerate(chapters, 1):
        text = path.read_text(encoding="utf-8")
        title = text.splitlines()[0].lstrip("# ").strip()
        filename = f"chapter-{i:02}.xhtml"
        art = CHAPTER_ART[i-1]
        phase = ("Comece", "Prepare", "Prepare", "Apresente", "Conecte", "Lance", "Aprenda", "Planeje", "Consulte")[i-1]
        body = (f'<img class="chapter-art" src="images/{art}" alt="Fotografia editorial de criação musical"/>'
                f'<p class="chapter-label">CAPÍTULO {i:02d} / 09 · {phase.upper()}</p>' + to_xhtml(text))
        pages.append((filename, title, body))
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
                 '<img class="cover-art" src="images/studio-cover.jpg" alt="Microfone em uma sala de ensaio iluminada"/>'
                 '<div class="cover-copy"><p class="cover-kicker">UM GUIA PARA ARTISTAS INDEPENDENTES</p><h1>' + html.escape(TITLE) +
                 '</h1><p>Um passo possível de cada vez.</p><p>Projeto PISTA</p></div></div></body></html>')
    roadmap_doc = ('<?xml version="1.0" encoding="utf-8"?>'
                   '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pt-BR"><head><title>O caminho</title>'
                   '<link rel="stylesheet" type="text/css" href="style/book.css"/></head><body><section class="route">'
                   '<img src="images/studio-roadmap.jpg" alt="Cinco cartões em uma mesa de trabalho musical"/>'
                   '<h1>Uma música. Cinco movimentos.</h1><ol>'
                   '<li><b>Prepare:</b> clareza, público e lançamento pronto.</li>'
                   '<li><b>Escute:</b> feedback antes de ampliar a conversa.</li>'
                   '<li><b>Apresente:</b> conteúdo e relações com intenção.</li>'
                   '<li><b>Lance:</b> um dia simples e uma primeira semana ativa.</li>'
                   '<li><b>Aprenda:</b> o que funcionou e o próximo passo.</li>'
                   '</ol></section></body></html>')
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
        zf.writestr("EPUB/roadmap.xhtml", roadmap_doc)
        zf.writestr("EPUB/style/book.css", CSS)
        zf.write(root / "assets" / "cover.svg", "EPUB/images/soundmark.svg")
        for image_name in ("studio-cover.jpg", "studio-roadmap.jpg", "studio-chapter.jpg", "roadmap-chapter.jpg", "recording-chapter.jpg", "review-chapter.jpg"):
            zf.write(root / "assets" / image_name, "EPUB/images/" + image_name)
        zf.write(root / "assets" / "pista-map.svg", "EPUB/images/pista-map.svg")
        zf.write(root / "assets" / "trilha.svg", "EPUB/images/trilha.svg")
        for filename, _, body in pages:
            xhtml = ('<?xml version="1.0" encoding="utf-8"?>'
                     '<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="pt-BR"><head><title>Capítulo</title>'
                     '<link rel="stylesheet" type="text/css" href="style/book.css"/></head><body>' + body + '</body></html>')
            zf.writestr("EPUB/" + filename, xhtml)
    return output
