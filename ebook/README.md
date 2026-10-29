# Oficina do ebook PISTA

Pipeline local, guiado por especificações, para transformar fontes em capítulos claros, auditáveis e publicáveis. Busca lexical, validação e EPUB usam a biblioteca padrão do Python. O PDF usa PyMuPDF para embutir fontes TrueType e preservar a acentuação; a revisão visual também usa PyMuPDF.

## Estrutura

- `specs/`: produto, editorial, arquitetura e tarefas SDD.
- `sources/`: fonte-base e documentação que alimentam o RAG.
- `editorial/`: brief, sumário e critérios de aceite executáveis.
- `manuscript/`: capítulos Markdown, um arquivo por capítulo.
- `src/pista/`: indexação, recuperação, validação e compilação.
- `data/`: índice regenerável; `build/`: artefatos gerados.

## Começar no Windows

```powershell
cd ebook
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
$env:PYTHONPATH = "src"
python -m pista.cli index
python -m pista.cli search "como coletar feedback"
python -m pista.cli check
python -m pista.cli compile --format all
```

Os arquivos ficam em `build/pista.epub` e `build/pista.pdf`.

## Ver páginas como imagens

Para inspecionar visualmente cada página real do PDF, instale PyMuPDF no mesmo Python usado para compilar o livro e gere PNGs:

```powershell
python -m pip install PyMuPDF
python tools/preview_pdf.py build/pista.pdf build/preview-real
```

O script usa PyMuPDF e renderiza cada página real a 180 DPI. Sem a biblioteca, ele para e informa o comando de instalação. Depois de gerar `build/preview-real/page-01.png` e as demais páginas, compare-as com o seu leitor; envie capturas se houver diferenças.

## Ciclo SDD de escrita

1. Atualize uma especificação e os critérios de aceite antes de mudar o livro ou o harness.
2. Divida a mudança em tarefas pequenas em `specs/03-tarefas.md`.
3. Indexe fontes e recupere passagens com `search`; anote arquivo e seção.
4. Redija com Codex no manuscrito. Diferencie fatos oficiais, relatos, recomendações e hipóteses.
5. Rode `check`, corrija os bloqueios e compile ambos formatos.
6. Revise visualmente e humanamente antes de publicar.

O índice lexical ajuda a localizar trechos; não verifica fatos nem substitui a leitura da fonte. Nenhuma chave de API é necessária.
