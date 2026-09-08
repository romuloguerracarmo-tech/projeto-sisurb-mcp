# SISURB MCP — Juiz de Fora

Servidor MCP remoto para o Claude consultar a camada de lotes do SISURB.

Ferramenta: `buscar_lote_sisurb(endereco)`

Exemplo: `Rua São Mateus, 490`

O servidor consulta a camada oficial:
SISURB/PJF — uso_cad_lotes / MapServer/158.

Depois de publicar em HTTPS, a URL do conector no Claude será:
`https://SEU-SERVICO.onrender.com/mcp`

Esta primeira versão consulta dados cadastrais/urbanísticos.
Recuos, restrições e regras específicas serão adicionados depois.
