import os
import re
import json
import unicodedata
from urllib.parse import urlencode
from urllib.request import urlopen, Request

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("SISURB Juiz de Fora")

SISURB_LAYER = (
    "https://sisurb.pjf.mg.gov.br/server/rest/services/"
    "uso_cad_lotes/MapServer/158/query"
)

OUTPUT_FIELDS = [
    "OBJECTID", "geocodigo", "id_lote", "id_lote_pjf", "id_lote_2",
    "jftech_codigo_lote", "endereco", "area_construida_est_m2",
    "area_maior_edificacao", "area_min_lote_perm_m2",
    "area_projecao_edif_est_m2", "area_remanescente_est_m2",
    "coefic_aprov_pratic_est", "coefic_aproveitamento_perm_gera",
    "gabarito", "modelo_parcelamento_geral", "qtde_inscricoes",
    "qtde_unid_edificadas", "qtde_pavimentos",
    "taxa_ocupacao_praticada_est", "taxa_ocupacao_perm_geral",
    "taxa_permeab_praticada_est", "taxa_impermeabilidade_perm_gera",
    "tipo_lote", "tipo_uso", "utilizacao", "unidades_planejamento",
    "zoneamento", "fonte", "ano", "area_geometria", "qtde_matriculas",
]

def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", text).strip().upper()

def arcgis_query(where: str, limit: int = 20):
    params = {
        "where": where,
        "outFields": ",".join(OUTPUT_FIELDS),
        "returnGeometry": "false",
        "resultRecordCount": str(limit),
        "f": "json",
    }
    url = SISURB_LAYER + "?" + urlencode(params)
    req = Request(url, headers={"User-Agent": "SISURB-MCP/1.0"})
    with urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))

    if "error" in data:
        raise RuntimeError(str(data["error"]))

    return [item.get("attributes", {}) for item in data.get("features", [])]

@mcp.tool()
def buscar_lote_sisurb(endereco: str) -> dict:
    """
    Consulta um endereço no cadastro urbanístico do SISURB de Juiz de Fora.
    Retorna dados cadastrais e urbanísticos do(s) lote(s) encontrado(s).
    """
    if not endereco or len(endereco.strip()) < 4:
        return {
            "sucesso": False,
            "erro": "Informe um endereço suficientemente completo."
        }

    normalized = normalize(endereco)
    safe = normalized.replace("'", "''")

    # Busca pelo texto completo.
    records = arcgis_query(f"UPPER(endereco) LIKE '%{safe}%'")

    # Segunda tentativa: separa logradouro e número.
    if not records:
        match = re.search(r"(.+?)[,\s]+(\d+)\s*$", normalized)
        if match:
            street = match.group(1).strip().replace("'", "''")
            number = match.group(2)
            records = arcgis_query(
                f"UPPER(endereco) LIKE '%{street}%' "
                f"AND endereco LIKE '%{number}%'"
            )

    if not records:
        return {
            "sucesso": False,
            "endereco_pesquisado": endereco,
            "fonte_oficial": "SISURB / Prefeitura de Juiz de Fora",
            "erro": "Nenhum lote encontrado no cadastro do SISURB para o endereço informado."
        }

    target = normalize(endereco)
    records.sort(
        key=lambda r: (
            normalize(str(r.get("endereco", ""))) == target,
            normalize(str(r.get("endereco", ""))).startswith(target),
        ),
        reverse=True,
    )

    return {
        "sucesso": True,
        "endereco_pesquisado": endereco,
        "quantidade_encontrada": len(records),
        "fonte_oficial": "SISURB / Prefeitura de Juiz de Fora",
        "camada_consultada": SISURB_LAYER,
        "lotes": records[:20],
        "observacao": (
            "Resultado cadastral/urbanístico da camada consultada. "
            "Recuos, restrições e interpretação da legislação municipal "
            "serão tratados em etapas próprias."
        ),
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=port,
        stateless_http=True,
        json_response=True,
    )
