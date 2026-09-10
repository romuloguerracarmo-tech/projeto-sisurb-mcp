# SISURB Juiz de Fora — V14

Versão V14 do MCP para consulta e análise preliminar de viabilidade urbanística.

## Correções principais

- Atualiza a regra do M3A para a referência do Anexo 8 oficial consultada:
  - 100% no 1º e 2º pavimentos até 8,90 m;
  - 60% nos demais pavimentos.
- Registra CA base do M3A = 2,2 e CA 2,8 como **condicionado/marcado com asterisco**, sem tratá-lo como CA básico irrestrito.
- Registra recuo frontal de 0 m no 2º pavimento e 2,0 m nos demais, conforme a leitura consultada do Anexo 8.
- Mantém o gabarito cadastral SISURB separado do número de pavimentos legais; nunca usa `gabarito=3` para multiplicar área.
- Mantém o fator limitante global como PENDENTE quando faltarem condições necessárias.
- Mantém a consulta espacial de restrições como etapa independente, sem inventar resultado em caso de erro do serviço.
- Proíbe geração de SVG, HTML, código ou relatórios duplicados na saída interpretável do MCP.

## Fontes oficiais

- Lei 6.910/1986: https://www.camarajf.mg.gov.br/sal/norma.php?njc=&njn=06910&njt=LEI
- Anexo 8: https://www.camarajf.mg.gov.br/sal/anexo.php?cod=55&t=nj
- LC 54/2016: https://www.camarajf.mg.gov.br/sal/norma.php?njc=&njn=054&njt=LEICO&t=0
- SISURB zoneamento: https://sisurb.pjf.mg.gov.br/server/rest/services/uso_zon_zoneamento_urbano_pjf/MapServer/167
- SISURB restrições: https://sisurb.pjf.mg.gov.br/server/rest/services/SISURB_peus/anl_areas_restricao_P6/MapServer/0

## Observação

A V14 não declara potencial construtivo definitivo. O CA 2,8 é tratado como condicionado enquanto a condição associada ao asterisco não for explicitamente resolvida para o caso concreto. A análise geométrica do envelope depende de testada/profundidade e da definição completa das divisas/regras aplicáveis.
