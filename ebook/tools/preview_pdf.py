"""Rasterização aproximada do PDF local para inspeção visual offline.

Reconhece somente as operações emitidas por pista.pdf. A aparência final
deve ser conferida em um leitor PDF antes da publicação.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT, SCALE = 419.53, 595.28, 2
FONTS = {
    "F1": "arial.ttf",
    "F2": "arialbd.ttf",
    "F3": "ariali.ttf",
    "F4": "timesbd.ttf",
    "F5": "times.ttf",
}
NUMBER = r"-?\d+(?:\.\d+)?"
TEXT = re.compile(rf"BT /(F\d) ({NUMBER}) Tf ({NUMBER}) ({NUMBER}) ({NUMBER}) rg 1 0 0 1 ({NUMBER}) ({NUMBER}) Tm <([A-F0-9]+)> Tj ET")
RECT = re.compile(rf"q ({NUMBER}) ({NUMBER}) ({NUMBER}) rg ({NUMBER}) ({NUMBER}) ({NUMBER}) ({NUMBER}) re f Q")
LINE = re.compile(rf"q ({NUMBER}) ({NUMBER}) ({NUMBER}) RG ({NUMBER}) w ({NUMBER}) ({NUMBER}) m ({NUMBER}) ({NUMBER}) l S Q")


def color(values):
    return tuple(max(0, min(255, round(float(value) * 255))) for value in values)


def render_page(content: str) -> Image.Image:
    image = Image.new("RGB", (round(WIDTH*SCALE), round(HEIGHT*SCALE)), "white")
    draw = ImageDraw.Draw(image)
    for op in content.splitlines():
        match = TEXT.fullmatch(op)
        if match:
            face, size, r, g, b, x, y, data = match.groups()
            font = ImageFont.truetype(str(Path("C:/Windows/Fonts") / FONTS[face]), round(float(size)*SCALE))
            draw.text((float(x)*SCALE, (HEIGHT-float(y))*SCALE), bytes.fromhex(data).decode("cp1252"),
                      font=font, fill=color((r, g, b)), anchor="ls")
            continue
        match = RECT.fullmatch(op)
        if match:
            r, g, b, x, y, w, h = map(float, match.groups())
            draw.rectangle((x*SCALE, (HEIGHT-y-h)*SCALE, (x+w)*SCALE, (HEIGHT-y)*SCALE), fill=color((r, g, b)))
            continue
        match = LINE.fullmatch(op)
        if match:
            r, g, b, thick, x1, y1, x2, y2 = map(float, match.groups())
            draw.line((x1*SCALE, (HEIGHT-y1)*SCALE, x2*SCALE, (HEIGHT-y2)*SCALE), fill=color((r,g,b)), width=max(1,round(thick*SCALE)))
            continue
        if op.startswith("q ") and " c " in op and op.endswith((" f Q", " S Q")):
            nums = [float(v) for v in re.findall(NUMBER, op)]
            stroke = op.endswith(" S Q")
            offset = 4
            cx, cy = nums[offset+6], nums[offset+1]
            radius = nums[offset] - cx
            box = ((cx-radius)*SCALE, (HEIGHT-cy-radius)*SCALE,
                   (cx+radius)*SCALE, (HEIGHT-cy+radius)*SCALE)
            if stroke:
                draw.ellipse(box, outline=color(nums[:3]), width=max(1, round(nums[3]*SCALE)))
            else:
                draw.ellipse(box, fill=color(nums[:3]))
    return image


def main() -> None:
    source = Path(sys.argv[1])
    output = Path(sys.argv[2])
    output.mkdir(parents=True, exist_ok=True)
    for stale in output.glob("page-*.png"):
        stale.unlink()
    try:
        import pymupdf
    except ImportError:
        print("PyMuPDF indisponível: gerando prévia aproximada dos comandos vetoriais.")
    else:
        document = pymupdf.open(source)
        for index, page in enumerate(document, 1):
            path = output / f"page-{index:02}.png"
            page.get_pixmap(dpi=180, alpha=False).save(path)
            print(path)
        return
    streams = re.findall(rb"stream\n(.*?)\nendstream", source.read_bytes(), flags=re.S)
    for index, raw in enumerate(streams, 1):
        path = output / f"page-{index:02}.png"
        render_page(raw.decode("ascii")).save(path)
        print(path)


if __name__ == "__main__":
    main()
