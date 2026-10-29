"""PDF A5 enxuto, com backend local de biblioteca padrão para uso offline."""
from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path

from .epub import TITLE
from .design import rgb
from .markdown import parse_markdown

PAGE_W, PAGE_H = 419.53, 595.28
MARGIN = 48.0
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
        self.pages: list[list[str]] = []
        self.links: list[list[tuple[float, float, float, float, str]]] = []
        self.internal_links: list[list[tuple[float, float, float, float, int]]] = []
        self.destinations: dict[str, tuple[int, float]] = {}
        self.y = 0.0
        self.new_page()

    def new_page(self) -> None:
        self.pages.append([])
        self.links.append([])
        self.internal_links.append([])
        self.y = PAGE_H - MARGIN
        self.rect(0, 0, PAGE_W, PAGE_H, PAPER)

    def ensure(self, height: float) -> None:
        if self.y - height < MARGIN:
            self.new_page()

    def raw(self, op: str) -> None:
        self.pages[-1].append(op)

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
        self.raw(f"BT /{font} {size:.2f} Tf {r:.3f} {g:.3f} {b:.3f} rg 1 0 0 1 {x:.2f} {y:.2f} Tm <{_pdf_text(value)}> Tj ET")

    def write(self, value: str, *, size=10.2, leading=15, font="F1", color=INK, indent=0,
              max_width=None, link: str | None = None, after=5, x=None) -> None:
        text = value.replace("\n", " ").strip()
        if not text:
            self.y -= leading
            return
        start_x = x if x is not None else MARGIN + indent
        width = max_width or (PAGE_W - start_x - MARGIN)
        chars = max(12, int(width / (size * (.55 if font == "F2" else .49))))
        wrapped = textwrap.wrap(text, width=chars, break_long_words=True, break_on_hyphens=False) or [""]
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
        self.write(visible, indent=12 if quote else 0, color=PLUM if quote else INK,
                   link=links[0][0] if links else None)
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
        self.ensure(35)
        self.y -= 4
        self.rect(MARGIN, self.y-12, 3.5, 17, CORAL if not small else GOLD)
        self.write(text, size=11.5 if small else 13, leading=16 if small else 18,
                   font="F2", color=PLUM if not small else TEAL, indent=12, after=6)

    def chapter_open(self, number: int, title: str) -> None:
        self.circle(PAGE_W-MARGIN-17, PAGE_H-77, 17, LILAC)
        self.circle(PAGE_W-MARGIN-17, PAGE_H-77, 11, CORAL)
        self.circle(PAGE_W-MARGIN-17, PAGE_H-77, 4, GOLD)
        self.write(f"CAPÍTULO {number:02d}", size=8.5, leading=13, font="F2", color=CORAL, after=10)
        self.line(MARGIN, self.y, MARGIN+42, self.y, GOLD, 2.2)
        self.y -= 12
        self.write(title, size=21.5, leading=27, font="F4", color=PLUM, after=17)

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

    def table(self, rows: list[list[str]]) -> None:
        if not rows:
            return
        columns = max(len(row) for row in rows)
        width = PAGE_W - 2*MARGIN
        widths = [width * .28] + [width * .72 / (columns - 1)] * (columns - 1) if columns > 1 else [width]
        normalized = [row + [""] * (columns - len(row)) for row in rows]
        for ridx, row in enumerate(normalized):
            wrapped = []
            for col, cell in enumerate(row):
                value = _plain(cell)
                maxchars = max(8, int((widths[col] - 10) / 4.0))
                wrapped.append(textwrap.wrap(value, maxchars, break_long_words=True) or [""])
            row_height = max(1, max(map(len, wrapped))) * 10 + 8
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
                    self.draw_text(line_text, size=7.2, font=font, color=color, x=x+5,
                                   y=self.y-14-n*10)
                x += widths[col]
                if col < columns - 1:
                    self.line(x, bottom, x, self.y, LINE, .35)
            self.y = bottom
        self.y -= 8


def _stdlib_pdf(output: Path, layout: Layout) -> Path:
    objects: list[bytes | None] = [None] * 5
    def add(payload: bytes) -> int:
        objects.append(payload)
        return len(objects)
    def set_obj(number: int, payload: bytes) -> None:
        objects[number - 1] = payload

    page_numbers = []
    for page_index, ops in enumerate(layout.pages):
        if page_index > 0:
            yline = 32
            ops.extend([
                f"q {LINE[0]} {LINE[1]} {LINE[2]} RG .6 w {MARGIN} {yline+8} m {PAGE_W-MARGIN} {yline+8} l S Q",
                f"q {CORAL[0]} {CORAL[1]} {CORAL[2]} rg {MARGIN} {yline+6} 25 3 re f Q",
                f"BT /F1 7 Tf {MUTED[0]} {MUTED[1]} {MUTED[2]} rg 1 0 0 1 {MARGIN+32} {yline} Tm <{_pdf_text('GUIA PISTA - LANCAMENTO MUSICAL')}> Tj ET",
                f"q {LILAC[0]} {LILAC[1]} {LILAC[2]} rg {PAGE_W-MARGIN-29} {yline-2} 29 13 re f Q",
                f"BT /F2 7 Tf {PLUM[0]} {PLUM[1]} {PLUM[2]} rg 1 0 0 1 {PAGE_W-MARGIN-20} {yline+1} Tm <{_pdf_text(str(page_index))}> Tj ET",
            ])
            if page_index > 1:
                ops.insert(1, f"BT /F2 6.5 Tf {MUTED[0]} {MUTED[1]} {MUTED[2]} rg 1 0 0 1 {MARGIN} {PAGE_H-27} Tm <{_pdf_text('ARTISTA INDEPENDENTE  /  PISTA')}> Tj ET")
        stream = "\n".join(ops).encode("ascii")
        stream_no = add(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        page_no = add(b"")
        page_numbers.append((page_no, stream_no, page_index))
    set_obj(3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    set_obj(4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    set_obj(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")
    objects.extend([
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Bold /Encoding /WinAnsiEncoding >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Times-Roman /Encoding /WinAnsiEncoding >>",
    ])
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
        set_obj(page_no, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W:.2f} {PAGE_H:.2f}] /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R /F4 6 0 R /F5 7 0 R >> >> /Contents {stream_no} 0 R{annots_part} >>".encode("ascii"))
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
    return output


def compile_pdf(root: Path, output: Path) -> Path:
    chapters = sorted((root / "manuscript").glob("*.md"))
    if not chapters:
        raise ValueError("Nenhum capítulo Markdown encontrado em manuscript/.")
    layout = Layout()
    layout.write("GUIA DE LANÇAMENTO MUSICAL", size=8.5, leading=14, font="F2", color=CORAL, after=25)
    layout.circle(331, 375, 70, PLUM)
    layout.circle(331, 375, 54, CORAL, stroke=True, width=2.5)
    layout.circle(331, 375, 43, GOLD, stroke=True, width=1)
    layout.circle(331, 375, 29, PAPER_ALT, stroke=True, width=1)
    layout.circle(331, 375, 17, CORAL)
    layout.circle(331, 375, 6, GOLD)
    layout.write(TITLE, size=22.5, leading=29, font="F4", color=PLUM,
                 x=MARGIN, max_width=203, after=13)
    layout.rect(MARGIN, layout.y-2, 56, 3, GOLD)
    layout.y -= 20
    layout.write("Um passo possível de cada vez.", size=12, leading=18, color=TEAL, after=24)
    layout.write("PLANEJE  ·  APRESENTE  ·  APRENDA", size=7.5, leading=12, font="F2", color=MUTED)
    layout.y -= 12
    layout.line(MARGIN, layout.y, PAGE_W-MARGIN, layout.y, LINE, .8)
    layout.y -= 22
    layout.write("Projeto PISTA", size=9, color=MUTED)

    layout.new_page()
    layout.write("NESTE GUIA", size=8.5, leading=14, font="F2", color=CORAL, after=5)
    layout.write("Conteúdo", size=23, leading=29, font="F4", color=PLUM, after=16)
    for chapter_index, path in enumerate(chapters):
        title = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        layout.toc_item(chapter_index+1, title, chapter_index)

    for index, path in enumerate(chapters):
        layout.new_page()
        layout.destinations[f"chapter{index}"] = (len(layout.pages)-1, layout.y)
        content = parse_markdown(path.read_text(encoding="utf-8"))
        title = _plain(content[0]["text"]) if content and content[0]["type"] == "h" else path.stem
        layout.chapter_open(index+1, title)
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
                for item_index, item in enumerate(block["items"], 1):
                    prefix = f"{item_index}. " if kind == "ol" else "• "
                    layout.write(prefix + _plain(item), size=9.8, leading=15, color=INK,
                                 indent=8, after=2)
                layout.y -= 5
            elif kind == "table":
                layout.table(block["rows"])
            elif kind == "hr":
                layout.y -= 2; layout.line(MARGIN, layout.y, PAGE_W-MARGIN, layout.y, GOLD, .6); layout.y -= 10
    return _stdlib_pdf(output, layout)
