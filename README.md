# SISURB MCP – Juiz de Fora – V7

V7 do conector MCP para análise de viabilidade urbanística em Juiz de Fora/MG.

## Novidades da V7
- Corrige e torna mais robusta a busca automática de lote por endereço.
- Faz fallback entre igualdade exata, LIKE e separação de rua/número.
- Recupera a geometria do lote quando disponível.
- Adiciona `consultar_restricoes_sisurb`, por interseção espacial do polígono do lote.
- Adiciona `consultar_restricoes_por_lote`, que automatiza localização + consulta espacial.
- Mantém a lógica do V6 para M3A/ZR2 (Corredor): CA 2,8 sem redução automática pela antiga regra de vagas.
- Mantém separação entre potencial teórico pelo CA e potencial edificável definitivo.

## Ferramentas
- `buscar_lote_sisurb(endereco)`
- `consultar_restricoes_sisurb(geometria_lote)`
- `consultar_restricoes_por_lote(endereco, id_lote, geocodigo)`
- `consultar_zoneamento_sisurb(nome_zona)`
- `consultar_legislacao_jf(zona, modelo, categoria_uso)`
- `consultar_regra_urbanistica_jf(zona, modelo, uso)`
- `avaliar_modelo_ocupacao_jf(zona, modelo, uso, area_lote_m2)`
- `calcular_potencial_preliminar(...)`
