# SISURB Juiz de Fora — V12

MCP para análise preliminar de viabilidade urbanística a partir das camadas oficiais do SISURB/PJF.

## Correções da V12

- `gabarito` do cadastro SISURB é normalizado como `gabarito_cadastral_sisurb`.
- Nunca converter automaticamente `gabarito_cadastral_sisurb` em número de pavimentos.
- `pavimentos_legais_confirmados` permanece nulo até confirmação normativa externa.
- Não calcular TO × pavimentos nem declarar fator limitante global enquanto faltarem pavimentos legais, recuos/envelope ou efeito normativo das restrições.
- A consulta de restrições usa estratégia em duas etapas: primeiro atributos das feições intersectantes; depois recupera apenas as geometrias dessas feições. Isso reduz timeouts do SISURB.
- Quando as geometrias das restrições estão disponíveis, calcula área total intersectada, percentual do lote e área não atingida, sem dupla contagem de sobreposições.
- Se o servidor da Prefeitura estiver indisponível, o resultado fica PENDENTE e não inventa a restrição.
- O MCP sinaliza explicitamente que o relatório final não deve conter SVG, código, markup ou duplicações.

## Fontes oficiais principais

- Lotes urbanísticos: https://sisurb.pjf.mg.gov.br/server/rest/services/uso_cad_lotes/MapServer/158/query
- Zoneamento: https://sisurb.pjf.mg.gov.br/server/rest/services/uso_zon_zoneamento_urbano_pjf/MapServer/167/query
- Áreas de restrição: https://sisurb.pjf.mg.gov.br/server/rest/services/SISURB_peus/anl_areas_restricao_P6/MapServer/0/query
- Lei 6.910/1986: https://www.camarajf.mg.gov.br/sal/norma.php?njc=&njn=06910&njt=LEI

## Teste recomendado

Após deploy, no Claude digitar apenas:

`Rua São Mateus, 490`

Esperado: gabarito cadastral separado de pavimentos legais; potencial por pavimentos PENDENTE; fator limitante global PENDENTE; e, se o SISURB responder, área/percentual de restrição calculados.
