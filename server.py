
import os
import re
import unicodedata
import requests
from mcp.server import MCPServer

mcp = MCPServer("SISURB Juiz de Fora")

LOTES_URL = (
    "https://sisurb.pjf.mg.gov.br/server/rest/services/"
    "uso_cad_lotes/MapServer/158/query"
)

ZONEAMENTO_URL = (
    "https://sisurb.pjf.mg.gov.br/server/rest/services/"
    "uso_zon_zoneamento_urbano_pjf/MapServer/167/query"
)

# Lei 6.910/1986, com alterações posteriores.
# A matriz abaixo reproduz somente informações que conseguimos confirmar
# na legislação consolidada consultada. Campos não confirmados ficam nulos.
LEGISLACAO_URL = (
    "https://www.camarajf.mg.gov.br/sal/norma.php?"
    "njc=&njn=06910&njt=LEI"
)

MODEL_RULES = {
    "M1": {
        "area_minima_m2": None, "testada_minima_m": None,
        "ca_max": 1.0, "taxa_ocupacao": "65%",
        "recuo_frontal_m": 3.0,
        "afastamento_lateral_fundos": "não informado na matriz desta ferramenta"
    },
    "M1A": {
        "area_minima_m2": None, "testada_minima_m": None,
        "ca_max": 1.0,
        "taxa_ocupacao": "1º ao 3º pavimento = 100% até 9,20 m; demais = 65%",
        "recuo_frontal_m": 2.0,
        "afastamento_lateral_fundos": "não informado na matriz desta ferramenta"
    },
    "M2": {
        "area_minima_m2": 300.0, "testada_minima_m": None,
        "ca_max": 1.3, "ca_max_com_vagas": 1.7,
        "taxa_ocupacao": "65%",
        "recuo_frontal_m": None,
        "afastamento_lateral_fundos": "lote > 300 m²: uma divisa = 0; demais = 1,5 m"
    },
    "M2A": {
        "area_minima_m2": 300.0, "testada_minima_m": None,
        "ca_max": 1.65, "ca_max_com_vagas": 2.1,
        "taxa_ocupacao": "1º ao 3º pavimento = 100% até 9,20 m; demais = 65%",
        "recuo_frontal_m": None,
        "afastamento_lateral_fundos": "1º ao 3º pavimento = 0; demais: uma divisa = 0; demais = 1,5 m"
    },
    "M3": {
        "area_minima_m2": 300.0, "testada_minima_m": 10.0,
        "ca_max": 1.8, "ca_max_com_vagas": 2.4,
        "taxa_ocupacao": "65%",
        "recuo_frontal_m": 3.0,
        "afastamento_lateral_fundos": "não informado na matriz desta ferramenta"
    },
    "M3A": {
        "area_minima_m2": 360.0, "testada_minima_m": 10.0,
        "ca_max": 2.2, "ca_max_com_vagas": 2.8,
        "taxa_ocupacao": "consultar condição específica no Anexo 8; não inferir automaticamente",
        "recuo_frontal_m": None,
        "afastamento_lateral_fundos": "consultar condição específica no Anexo 8; não inferir automaticamente"
    },
    "M4": {
        "area_minima_m2": 360.0, "testada_minima_m": 10.0,
        "ca_max": 2.5, "ca_max_com_vagas": 2.8,
        "taxa_ocupacao": "50%",
        "recuo_frontal_m": 3.0,
        "afastamento_lateral_fundos": "testada < 12 m: uma divisa = 0; demais = 1,5 m; testada > 12 m = 1,5 m"
    },
    "M4A": {
        "area_minima_m2": 360.0, "testada_minima_m": 10.0,
        "ca_max": 3.0,
        "taxa_ocupacao": "1º ao 3º pavimento = 100% até 9,20 m; demais = 50%",
        "recuo_frontal_m": None,
        "afastamento_lateral_fundos": "1º ao 3º pavimento = 0; demais conforme testada"
    },
    "M5": {
        "area_minima_m2": 450.0, "testada_minima_m": 12.0,
        "ca_max": 3.0, "taxa_ocupacao": None,
        "recuo_frontal_m": 3.0,
        "afastamento_lateral_fundos": "2,0 m"
    },
    "M5A": {
        "area_minima_m2": 450.0, "testada_minima_m": 12.0,
        "ca_max": 3.5, "taxa_ocupacao": None,
        "recuo_frontal_m": None,
        "afastamento_lateral_fundos": "1º ao 3º pavimento = 0; demais = 2,0 m"
    },
    "M6A": {
        "area_minima_m2": 550.0, "testada_minima_m": 12.0,
        "ca_max": 4.5,
        "taxa_ocupacao": "1º ao 4º pavimento = 100% até 12,00 m; demais = 50%",
        "recuo_frontal_m": None,
        "afastamento_lateral_fundos": "1º ao 4º pavimento = 0; demais = 2,0 m"
    },
    "M7A": {
        "area_minima_m2": 700.0, "testada_minima_m": 15.0,
        "ca_max": 5.5,
        "taxa_ocupacao": None,
        "recuo_frontal_m": None,
        "afastamento_lateral_fundos": "1º ao 4º pavimento = 0; demais conforme Anexo 8"
    },
    "M8A": {
        "area_minima_m2": 1200.0, "testada_minima_m": 18.0,
        "ca_max": 6.5,
        "taxa_ocupacao": None,
        "recuo_frontal_m": None,
        "afastamento_lateral_fundos": "1º ao 4º pavimento = 0; demais = 2,4 m"
    },
}

def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"\s+", " ", s).strip().upper()
    return s

def arcgis_query(url, where, out_fields, return_geometry=False):
    params = {
        "where": where,
        "outFields": out_fields,
        "returnGeometry": "true" if return_geometry else "false",
        "f": "json",
    }
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(str(data["error"]))
    return data

@mcp.tool()
def buscar_lote_sisurb(endereco: str) -> dict:
    """Busca automaticamente o lote cadastral/urbanístico do SISURB pelo endereço."""
    if not endereco or not endereco.strip():
        return {"ok": False, "erro": "Informe um endereço."}

    q = norm(endereco).replace("'", "''")
    fields = (
        "OBJECTID,geocodigo,id_lote,id_lote_pjf,id_lote_2,jftech_codigo_lote,"
        "endereco,area_construida_est_m2,area_maior_edificacao,"
        "area_min_lote_perm_m2,area_projecao_edif_est_m2,area_remanescente_est_m2,"
        "coefic_aprov_pratic_est,coefic_aproveitamento_perm_gera,"
        "gabarito,modelo_parcelamento_geral,modelo_ocupacao_geral,"
        "qtde_inscricoes,qtde_unid_edificadas,qtde_pavimentos,"
        "taxa_ocupacao_praticada_est,taxa_ocupacao_perm_geral,"
        "taxa_permeab_praticada_est,taxa_impermeabilidade_perm_gera,"
        "tipo_lote,tipo_uso,utilizacao,unidades_planejamento,zoneamento,"
        "fonte,ano,area_geometria"
    )

    # Tentativa principal: endereço completo.
    where = f"UPPER(endereco) LIKE '%{q}%'"
    data = arcgis_query(LOTES_URL, where, fields)

    # Fallback: separa número do nome da via.
    if not data.get("features"):
        m = re.match(r"^(.*?)[,\s]+(\d+[A-Z]?)$", endereco.strip(), re.I)
        if m:
            rua = norm(m.group(1)).replace("'", "''")
            numero = m.group(2).replace("'", "''")
            where = (
                f"UPPER(endereco) LIKE '%{rua}%' "
                f"AND UPPER(endereco) LIKE '%{numero}%'"
            )
            data = arcgis_query(LOTES_URL, where, fields)

    feats = data.get("features", [])
    if not feats:
        return {
            "ok": False,
            "erro": "Nenhum lote encontrado no SISURB para o endereço informado.",
            "fonte": LOTES_URL,
        }

    resultados = [f.get("attributes", {}) for f in feats[:10]]
    return {
        "ok": True,
        "quantidade_resultados": len(resultados),
        "resultados": resultados,
        "fonte": LOTES_URL,
        "observacao": (
            "Dados cadastrais/urbanísticos do SISURB. "
            "Campos estimados devem permanecer identificados como estimados."
        ),
    }

@mcp.tool()
def consultar_zoneamento_sisurb(nome_zona: str) -> dict:
    """Consulta os parâmetros atuais da camada oficial de zoneamento do SISURB."""
    if not nome_zona.strip():
        return {"ok": False, "erro": "Informe o nome do zoneamento."}

    z = norm(nome_zona).replace("'", "''")
    fields = (
        "OBJECTID,nome,sigla,coef_aprov_perm_geral,taxa_ocup_perm_geral,"
        "taxa_impermeab_perm_geral,modelo_parcelamento_geral,area_minima_lote,"
        "coef_aprov_perm_res,coef_aprov_perm_com,coef_aprov_perm_inst,"
        "coef_aprov_perm_ind,modelo_ocupacao_geral,observacao,fonte,ano,"
        "geocodigo,legislacao_incidente,geocodigo_unificados,comentario_dado,"
        "tx_ocupacao_art36,area_geometria"
    )
    where = f"UPPER(nome) = '{z}'"
    data = arcgis_query(ZONEAMENTO_URL, where, fields)

    feats = data.get("features", [])
    if not feats:
        where = f"UPPER(nome) LIKE '%{z}%'"
        data = arcgis_query(ZONEAMENTO_URL, where, fields)
        feats = data.get("features", [])

    return {
        "ok": bool(feats),
        "quantidade_resultados": len(feats),
        "resultados": [f.get("attributes", {}) for f in feats[:10]],
        "fonte": ZONEAMENTO_URL,
        "observacao": (
            "Esta consulta serve para confirmar o modelo de ocupação e a "
            "legislação incidente. Não substitui a leitura da legislação."
        ),
    }

@mcp.tool()
def consultar_legislacao_jf(zona: str, modelo: str = "", categoria_uso: str = "residencial_unifamiliar") -> dict:
    """Retorna regras legislativas confirmadas e indica o que ainda exige leitura do Anexo 8."""
    z = norm(zona)
    m = norm(modelo).replace(" ", "")
    resultado = {
        "ok": True,
        "lei_base": "Lei nº 6.910/1986 — Uso e Ocupação do Solo",
        "fonte_oficial": LEGISLACAO_URL,
        "categoria_uso": categoria_uso,
        "zona_consultada": zona,
        "modelo_consultado": modelo or None,
        "regras_confirmadas": [],
        "pendencias": [],
    }

    # Tabela B do Anexo 6: ZR2 zona/corredor para residencial unifamiliar.
    if z == "ZONA RESIDENCIAL 2 (CORREDOR)" or z == "ZONA RESIDENCIAL 2 CORREDOR":
        resultado["regras_confirmadas"].append(
            "Para uso residencial unifamiliar em ZR2 (Corredor), a Tabela B "
            "do Anexo 6 admite modelos até M3A."
        )
        if m:
            if m == "M3A":
                resultado["modelo"] = MODEL_RULES["M3A"]
                resultado["regras_confirmadas"].append(
                    "Para M3A, o Anexo 8 registra CA máximo de 2,2, "
                    "com possibilidade de 2,8(*) quando atendidas as condições "
                    "associadas aos coeficientes marcados com asterisco."
                )
                resultado["pendencias"].append(
                    "Para fechar o envelope do M3A, conferir diretamente o Anexo 8 "
                    "e as condições específicas de afastamento/taxa de ocupação; "
                    "esta ferramenta deliberadamente não infere valores ausentes."
                )
            elif m in MODEL_RULES:
                resultado["modelo"] = MODEL_RULES[m]
            else:
                resultado["pendencias"].append(
                    f"Modelo {modelo} não está cadastrado na matriz desta ferramenta."
                )
        else:
            resultado["pendencias"].append(
                "Informe o modelo de ocupação para detalhar as regras do Anexo 8."
            )
    else:
        resultado["pendencias"].append(
            "Zona diferente de ZR2 (Corredor): confirmar a Tabela B do Anexo 6 "
            "e eventual legislação específica incidente."
        )

    resultado["pendencias"].append(
        "A Lei Complementar nº 243/2024 alterou o Anexo 8 em matéria específica de uso institucional/hospitais; essa alteração não deve ser extrapolada para M3A residencial sem verificar o texto vigente. ""A legislação municipal possui alterações posteriores; a análise definitiva "
        "deve considerar a legislação vigente e eventuais leis específicas do trecho/via."
    )
    return resultado

@mcp.tool()
def calcular_potencial_preliminar(area_lote_m2: float, ca: float, taxa_ocupacao_pct: float, pavimentos: int, area_existente_m2: float = 0.0) -> dict:
    """Calcula apenas os limites matemáticos preliminares, sem afirmar envelope real."""
    ca_area = area_lote_m2 * ca
    implantacao = area_lote_m2 * taxa_ocupacao_pct / 100.0
    pav_area = implantacao * pavimentos
    potencial = min(ca_area, pav_area)
    return {
        "area_lote_m2": area_lote_m2,
        "potencial_pelo_ca_m2": round(ca_area, 2),
        "implantacao_teorica_por_to_m2": round(implantacao, 2),
        "potencial_teorico_por_pavimentos_m2": round(pav_area, 2),
        "limitante_entre_ca_e_pavimentos": (
            "CA" if ca_area < pav_area else
            "PAVIMENTOS/TO" if pav_area < ca_area else "EMPATE"
        ),
        "potencial_teorico_preliminar_m2": round(potencial, 2),
        "potencial_adicional_teorico_m2": round(max(0.0, potencial - area_existente_m2), 2),
        "aviso": (
            "Não representa potencial edificável definitivo: recuos, afastamentos, "
            "altura, vagas, restrições espaciais e demais regras ainda devem ser verificados."
        ),
    }



@mcp.tool()
def consultar_regra_urbanistica_jf(zona: str, modelo: str, uso: str = "não informado") -> dict:
    """Consulta regras estruturadas para zona/modelo sem inventar parâmetros."""
    z = norm(zona)
    m = norm(modelo).replace(" ", "")
    result = {
        "ok": False, "zona": zona, "modelo": modelo, "uso_informado": uso,
        "status": "PENDENTE",
        "fontes": [
            "https://www.camarajf.mg.gov.br/sal/norma.php?njc=&njn=06910&njt=LEI",
            "https://www.camarajf.mg.gov.br/sal/norma.php?njc=&njn=054&njt=LEICO&t=0",
            "https://www.camarajf.mg.gov.br/sal/norma.php?njc=&njn=06909&njt=LEI",
        ],
        "regras": [], "observacoes": [], "pendencias": []
    }
    if "ZONA RESIDENCIAL 2" in z and "CORREDOR" in z and m == "M3A":
        result["ok"] = True
        result["status"] = "PARCIALMENTE CONFIRMADO"
        result["regras"] = [
            {"parametro":"modelo","valor":"M3A","status":"CONFIRMADO"},
            {"parametro":"ca_maximo_do_modelo","valor":2.8,"status":"CONFIRMADO",
             "fonte":"Anexo 8 da Lei 6.910/1986; referências oficiais da Câmara; SISURB"},
            {"parametro":"lote_minimo_m2","valor":360.0,"status":"CONFIRMADO"},
            {"parametro":"testada_minima_m","valor":10.0,"status":"CONFIRMADO"},
        ]
        result["observacoes"] = [
            "A LC 54/2016, art. 2º, cancelou a última observação relativa a vagas que figurava no Anexo 8.",
            "Esta versão NÃO condiciona automaticamente o CA 2,8 do M3A à antiga tabela de vagas.",
            "Vagas continuam sendo dimensionadas separadamente pela LC 54/2016.",
            "Para uso misto, considerar os arts. 32 e 33 da Lei 6.910/1986."
        ]
        result["pendencias"] = [
            "Confirmar recuos/afastamentos específicos do M3A no Anexo 8 vigente.",
            "Confirmar altura/gabarito como regra legal, sem confundir com campo cadastral.",
            "Consultar espacialmente a camada de restrições do SISURB."
        ]
    return result

@mcp.tool()
def avaliar_modelo_ocupacao_jf(zona: str, modelo: str, uso: str = "não informado", area_lote_m2: float = 0.0) -> dict:
    """Avalia M3A sem reduzir automaticamente o CA 2,8 por regra antiga de vagas."""
    regra = consultar_regra_urbanistica_jf(zona, modelo, uso)
    if not regra.get("ok"):
        return regra
    out = {
        "ok": True, "status": regra["status"], "zona": zona, "modelo": modelo,
        "uso": uso, "ca_aplicavel_preliminar": 2.8,
        "ca_status": "CONFIRMADO COMO LIMITE DO MODELO, SUJEITO À APLICABILIDADE DO USO",
        "fontes": regra["fontes"], "observacoes": regra["observacoes"],
        "pendencias": regra["pendencias"],
        "vagas": {"status":"CALCULAR SEPARADAMENTE", "fonte":"Lei Complementar nº 54/2016",
                  "observacao":"Não reduzir automaticamente o CA 2,8 por esta regra de vagas."}
    }
    if area_lote_m2 > 0:
        out["potencial_pelo_ca_m2"] = round(area_lote_m2 * 2.8, 2)
    return out

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "10000")),
        stateless_http=True,
        json_response=True,
    )
