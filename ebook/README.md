# Oficina do ebook PISTA

Pipeline local para transformar fontes em capítulos claros, auditáveis e publicáveis. O projeto começa sem dependências externas: Python padrão para indexação lexical e EPUB 3.

## Estrutura

- `sources/`: cópias e novas fontes que alimentam o RAG.
- `editorial/`: promessa, público, voz, limites de evidência e mapa do livro.
- `manuscript/`: capítulos em Markdown, um arquivo por capítulo.
- `src/pista/`: indexação, recuperação, checagem e compilação.
- `data/`: índice regenerável.
- `build/`: artefatos compilados.

## Começar

```powershell
cd ebook
python -m venv .venv
..venv\Scripts\Activate.ps1
python -m pip install -e .
pista index
pista search "como coletar feedback"
pista compile
```

Sem instalar o pacote, use `python -m pista.cli` com `PYTHONPATH=src`.

## Fluxo de escrita

1. Coloque fontes `.md` ou `.txt` em `sources/`.
2. Rode `pista index` para dividir por títulos e parágrafos e atualizar o índice local.
3. Rode `pista search "pergunta do capítulo" --top 6` e use as passagens com citação de arquivo/seção.
4. Escreva no capítulo em `manuscript/`. Preserve o que é regra documentada, relato, hipótese editorial ou exemplo ilustrativo.
5. Rode `pista check` para conferir estrutura e referências locais.
6. Rode `pista compile` para criar `build/pista.epub`.

O índice lexical ajuda a encontrar trechos; ele não valida fatos nem substitui leitura da fonte. Para adicionar embeddings/LLM no futuro, mantenha as interfaces `index`, `search` e `compile` estáveis e troque somente o backend de recuperação/geração. Nenhuma chave de API é necessária para o fluxo atual.
