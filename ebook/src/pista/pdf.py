"""PDF A5 enxuto, com backend local de biblioteca padrão para uso offline."""
from __future__ import annotations

import html
import re
import textwrap
from pathlib import Path

from .epub import TITLE
from .markdown import parse_markdown

PAGE_W, PAGE_H = 419.53, 595.28
MARGIN = 48.0
GREEN = (0.09, 0.23, 0.20)
MUTED = (0.35, 0.39, 0.36)
GOLD = (0.76, 0.55, 0.33)
LINE = (0.85, 0.87, 0.85)
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

    def ensure(self, height: float) -> None:
        if self.y - height < MARGIN:
            self.new_page()

    def raw(self, op: str) -> None:
        self.pages[-1].append(op)

    def rect(self, x: float, y: float, w: float, h: float, color: tuple[float, float, float], stroke=False) -> None:
        r, g, b = color
        self.raw(f"q {r:.3f} {g:.3f} {b:.3f} {'RG' if stroke else 'rg'} {x:.2f} {y:.2f} {w:.2f} {h:.2f} re {'S' if stroke else 'f'} Q")

    def line(self, x1: float, y1: float, x2: float, y2: float, color=LINE, thickness=.5) -> None:
        r, g, b = color
        self.raw(f"q {r:.3f} {g:.3f} {b:.3f} RG {thickness:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S Q")

    def draw_text(self, value: str, *, size=9.5, font="F1", color=(.15, .17, .16), x=MARGIN, y=None) -> None:
        if y is None:
            y = self.y
        r, g, b = color
        self.raw(f"BT /{font} {size:.2f} Tf {r:.3f} {g:.3f} {b:.3f} rg 1 0 0 1 {x:.2f} {y:.2f} Tm <{_pdf_text(value)}> Tj ET")

    def write(self, value: str, *, size=9.5, leading=14, font="F1", color=(.15, .17, .16), indent=0,
              max_width=None, link: str | None = None, after=4) -> None:
        text = value.replace("\n", " ").strip()
        if not text:
            self.y -= leading
            return
        width = max_width or (PAGE_W - 2*MARGIN - indent)
        chars = max(12, int(width / (size * (.55 if font == "F2" else .49))))
        wrapped = textwrap.wrap(text, width=chars, break_long_words=True, break_on_hyphens=False) or [""]
        for line_text in wrapped:
            self.ensure(leading)
            y = self.y - leading
            self.draw_text(line_text, size=size, font=font, color=color, x=MARGIN + indent, y=y)
            if link:
                approximate = min(width, max(16, len(line_text) * size * .48))
                self.links[-1].append((MARGIN + indent, y - 2, MARGIN + indent + approximate, y + leading - 2, link))
            self.y -= leading
        self.y -= after

    def paragraph(self, markup: str, *, quote=False) -> None:
        links = LINK_RE.findall(markup)
        visible = _plain(markup)
        if quote:
            self.ensure(34)
            self.rect(MARGIN, self.y - 26, 2.5, 26, GOLD)
        self.write(visible, indent=10 if quote else 0, color=GREEN if quote else (.15, .17, .16),
                   link=links[0][0] if links else None)
        self.y -= 3

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
            self.rect(MARGIN, bottom, width, row_height, GREEN if ridx == 0 else (1, 1, 1))
            self.line(MARGIN, bottom, MARGIN+width, bottom, LINE, .4)
            x = MARGIN
            for col, lines in enumerate(wrapped):
                color = (1, 1, 1) if ridx == 0 else (.15, .17, .16)
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
                f"q {LINE[0]} {LINE[1]} {LINE[2]} RG .5 w {MARGIN} {yline+7} m {PAGE_W-MARGIN} {yline+7} l S Q",
                f"BT /F1 7 Tf {MUTED[0]} {MUTED[1]} {MUTED[2]} rg 1 0 0 1 {MARGIN} {yline} Tm <{_pdf_text('PISTA - Artista Independente')}> Tj ET",
                f"BT /F1 7 Tf {MUTED[0]} {MUTED[1]} {MUTED[2]} rg 1 0 0 1 {PAGE_W-MARGIN-20} {yline} Tm <{_pdf_text(str(page_index))}> Tj ET",
            ])
        stream = "\n".join(ops).encode("ascii")
        stream_no = add(f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"\nendstream")
        page_no = add(b"")
        page_numbers.append((page_no, stream_no, page_index))
    set_obj(3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
    set_obj(4, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
    set_obj(5, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique /Encoding /WinAnsiEncoding >>")
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
        set_obj(page_no, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_W:.2f} {PAGE_H:.2f}] /Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> /Contents {stream_no} 0 R{annots_part} >>".encode("ascii"))
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
    layout.y -= 78
    layout.write("GUIA PRÁTICO", size=9, leading=15, font="F2", color=GOLD, after=20)
    layout.write(TITLE, size=23, leading=29, font="F2", color=GREEN, after=12)
    layout.rect(MARGIN, layout.y-2, 90, 2, GOLD)
    layout.y -= 20
    layout.write("Um passo possível de cada vez.", size=12, leading=18, color=MUTED, after=28)
    layout.write("Projeto PISTA", size=10, color=MUTED)

    layout.new_page()
    layout.write("Conteúdo", size=20, leading=27, font="F2", color=GREEN, after=14)
    for chapter_index, path in enumerate(chapters):
        title = path.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        line_y = layout.y - 14
        layout.write(title, size=10, leading=17, color=MUTED, after=1)
        layout.internal_links[-1].append((MARGIN, line_y-2, PAGE_W-MARGIN, line_y+12, chapter_index))

    for index, path in enumerate(chapters):
        layout.new_page()
        layout.destinations[f"chapter{index}"] = (len(layout.pages)-1, layout.y)
        for block in parse_markdown(path.read_text(encoding="utf-8")):
            kind = block["type"]
            if kind == "h":
                if block["level"] == 1:
                    layout.write(_plain(block["text"]), size=19, leading=24, font="F2", color=GREEN, after=12)
                elif block["level"] == 2:
                    layout.ensure(28); layout.y -= 4
                    layout.write(_plain(block["text"]), size=13, leading=17, font="F2", color=GREEN, after=5)
                else:
                    layout.write(_plain(block["text"]), size=11, leading=14, font="F2", color=GREEN, after=4)
            elif kind == "p":
                layout.paragraph(block["text"])
            elif kind == "quote":
                layout.paragraph(block["text"], quote=True)
            elif kind in ("ul", "ol"):
                for item_index, item in enumerate(block["items"], 1):
                    prefix = f"{item_index}. " if kind == "ol" else "• "
                    layout.write(prefix + _plain(item), indent=6, after=1)
                layout.y -= 4
            elif kind == "table":
                layout.table(block["rows"])
            elif kind == "hr":
                layout.y -= 2; layout.line(MARGIN, layout.y, PAGE_W-MARGIN, layout.y, GOLD, .6); layout.y -= 10
    return _stdlib_pdf(output, layout)
