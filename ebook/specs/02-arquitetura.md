# Especificação da oficina Python

## Interfaces
- `pista index`: indexa fontes Markdown/TXT em `sources/` para recuperação lexical local.
- `pista search <consulta> [--top N]`: retorna trechos, arquivo, seção e pontuação.
- `pista check`: verifica ordem, estrutura, cobertura mínima e referências do manuscrito.
- `pista compile [--format epub|pdf|all]`: gera `build/pista.epub` e/ou `build/pista.pdf`; `all` é o padrão.

## Fluxo SDD
1. Atualizar spec e critérios de aceite.
2. Dividir a mudança em tarefas pequenas.
3. Recuperar evidências no RAG e redigir com Codex.
4. Conferir conteúdo, fontes e critérios com `pista check`.
5. Revisar visualmente EPUB/PDF e aprovar manualmente.

## Arquitetura
- `sources/`: fonte-base e documentação arquivada.
- `data/index.json`: índice regenerável; não é fonte da verdade.
- `manuscript/`: capítulos Markdown numerados e uma bibliografia final.
- `src/pista/`: recuperação, parsing e compiladores.
- `build/`: EPUB/PDF gerados e não versionados.

## Restrições
- Sem chamada de API LLM ou segredo obrigatório; Codex faz a redação.
- Execução local em Python 3.12 no Windows.
- PyMuPDF é obrigatório para compilar o PDF com acentos e gerar imagens reais das páginas. EPUB, busca e validação funcionam sem ele.
- Dependências de compilação são declaradas no `pyproject.toml` e instaladas no venv do projeto.
- Erros de cobertura ou referências inválidas bloqueiam a compilação; dependência ausente informa comando de instalação.
