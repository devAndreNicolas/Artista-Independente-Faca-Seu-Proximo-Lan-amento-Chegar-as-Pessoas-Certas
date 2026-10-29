"""Cria folhas de contato a partir das páginas reais rasterizadas do PDF."""
from pathlib import Path
from PIL import Image, ImageDraw


source = Path(__file__).resolve().parents[1] / "build" / "preview-real"
pages = sorted(source.glob("page-*.png"))
for start in range(0, len(pages), 10):
    sheet = Image.new("RGB", (1600, 920), "#dedede")
    draw = ImageDraw.Draw(sheet)
    for index, path in enumerate(pages[start:start+10]):
        x = (index % 5) * 320
        y = (index // 5) * 460
        with Image.open(path) as page:
            sheet.paste(page.convert("RGB").resize((300, 425)), (x, y))
        draw.text((x+4, y+430), path.stem, fill="#222222")
    output = source / f"sheet-{start//10+1:02}.jpg"
    sheet.save(output, quality=88)
    print(output)
