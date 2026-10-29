# Revisão visual do PDF

Data: 28 out. 2026. Arquivo: `build/pista.pdf`, 34 páginas A5. Renderização real com PyMuPDF a 180 DPI em `build/preview-real/page-*.png`; folhas de contato criadas a partir desses PNGs.

## O que a inspeção mostrou e o que foi corrigido

- A primeira renderização real revelou caracteres acentuados ausentes em todo o PDF. O compilador agora embute fontes TrueType com PyMuPDF; texto extraído e imagens mostram `Faça`, `próximo`, `lançamento` e demais acentos corretamente.
- Duas páginas traziam apenas um parágrafo ou um cartão final. Os fechamentos repetidos foram cortados sem remover as instruções essenciais; a nova paginação não contém páginas internas com menos de 190 caracteres de texto, exceto a capa.
- O gráfico de cinco momentos começava sozinho na página seguinte. Ele foi compactado e agora acompanha a abertura do capítulo de preparação.
- Fotografias diferentes foram associadas a criação, planejamento, apresentação da música e revisão do lançamento. A capa e a rota de cinco movimentos também usam imagens fotográficas.
- A inspeção automática das caixas de texto não encontrou conteúdo fora da área visível das 34 páginas.

## Segunda passagem editorial

- A capa foi preservada. As aberturas internas agora usam fotografia em sangria e um painel de título sobreposto; cada parte recebe cor e identificação próprias.
- Os parágrafos passaram a usar Georgia. Seções ganharam números e linhas de orientação; as vinte ideias de conteúdo foram redesenhadas como cartões em duas colunas.
- Títulos de seção e cabeçalhos de tabela passaram a permanecer com o conteúdo seguinte. Fechamentos repetidos e blocos de fontes duplicados foram retirados do fluxo; as referências completas continuam no capítulo final.
- A nova inspeção de todas as 34 páginas não mostrou acentos perdidos, texto fora das margens ou páginas internas quase vazias. O sumário mantém nove links clicáveis.

## Limite da revisão

O EPUB é refluível: tamanho de fonte, tela e aplicativo mudam as quebras. Sua estrutura e imagens foram verificadas no pacote, mas a aparência precisa ser conferida em leitores EPUB reais antes da publicação.
