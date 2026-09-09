# SISURB MCP Juiz de Fora — V9

V9 acrescenta ferramentas para análise de envelope M3A e comparação correta de limitantes.

## Novas ferramentas
- `consultar_envelope_m3a_jf`: separa TO de recuos/afastamentos e não inventa parâmetros pendentes.
- `comparar_limitantes_sisurb`: compara CA e TO×pavimentos como limites independentes; não multiplica CA×TO×pavimentos.

A V9 mantém o fluxo espacial da V8: lote → zoneamento → restrições.

### Regra de segurança
A V9 não transforma uma referência de Anexo 8 em regra legal definitiva sem confirmação. Recuos, afastamentos e altura permanecem PENDENTES quando não confirmados.

Fonte principal da legislação: Câmara Municipal de Juiz de Fora — Lei 6.910/1986 e alterações.
