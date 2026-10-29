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

# A fotografia acompanha o assunto de cada capítulo, sem repetir um motivo único.
CHAPTER_ART = (
    "studio-chapter.jpg",     # Começo: espaço de criação
    "roadmap-chapter.jpg",    # Base: decisões concretas
    "roadmap-chapter.jpg",    # Preparação: organizar a rota
    "recording-chapter.jpg",  # Conteúdo: apresentar a música
    "recording-chapter.jpg",  # Relações: criação compartilhada
    "recording-chapter.jpg",  # Estreia: música em circulação
    "review-chapter.jpg",     # Aprendizado: observar sinais
    "roadmap-chapter.jpg",    # Plano: anotar próximos passos
    "review-chapter.jpg",     # Referências: voltar às fontes
)


def rgb(token: str) -> tuple[float, float, float]:
    value = PALETTE[token].lstrip("#")
    return tuple(int(value[i:i+2], 16) / 255 for i in (0, 2, 4))
