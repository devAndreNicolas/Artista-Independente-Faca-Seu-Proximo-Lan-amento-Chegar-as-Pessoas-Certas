"""Tokens visuais compartilhados pelos compiladores EPUB e PDF."""

PALETTE = {
    "paper": "#FBF5EB",
    "paper_alt": "#F4EDE7",
    "plum": "#2D1C37",
    "coral": "#EC6856",
    "gold": "#E7B858",
    "teal": "#267064",
    "ink": "#302B35",
    "muted": "#6B616B",
    "lilac": "#EFE6F1",
    "line": "#D7CCD7",
}


def rgb(token: str) -> tuple[float, float, float]:
    value = PALETTE[token].lstrip("#")
    return tuple(int(value[i:i+2], 16) / 255 for i in (0, 2, 4))
