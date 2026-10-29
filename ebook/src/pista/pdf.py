"""PDF A5 com imagens JPEG e texto Unicode embutido por PyMuPDF."""
from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path

from .epub import TITLE
from .design import CHAPTER_ART, rgb
from .markdown import parse_markdown

PAGE_W, PAGE_H = 419.53, 595.28
MARGIN = 48.0
PHASES = ("COMECE", "PREPARE", "PREPARE", "APRESENTE", "CONECTE", "LANCE", "APRENDA", "PLANEJE", "CONSULTE")
PAPER = rgb("paper")
PAPER_ALT = rgb("paper_alt")
PLUM = rgb("plum")
CORAL = rgb("coral")
GOLD = rgb("gold")
TEAL = rgb("teal")
INK = rgb("ink")
MUTED = rgb("muted")
LILAC = rgb("lilac")
LINE = rgb("line")
CHAPTER_ACCENTS = (CORAL, TEAL, TEAL, CORAL, GOLD, CORAL, TEAL, GOLD, PLUM)
LINK_RE = re.compile(r'<a href="(https?://[^\"]+)">(.*?)</a>')


def _plain(markup: str) -> str:
    markup = re.sub(LINK_RE, r"\2", markup)
    markup = re.sub(r"</?(?:b|i|strong|em)>", "", markup)
    return html.unescape(markup)


def _pdf_text(value: str) -> str:
    value = value.replace("−", "-").replace("–", "-").replace("—", "-" ).replace("…", "...")
    return value.encode("cp1252", errors="replace").hex().upper()


class Layout:
    def __init__(self) -> None:
        self.images: dict[str, Path] = {}
        self.pages: list[list[str]] = []
        self.page_chapters: list[int] = []
        self.chapter_open_pages: set[int] = set()
        self.current_chapter = 0
        self.section_no = 0
        self.text_runs: list[list[tuple[str, float, str, tuple[float, float, float], float, float]]] = []
        self.links: list[list[tuple[float, float, float, float, str]]] = []
        self.internal_links: list[list[tuple[float, float, float, float, int]]] = []
        self.destinations: dict[str, tuple[int, float]] = {}
        self.y = 0.0
        self.new_page()

    def new_page(self) -> None:
        self.pages.append([])
        self.page_chapters.append(self.current_chapter)
        self.text_runs.append([])
        self.links.append([])
        self.internal_links.append([])
        self.y = PAGE_H - MARGIN
        self.rect(0, 0, PAGE_W, PAGE_H, PAPER)
        if self.current_chapter:
            self.rect(0, 0, 3, PAGE_H, CHAPTER_ACCENTS[self.current_chapter-1])

    def ensure(self, height: float) -> None:
        if self.y - height < MARGIN:
            self.new_page()

    def raw(self, op: str) -> None:
        self.pages[-1].append(op)

    def photo(self, key: str, path: Path, x: float, y: float, w: float, h: float) -> None:
        self.images[key] = path
        self.raw(f"q {w:.2f} 0 0 {h:.2f} {x:.2f} {y:.2f} cm /{key} Do Q")

    def rect(self, x: float, y: float, w: float, h: float, color: tuple[float, float, float], stroke=False) -> None:
        r, g, b = color
        self.raw(f"q {r:.3f} {g:.3f} {b:.3f} {'RG' if stroke else 'rg'} {x:.2f} {y:.2f} {w:.2f} {h:.2f} re {'S' if stroke else 'f'} Q")

    def circle(self, cx: float, cy: float, radius: float, color: tuple[float, float, float], *, stroke=False, width=1.0) -> None:
        k = .55228475 * radius
        path = (f"{cx+radius:.2f} {cy:.2f} m {cx+radius:.2f} {cy+k:.2f} {cx+k:.2f} {cy+radius:.2f} {cx:.2f} {cy+radius:.2f} c "
                f"{cx-k:.2f} {cy+radius:.2f} {cx-radius:.2f} {cy+k:.2f} {cx-radius:.2f} {cy:.2f} c "
                f"{cx-radius:.2f} {cy-k:.2f} {cx-k:.2f} {cy-radius:.2f} {cx:.2f} {cy-radius:.2f} c "
                f"{cx+k:.2f} {cy-radius:.2f} {cx+radius:.2f} {cy-k:.2f} {cx+radius:.2f} {cy:.2f} c")
        r, g, b = color
        self.raw(f"q {r:.3f} {g:.3f} {b:.3f} {'RG' if stroke else 'rg'} {width:.2f} w {path} {'S' if stroke else 'f'} Q")

    def line(self, x1: float, y1: float, x2: float, y2: float, color=LINE, thickness=.5) -> None:
        r, g, b = color
        self.raw(f"q {r:.3f} {g:.3f} {b:.3f} RG {thickness:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S Q")

    def draw_text(self, value: str, *, size=9.5, font="F1", color=(.15, .17, .16), x=MARGIN, y=None) -> None:
        if y is None:
            y = self.y
        r, g, b = color
        self.text_runs[-1].append((value, size, font, color, x, y))
        self.raw(f"LAYOUT_TEXT BT /{font} {size:.2f} Tf {r:.3f} {g:.3f} {b:.3f} rg 1 0 0 1 {x:.2f} {y:.2f} Tm <{_pdf_text(value)}> Tj ET")

    def write(self, value: str, *, size=10.2, leading=15, font="F1", color=INK, indent=0,
              max_width=None, link: str | None = None, after=5, x=None, keep=False) -> None:
        text = value.replace("\n", " ").strip()
        if not text:
            self.y -= leading
            return
        start_x = x if x is not None else MARGIN + indent
        width = max_width or (PAGE_W - start_x - MARGIN)
        chars = max(12, int(width / (size * (.55 if font == "F2" else .49))))
        wrapped = textwrap.wrap(text, width=chars, break_long_words=True, break_on_hyphens=False) or [""]
        if keep and len(wrapped)*leading + after < PAGE_H-2*MARGIN:
            self.ensure(len(wrapped)*leading + after)
        for line_text in wrapped:
            self.ensure(leading)
            y = self.y - leading
            self.draw_text(line_text, size=size, font=font, color=color, x=start_x, y=y)
            if link:
                approximate = min(width, max(16, len(line_text) * size * .48))
                self.links[-1].append((start_x, y - 2, start_x + approximate, y + leading - 2, link))
                self.line(start_x, y-2.5, start_x+approximate, y-2.5, TEAL, .35)
            self.y -= leading
        self.y -= after

    def paragraph(self, markup: str, *, quote=False) -> None:
        callout = re.match(r"<b>(Faça|Entrega|Observe):</b>\s*(.*)", markup)
        if callout:
            self.action_card(callout.group(1), callout.group(2))
            return
        links = LINK_RE.findall(markup)
        visible = _plain(markup)
        if quote:
            self.ensure(42)
            self.rect(MARGIN, self.y - 35, PAGE_W - 2*MARGIN, 35, LILAC)
            self.rect(MARGIN, self.y - 35, 3, 35, CORAL)
        self.write(visible, font="F5", indent=12 if quote else 0, color=PLUM if quote else INK,
                   link=links[0][0] if links else None, keep=True)
        self.y -= 3

    def action_card(self, label: str, markup: str) -> None:
        text = _plain(markup)
        width = PAGE_W - 2*MARGIN - 24
        wrapped = textwrap.wrap(text, max(18, int(width / 5.1))) or [""]
        height = 31 + 14 * len(wrapped)
        self.ensure(height + 8)
        bottom = self.y - height
        tint = (0.965, 0.922, 0.894) if label == "Faça" else ((0.895, 0.937, 0.906) if label == "Entrega" else LILAC)
        self.rect(MARGIN, bottom, PAGE_W - 2*MARGIN, height, tint)
        self.rect(MARGIN, bottom, 4, height, CORAL if label == "Faça" else TEAL if label == "Entrega" else GOLD)
        accent = CORAL if label == "Faça" else TEAL if label == "Entrega" else PLUM
        self.draw_text(label.upper(), size=8, font="F2", color=accent, x=MARGIN+14, y=self.y-16)
        for i, line_text in enumerate(wrapped):
            self.draw_text(line_text, size=9.5, font="F1", color=INK, x=MARGIN+14, y=self.y-32-i*13)
        self.y = bottom - 9

    def section_heading(self, text: str, *, small=False) -> None:
        accent = CHAPTER_ACCENTS[self.current_chapter-1] if self.current_chapter else CORAL
        self.ensure((100 if self.current_chapter == 9 else 125) if not small else 55)
        self.y -= 8 if not small else 4
        if small:
            self.write(text, size=10.8, leading=15, font="F2", color=TEAL,
                       indent=0, after=7, keep=True)
            return
        self.section_no += 1
        self.line(MARGIN, self.y, MARGIN+31, self.y, accent, 1.7)
        self.y -= 10
        self.draw_text(f"{self.section_no:02d}", size=8.4, font="F2", color=accent,
                       x=MARGIN, y=self.y-4)
        self.write(text, size=13, leading=18, font="F2", color=PLUM,
                   x=MARGIN+27, max_width=PAGE_W-2*MARGIN-27, after=8, keep=True)

    def chapter_open(self, number: int, title: str, key: str, path: Path) -> None:
        self.current_chapter = number
        self.page_chapters[-1] = number
        self.chapter_open_pages.add(len(self.pages)-1)
        self.section_no = 0
        self.photo(key, path, 0, PAGE_H-235, PAGE_W, 235)
        self.rect(MARGIN-12, PAGE_H-310, PAGE_W-2*MARGIN+24, 154, PAPER)
        self.y = PAGE_H-169
        accent = CHAPTER_ACCENTS[number-1]
        self.write(f"CAPÍTULO {number:02d} / 09     {PHASES[number-1]}", size=8.3,
                   leading=13, font="F2", color=accent, after=11)
        self.line(MARGIN, self.y, MARGIN+46, self.y, GOLD, 2.2)
        self.y -= 12
        self.write(title, size=21.5, leading=27, font="F4", color=PLUM, after=15, keep=True)

    def toc_item(self, number: int, title: str, target: int) -> None:
        height = 39
        self.ensure(height + 5)
        top = self.y
        bottom = top - height
        self.rect(MARGIN, bottom, PAGE_W-2*MARGIN, height-3, PAPER_ALT if number % 2 else LILAC)
        self.circle(MARGIN+16, top-18, 10, PLUM if number % 2 else TEAL)
        self.draw_text(f"{number:02d}", size=7.2, font="F2", color=PAPER, x=MARGIN+9.7, y=top-20.5)
        self.write(title, size=9.5, leading=12, font="F2", color=PLUM,
                   x=MARGIN+34, max_width=PAGE_W-2*MARGIN-44, after=0)
        self.internal_links[-1].append((MARGIN, bottom, PAGE_W-MARGIN, top, target))
        self.y = bottom - 4

    def infographic(self, source: str) -> None:
        if source.endswith("pista-map.svg"):
            height = 93
            self.ensure(height + 7)
            top = self.y
            self.rect(MARGIN, top-height, PAGE_W-2*MARGIN, height, PAPER_ALT)
            centers = [MARGIN+29+i*66 for i in range(5)]
            self.line(centers[0], top-38, centers[-1], top-38, LINE, 2)
            for index, (x, letter, label) in enumerate(zip(centers, "PISTA", ("Público", "Identidade", "Saídas", "Tentativas", "Aprender"))):
                fill = (PLUM, CORAL, TEAL, PLUM, CORAL)[index]
                self.circle(x, top-38, 16, fill)
                self.draw_text(letter, size=12, font="F2", color=PAPER, x=x-4, y=top-42)
                self.draw_text(label, size=7.2, font="F2", color=PLUM, x=x-len(label)*1.8, y=top-73)
            self.y = top-height-11
        elif source.endswith("trilha.svg"):
            height = 124
            self.ensure(height + 7)
            top = self.y
            self.rect(MARGIN, top-height, PAGE_W-2*MARGIN, height, PAPER_ALT)
            x = MARGIN+23
            self.line(x, top-16, x, top-108, LINE, 2.5)
            labels = (("Prepare", "cerca de 1 mês antes"), ("Escute", "nas semanas seguintes"),
                      ("Organize", "antes da estreia"), ("Lance", "no dia combinado"),
                      ("Aprenda", "no mês seguinte"))
            for index, (label, timing) in enumerate(labels):
                y = top-20-index*22
                self.circle(x, y, 8, (PLUM, CORAL, TEAL, PLUM, CORAL)[index])
                self.draw_text(label, size=9, font="F2", color=PLUM, x=x+17, y=y-3)
                self.draw_text(timing, size=7.8, font="F1", color=MUTED, x=x+104, y=y-3)
            self.y = top-height-11
        else:
            raise ValueError(f"Imagem sem renderização PDF: {source}")

    def table(self, rows: list[list[str]]) -> None:
        if not rows:
            return
        columns = max(len(row) for row in rows)
        width = PAGE_W - 2*MARGIN
        widths = [width * .28] + [width * .72 / (columns - 1)] * (columns - 1) if columns > 1 else [width]
        normalized = [row + [""] * (columns - len(row)) for row in rows]
        prepared = []
        for row in normalized:
            wrapped = []
            for col, cell in enumerate(row):
                value = _plain(cell)
                maxchars = max(8, int((widths[col] - 12) / 4.35))
                wrapped.append(textwrap.wrap(value, maxchars, break_long_words=True) or [""])
            row_height = max(1, max(map(len, wrapped))) * 11 + 10
            prepared.append((wrapped, row_height))
        self.ensure(sum(height for _, height in prepared[:2]) + 10)
        for ridx, (wrapped, row_height) in enumerate(prepared):
            self.ensure(row_height + 2)
            bottom = self.y - row_height
            row_color = PLUM if ridx == 0 else (PAPER_ALT if ridx % 2 else PAPER)
            self.rect(MARGIN, bottom, width, row_height, row_color)
            self.line(MARGIN, bottom, MARGIN+width, bottom, LINE, .4)
            x = MARGIN
            for col, lines in enumerate(wrapped):
                color = PAPER if ridx == 0 else INK
                font = "F2" if ridx == 0 else "F1"
                for n, line_text in enumerate(lines):
                    self.draw_text(line_text, size=7.8, font=font, color=color, x=x+6,
                                   y=self.y-15-n*11)
                x += widths[col]
                if col < columns - 1:
                    self.line(x, bottom, x, self.y, LINE, .35)
            self.y = bottom
        self.y -= 8

    def ideas(self, items: list[str]) -> None:
        """As vinte ideias aparecem como cartões de consulta rápida."""
        gap = 9
        card_w = (PAGE_W-2*MARGIN-gap)/2
        accent = CHAPTER_ACCENTS[self.current_chapter-1]
        for start in range(0, len(items), 2):
            pair = []
            for item in items[start:start+2]:
                match = re.match(r"<b>(.*?)</b>\s*(.*)", item)
                label = _plain(match.group(1)) if match else "Ideia"
                detail = _plain(match.group(2)) if match else _plain(item)
                label_lines = textwrap.wrap(label, 22, break_long_words=False) or [label]
                detail_lines = textwrap.wrap(detail, 31, break_long_words=False) or [detail]
                height = 45 + max(0, len(label_lines)-1)*11 + len(detail_lines)*11
                pair.append((label_lines, detail_lines, height))
            row_h = max(card[2] for card in pair)
            self.ensure(row_h+gap)
            top = self.y
            for side, (labels, details, _) in enumerate(pair):
                x = MARGIN + side*(card_w+gap)
                self.rect(x, top-row_h, card_w, row_h, PAPER_ALT if (start//2+side)%2 == 0 else LILAC)
                self.rect(x, top-row_h, 2.5, row_h, accent)
                self.draw_text(f"{start+side+1:02d}", size=8, font="F2", color=accent, x=x+10, y=top-17)
                for n, line_text in enumerate(labels):
                    self.draw_text(line_text, size=8.6, font="F2", color=PLUM, x=x+31, y=top-17-n*11)
                first_detail_y = top-34-(len(labels)-1)*11
                for n, line_text in enumerate(details):
                    self.draw_text(line_text, size=8.2, color=INK, x=x+10, y=first_detail_y-n*11)
            self.y = top-row_h-gap

    def checklist_item(self, item: str) -> None:
        value = _plain(item).removeprefix("[ ]").strip()
        x = MARGIN+27
        width = PAGE_W-x-MARGIN
        lines = textwrap.wrap(value, max(12, int(width/(9.5*.49))),
                              break_long_words=False) or [value]
        self.ensure(len(lines)*14+5)
        self.rect(MARGIN+7, self.y-15, 10, 10, PLUM, stroke=True)
        self.write(value, size=9.5, leading=14, x=x, max_width=width,
                   after=3, color=INK, keep=True)


def _write_pdf(output: Path, layout: Layout) -> Path:
    try:
        import pymupdf
    except ImportError as exc:
        raise RuntimeError("PDF com texto Unicode requer PyMuPDF: python -m pip install PyMuPDF") from exc
    objects: list[bytes | None] = [None] * 7
    def add(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)
    def set_obj(number: int, payload: bytes) -> None:
        objects[number - 1] = payload

    page_numbers = []
    for page_index, ops in enumerate(layout.pages):
        chapter_number = layout.page_chapters[page_index]
        accent = CHAPTER_ACCENTS[chapter_number-1] if chapter_number else CORAL
        if page_index > 0:
            yline = 32
            ops.extend([
                f"q {LINE[0]} {LINE[1]} {LINE[2]} RG .6 w {MARGIN} {yline+8} m {PAGE_W-MARGIN} {yline+8} l S Q",
                f"q {accent[0]} {accent[1]} {accent[2]} rg {MARGIN} {yline+6} 25 3 re f Q",
                f"BT /F1 7 Tf {MUTED[0]} {MUTED[1]} {MUTED[2]} rg 1 0 0 1 {MARGIN+32} {yline} Tm <{_pdf_text('GUIA PISTA - LANCAMENTO MUSICAL')}> Tj ET",
                f"q {LILAC[0]} {LILAC[1]} {LILAC[2]} rg {PAGE_W-MARGIN-29} {yline-2} 29 13 re f Q",
                f"BT /F2 7 Tf {PLUM[0]} {PLUM[1]} {PLUM[2]} rg 1 0 0 1 {PAGE_W-MARGIN-20} {yline+1} Tm <{_pdf_text(str(page_index))}> Tj ET",
            ])
            if page_index > 1 and page_index not in layout.chapter_open_pages:
                header = f"PISTA  /  {PHASES[chapter_number-1]}" if chapter_number else "ARTISTA INDEPENDENTE  /  PISTA"
                ops.insert(1, f"BT /F2 7 Tf {MUTED[0]} {MUTED[1]} {MUTED[2]} rg 1 0 0 1 {MARGIN} {PAGE_H-27} Tm <{_pdf_text(header)}> Tj ET")
        stream = "\n".join(op for op in ops if not op.startswith("LAYOUT_TEXT ")).encode("ascii")
        stream_no = add(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        page_no = add(b"")
        page_numbers.append((page_no, stream_no, page_index))
    set_obj(3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    set_obj(4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    set_obj(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")
    set_obj(6, b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Bold /Encoding /WinAnsiEncoding >>")
    set_obj(7, b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>")
    image_refs = {}
    for key, path in layout.images.items():
        data = path.read_bytes()
        width, height = _jpeg_dimensions(data)
        header = (f"<< /Type /XObject /Subtype /Image /Width {width} /Height {height} "
                  f"/ColorSpace /DeviceRGB /BitsPerComponent 8 /Filter /DCTDecode /Length {len(data)} >>\nstream\n").encode("ascii")
        image_refs[key] = add(header + data + b"\nendstream")
    page_refs = []
    for page_no, stream_no, page_index in page_numbers:
        annots = []
        for x1, y1, x2, y2, url in layout.links[page_index]:
            url_encoded = url.encode("ascii", errors="ignore").decode("ascii")
            annot_no = add(f"<< /Type /Annot /Subtype /Link /Rect [{x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f}] /Border [0 0 0] /A << /S /URI /URI ({url_encoded}) >> >>".encode("ascii"))
            annots.append(f"{annot_no} 0 R")
        for x1, y1, x2, y2, target in layout.internal_links[page_index]:
            destination_page, destination_y = layout.destinations[f"chapter{target}"]
            target_page = page_numbers[destination_page][0]
            annot_no = add(f"<< /Type /Annot /Subtype /Link /Rect [{x1:.2f} {y1:.2f} {x2:.2f} {y2:.2f}] /Border [0 0 0] /Dest [{target_page} 0 R /XYZ null {destination_y:.2f} null] >>".encode("ascii"))
            annots.append(f"{annot_no} 0 R")
        annots_part = f" /Annots [{' '.join(annots)}]" if annots else ""
        xobjects = " ".join(f"/{key} {ref} 0 R" for key, ref in image_refs.items())
        set_obj(page_no, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W:.2f} {PAGE_H:.2f}] /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R /F5 7 0 R >> /XObject << {xobjects} >> >> /Contents {stream_no} 0 R{annots_part} >>".encode("ascii"))
        page_refs.append(f"{page_no} 0 R")
    set_obj(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    set_obj(2, ("<< /Type /Pages /Kids [" + " ".join(page_refs) + f"] /Count {len(page_refs)} >>").encode("ascii"))
    output.parent.mkdir(parents=True, exist_ok=True)
    data = bytearray(b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for index, payload in enumerate(objects, 1):
        if payload is None:
            raise RuntimeError(f"Objeto PDF {index} não foi construído.")
        offsets.append(len(data))
        data.extend(f"{index} 0 obj\n".encode("ascii")); data.extend(payload); data.extend(b"\nendobj\n")
    xref_offset = len(data)
    data.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode("ascii"))
    for offset in offsets[1:]:
        data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    data.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R /Info << /Title <{_pdf_text(TITLE)}> /Author (Projeto PISTA) >> >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
    output.write_bytes(data)
    _add_unicode_text(output, layout, pymupdf)
    return output


def _add_unicode_text(output: Path, layout: Layout, pymupdf) -> None:
    """Use fontes TrueType para preservar acentos no PDF renderizado e pesquisável."""
    fonts = {
        "F1": Path("C:/Windows/Fonts/arial.ttf"),
        "F2": Path("C:/Windows/Fonts/arialbd.ttf"),
        "F3": Path("C:/Windows/Fonts/ariali.ttf"),
        "F4": Path("C:/Windows/Fonts/timesbd.ttf"),
        "F5": Path("C:/Windows/Fonts/georgia.ttf"),
    }
    missing = [str(path) for path in fonts.values() if not path.exists()]
    if missing:
        raise RuntimeError("Fontes TrueType ausentes para texto Unicode: " + ", ".join(missing))
    document = pymupdf.open(output)
    for index, runs in enumerate(layout.text_runs):
        page = document[index]
        used = {run[2] for run in runs}
        for key in used:
            page.insert_font(fontname="Book" + key, fontfile=str(fonts[key]))
        for value, size, font, color, x, y in runs:
            page.insert_text((x, PAGE_H-y), value, fontname="Book" + font,
                             fontsize=size, color=color, overlay=True)
    temp = output.with_suffix(".unicode.pdf")
    document.save(temp, garbage=4, deflate=True)
    document.close()
    temp.replace(output)


def _jpeg_dimensions(data: bytes) -> tuple[int, int]:
    if data[:2] != b"\xff\xd8":
        raise ValueError("A imagem do PDF precisa ser JPEG.")
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        size = int.from_bytes(data[i:i+2], "big")
        if marker in (0xC0, 0xC1, 0xC2):
            return int.from_bytes(data[i+5:i+7], "big"), int.from_bytes(data[i+3:i+5], "big")
        i += size
    raise ValueError("Dimensões JPEG não encontradas.")


def compile_pdf(root: Path, output: Path) -> Path:
    chapters = sorted((root / "manuscript").glob("*.md"))
    if not chapters:
        raise ValueError("Nenhum capítulo Markdown encontrado em manuscript/.")
    layout = Layout()
    layout.photo("CoverPhoto", root / "assets" / "studio-cover.jpg", 0, 0, PAGE_W, PAGE_H)
    layout.rect(0, 0, PAGE_W, 252, PLUM)
    layout.y = 226
    layout.write("UM GUIA PARA ARTISTAS INDEPENDENTES", size=8.2, leading=14, font="F2", color=GOLD, after=19)
    layout.write("Faça seu próximo lançamento chegar às pessoas certas", size=25, leading=30,
                 font="F4", color=PAPER, max_width=PAGE_W-2*MARGIN, after=17, keep=True)
    layout.rect(MARGIN, layout.y-2, 51, 2.5, CORAL)
    layout.y -= 17
    layout.write("Um passo possível de cada vez.", size=11, leading=16, color=PAPER_ALT, after=12)

    layout.new_page()
    layout.photo("RoadmapPhoto", root / "assets" / "studio-roadmap.jpg", 0, PAGE_H-278, PAGE_W, 278)
    layout.y = PAGE_H-304
    layout.write("O CAMINHO", size=8.2, leading=13, font="F2", color=CORAL, after=6)
    layout.write("Uma música. Cinco movimentos.", size=20, leading=25, font="F4", color=PLUM, after=12)
    for n, (name, detail) in enumerate((
        ("01  Prepare", "clareza, público e lançamento pronto"),
        ("02  Escute", "feedback antes de ampliar a conversa"),
        ("03  Apresente", "conteúdo e relações com intenção"),
        ("04  Lance", "um dia simples e uma primeira semana ativa"),
        ("05  Aprenda", "o que funcionou e o próximo passo"),
    )):
        y = layout.y - 16
        layout.draw_text(name, size=10, font="F2", color=PLUM, x=MARGIN, y=y)
        layout.draw_text(detail, size=8.3, color=MUTED, x=MARGIN+109, y=y)
        layout.y -= 30

    layout.new_page()
    layout.write("NAVEGUE PELO LIVRO", size=8.5, leading=14, font="F2", color=CORAL, after=5)
    layout.write("O que você vai encontrar", size=22, leading=28, font="F4", color=PLUM, after=14)
    for chapter_index, path in enumerate(chapters):
        title = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        layout.toc_item(chapter_index+1, title, chapter_index)

    for index, path in enumerate(chapters):
        layout.current_chapter = index+1
        layout.new_page()
        layout.destinations[f"chapter{index}"] = (len(layout.pages)-1, layout.y)
        photo_name = CHAPTER_ART[index]
        photo_key = {"studio-chapter.jpg": "StudioChapter", "roadmap-chapter.jpg": "RoadmapChapter",
                     "recording-chapter.jpg": "RecordingChapter", "review-chapter.jpg": "ReviewChapter"}[photo_name]
        content = parse_markdown(path.read_text(encoding="utf-8"))
        title = _plain(content[0]["text"]) if content and content[0]["type"] == "h" else path.stem
        layout.chapter_open(index+1, title, photo_key, root / "assets" / photo_name)
        for block in content:
            kind = block["type"]
            if kind == "h":
                if block["level"] == 1:
                    continue
                elif block["level"] == 2:
                    layout.section_heading(_plain(block["text"]))
                else:
                    layout.section_heading(_plain(block["text"]), small=True)
            elif kind == "p":
                layout.paragraph(block["text"])
            elif kind == "quote":
                layout.paragraph(block["text"], quote=True)
            elif kind in ("ul", "ol"):
                if kind == "ol" and len(block["items"]) == 20:
                    layout.ideas(block["items"])
                    continue
                for item_index, item in enumerate(block["items"], 1):
                    if index == 7 and _plain(item).startswith("[ ]"):
                        layout.checklist_item(item)
                        continue
                    prefix = f"{item_index}. " if kind == "ol" else "• "
                    bibliography = index == 8
                    layout.write(prefix + _plain(item), size=8.6 if bibliography else 9.8,
                                 leading=12.5 if bibliography else 15, color=INK,
                                 indent=7 if bibliography else 8,
                                 after=1 if bibliography else 2, keep=True)
                layout.y -= 5
            elif kind == "table":
                layout.table(block["rows"])
            elif kind == "image":
                layout.infographic(block["src"])
            elif kind == "hr":
                layout.y -= 2; layout.line(MARGIN, layout.y, PAGE_W-MARGIN, layout.y, GOLD, .6); layout.y -= 10
    return _write_pdf(output, layout)
