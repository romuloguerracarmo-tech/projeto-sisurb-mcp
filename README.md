# SISURB MCP Juiz de Fora — v4

MCP remoto para Claude com:
- buscar_lote_sisurb(endereco)
- consultar_zoneamento_sisurb(nome_zona)
- consultar_legislacao_jf(zona, modelo, categoria_uso)
- calcular_potencial_preliminar(...)

Endpoint esperado no Render:
https://SEU-SERVICO.onrender.com/mcp

A v4 mantém a busca de lote e acrescenta consulta do zoneamento vigente,
referência à Lei 6.910/1986 e cálculo preliminar. Valores legislativos não
confirmados ficam explicitamente como pendentes; o servidor não deve inventar
recuos ou envelope construtivo.
