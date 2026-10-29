# Oficina do ebook PISTA

Pipeline local, guiado por especificações, para transformar fontes em capítulos claros, auditáveis e publicáveis. Busca lexical, validação e compilação EPUB/PDF funcionam com a biblioteca padrão do Python, inclusive sem rede.

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
$env:PYTHONPATH = "src"
python -m pista.cli index
python -m pista.cli search "como coletar feedback"
python -m pista.cli check
python -m pista.cli compile --format all
```

Os arquivos ficam em `build/pista.epub` e `build/pista.pdf`. Se a rede estiver disponível, instale o projeto com `python -m pip install -e .` para usar o comando `pista`.

## Ver páginas como imagens

Para inspecionar o PDF real, instale o extra de prévia e gere PNGs:

```powershell
python -m pip install PyMuPDF
python tools/preview_pdf.py build/pista.pdf build/preview
```

O script usa PyMuPDF e renderiza cada página a 180 DPI. Se ele não estiver instalado, gera uma prévia aproximada dos comandos vetoriais do nosso PDF e avisa isso no terminal. A prévia aproximada ajuda a encontrar falhas de paginação, mas a inspeção final deve usar os PNGs produzidos pelo PyMuPDF ou um leitor PDF.

## Ciclo SDD de escrita

1. Atualize uma especificação e os critérios de aceite antes de mudar o livro ou o harness.
2. Divida a mudança em tarefas pequenas em `specs/03-tarefas.md`.
3. Indexe fontes e recupere passagens com `search`; anote arquivo e seção.
4. Redija com Codex no manuscrito. Diferencie fatos oficiais, relatos, recomendações e hipóteses.
5. Rode `check`, corrija os bloqueios e compile ambos formatos.
6. Revise visualmente e humanamente antes de publicar.

O índice lexical ajuda a localizar trechos; não verifica fatos nem substitui a leitura da fonte. Nenhuma chave de API é necessária.
