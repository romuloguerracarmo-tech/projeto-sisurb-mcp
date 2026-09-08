
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

RESTRICOES_URL = (
    "https://sisurb.pjf.mg.gov.br/server/rest/services/"
    "SISURB_peus/anl_areas_restricao_P6/MapServer/0/query"
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

def arcgis_query(url, where, out_fields, return_geometry=False, geometry=None,
                 geometry_type=None, spatial_rel=None, in_sr=None, out_sr=None, timeout=45):
    params = {
        "where": where,
        "outFields": out_fields,
        "returnGeometry": "true" if return_geometry else "false",
        "f": "json",
    }
    if geometry is not None:
        params["geometry"] = geometry if isinstance(geometry, str) else __import__("json").dumps(geometry, separators=(",", ":"))
    if geometry_type:
        params["geometryType"] = geometry_type
    if spatial_rel:
        params["spatialRel"] = spatial_rel
    if in_sr:
        params["inSR"] = str(in_sr)
    if out_sr:
        params["outSR"] = str(out_sr)
    r = requests.get(url, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(str(data["error"]))
    return data

@mcp.tool()
def buscar_lote_sisurb(endereco: str) -> dict:
    """Busca o lote no SISURB por endereço e, quando possível, retorna sua geometria para análises espaciais."""
    if not endereco or not endereco.strip():
        return {"ok": False, "erro": "Informe um endereço."}

    q = norm(endereco).replace("'", "''")
    # Use outFields=* here. Earlier versions listed fields that are not present
    # in every SISURB publication (notably modelo_ocupacao_geral), which caused
    # ArcGIS HTTP 400 errors even when the address itself was valid.
    fields = "*"

    queries = []
    # 1) igualdade exata normalizada para evitar consultas LIKE excessivamente amplas.
    queries.append(f"UPPER(endereco) = '{q}'")
    # 2) endereço completo contido.
    queries.append(f"UPPER(endereco) LIKE '%{q}%'")

    # 3) fallback: separa número e nome da via.
    m = re.match(r"^(.*?)[,\s]+(\d+[A-Z]?)$", endereco.strip(), re.I)
    if m:
        rua = norm(m.group(1)).replace("'", "''")
        numero = m.group(2).replace("'", "''")
        queries.append(
            f"UPPER(endereco) LIKE '%{rua}%' AND UPPER(endereco) LIKE '%{numero}%'"
        )

    feats = []
    last_error = None
    for where in queries:
        try:
            data = arcgis_query(LOTES_URL, where, fields, timeout=45)
            feats = data.get("features", [])
            if feats:
                break
        except Exception as exc:
            last_error = str(exc)

    if not feats:
        return {
            "ok": False,
            "erro": "Nenhum lote encontrado no SISURB para o endereço informado.",
            "detalhe_tecnico": last_error,
            "fonte": LOTES_URL,
        }

    resultados = [f.get("attributes", {}) for f in feats[:10]]
    # Recupera a geometria somente dos resultados encontrados, em chamadas individuais.
    # Isso reduz o risco de timeout e permite que a consulta de restrições use o polígono real.
    geometria = []
    for f in feats[:10]:
        attrs = f.get("attributes", {})
        oid = attrs.get("OBJECTID")
        if oid is None:
            continue
        try:
            gd = arcgis_query(
                LOTES_URL,
                f"OBJECTID = {int(oid)}",
                "*",
                return_geometry=True,
                out_sr=31983,
                timeout=45,
            )
            gf = gd.get("features", [])
            if gf and gf[0].get("geometry"):
                geometria.append({
                    "OBJECTID": oid,
                    "geocodigo": attrs.get("geocodigo"),
                    "id_lote": attrs.get("id_lote"),
                    "geometry": gf[0]["geometry"],
                    "spatial_reference": gf[0]["geometry"].get("spatialReference", {"wkid":31983}),
                })
        except Exception:
            # A falha na geometria não invalida a identificação cadastral.
            continue

    return {
        "ok": True,
        "quantidade_resultados": len(resultados),
        "resultados": resultados,
        "geometrias": geometria,
        "geometria_disponivel": bool(geometria),
        "sistema_referencia_geometria": 31983,
        "fonte": LOTES_URL,
        "observacao": (
            "Dados cadastrais/urbanísticos do SISURB. A geometria é retornada "
            "quando disponível para permitir consultas espaciais de restrições. "
            "Campos estimados devem permanecer identificados como estimados."
        ),
    }

@mcp.tool()
def consultar_restricoes_sisurb(geometria_lote: dict) -> dict:
    """Consulta por interseção espacial as áreas de restrição do SISURB para a geometria do lote."""
    if not geometria_lote:
        return {"ok": False, "status": "PENDENTE", "erro": "Geometria do lote não informada."}

    # Aceita tanto a geometria ArcGIS pura quanto o objeto retornado por buscar_lote_sisurb.
    geometry = geometria_lote.get("geometry", geometria_lote) if isinstance(geometria_lote, dict) else geometria_lote
    if not isinstance(geometry, dict) or not geometry.get("rings"):
        return {"ok": False, "status": "PENDENTE", "erro": "Geometria de lote inválida ou sem anéis poligonais."}

    fields = "OBJECTID,classe,tipologia,categoria,observacao,fonte,ano,shape.STArea()"
    try:
        data = arcgis_query(
            RESTRICOES_URL,
            "1=1",
            fields,
            return_geometry=False,
            geometry=geometry,
            geometry_type="esriGeometryPolygon",
            spatial_rel="esriSpatialRelIntersects",
            in_sr=31983, out_sr=31983,
            timeout=45,
        )
    except Exception as exc:
        return {
            "ok": False,
            "status": "PENDENTE",
            "erro": "Falha na consulta espacial da camada de restrições.",
            "detalhe_tecnico": str(exc),
            "fonte": RESTRICOES_URL,
        }

    feats = data.get("features", [])
    restricoes = [f.get("attributes", {}) for f in feats]
    return {
        "ok": True,
        "status": "SEM RESTRIÇÃO IDENTIFICADA" if not restricoes else "RESTRIÇÃO IDENTIFICADA",
        "quantidade": len(restricoes),
        "restricoes": restricoes,
        "fonte": RESTRICOES_URL,
        "metodo": "interseção espacial do polígono do lote com a camada oficial de áreas de restrição",
        "observacao": "A ausência de interseção nesta camada não exclui outras limitações legais ou ambientais que estejam fora desta camada."
    }


@mcp.tool()
def consultar_restricoes_por_lote(endereco: str = "", id_lote: str = "", geocodigo: str = "") -> dict:
    """Localiza o lote e verifica automaticamente sua interseção com áreas de restrição do SISURB."""
    if not any([endereco.strip(), str(id_lote).strip(), geocodigo.strip()]):
        return {"ok": False, "status": "PENDENTE", "erro": "Informe endereço, id_lote ou geocódigo."}

    fields = (
        "OBJECTID,geocodigo,id_lote,id_lote_pjf,id_lote_2,endereco,area_geometria"
    )
    where = None
    if geocodigo.strip():
        q = geocodigo.strip().replace("'", "''")
        where = f"geocodigo = '{q}'"
    elif str(id_lote).strip():
        try:
            where = f"id_lote = {int(float(id_lote))}"
        except Exception:
            q = str(id_lote).strip().replace("'", "''")
            where = f"id_lote = '{q}'"
    else:
        q = norm(endereco).replace("'", "''")
        where = f"UPPER(endereco) = '{q}'"

    try:
        data = arcgis_query(
            LOTES_URL, where, fields, return_geometry=True, out_sr=31983, timeout=45
        )
        feats = data.get("features", [])
        if not feats and endereco:
            q = norm(endereco).replace("'", "''")
            data = arcgis_query(
                LOTES_URL, f"UPPER(endereco) LIKE '%{q}%'", fields,
                return_geometry=True, out_sr=31983, timeout=45
            )
            feats = data.get("features", [])
    except Exception as exc:
        return {"ok": False, "status": "PENDENTE", "erro": "Falha ao localizar a geometria do lote.", "detalhe_tecnico": str(exc), "fonte": LOTES_URL}

    if not feats:
        return {"ok": False, "status": "PENDENTE", "erro": "Lote não encontrado para consulta espacial.", "fonte": LOTES_URL}

    resultados = []
    for f in feats[:10]:
        attrs = f.get("attributes", {})
        geometry = f.get("geometry")
        if not geometry:
            continue
        try:
            rd = arcgis_query(
                RESTRICOES_URL, "1=1",
                "OBJECTID,classe,tipologia,categoria,observacao,fonte,ano,shape.STArea()",
                geometry=geometry, geometry_type="esriGeometryPolygon",
                spatial_rel="esriSpatialRelIntersects", in_sr=31983, out_sr=31983, timeout=45
            )
            restricoes = [x.get("attributes", {}) for x in rd.get("features", [])]
            resultados.append({
                "lote": attrs,
                "status": "SEM RESTRIÇÃO IDENTIFICADA" if not restricoes else "RESTRIÇÃO IDENTIFICADA",
                "quantidade_restricoes": len(restricoes),
                "restricoes": restricoes,
            })
        except Exception as exc:
            resultados.append({"lote": attrs, "status": "PENDENTE", "erro": str(exc)})

    return {
        "ok": bool(resultados),
        "status": "CONCLUÍDO" if resultados and all(r.get("status") != "PENDENTE" for r in resultados) else "PENDENTE",
        "resultados": resultados,
        "fonte_lotes": LOTES_URL,
        "fonte_restricoes": RESTRICOES_URL,
        "metodo": "interseção espacial do polígono do lote com a camada oficial de áreas de restrição",
    }

@mcp.tool()
def consultar_zoneamento_por_lote(geometria_lote: dict) -> dict:
    """Identifica o(s) polígono(s) de zoneamento que intersectam a geometria do lote."""
    if not geometria_lote:
        return {"ok": False, "status": "PENDENTE", "erro": "Geometria do lote não informada."}
    geometry = geometria_lote.get("geometry", geometria_lote) if isinstance(geometria_lote, dict) else geometria_lote
    if not isinstance(geometry, dict) or not geometry.get("rings"):
        return {"ok": False, "status": "PENDENTE", "erro": "Geometria de lote inválida ou sem anéis poligonais."}
    fields = (
        "OBJECTID,nome,sigla,coef_aprov_perm_geral,taxa_ocup_perm_geral,"
        "taxa_impermeab_perm_geral,modelo_parcelamento_geral,area_minima_lote,"
        "coef_aprov_perm_res,coef_aprov_perm_com,coef_aprov_perm_inst,coef_aprov_perm_ind,"
        "modelo_ocupacao_geral,observacao,fonte,ano,geocodigo,legislacao_incidente,"
        "geocodigo_unificados,comentario_dado,tx_ocupacao_art36,area_geometria"
    )
    try:
        data = arcgis_query(
            ZONEAMENTO_URL, "1=1", fields, return_geometry=False,
            geometry=geometry, geometry_type="esriGeometryPolygon",
            spatial_rel="esriSpatialRelIntersects", in_sr=31983, out_sr=4674, timeout=45
        )
    except Exception as exc:
        return {
            "ok": False, "status": "PENDENTE",
            "erro": "Falha na consulta espacial do zoneamento.",
            "detalhe_tecnico": str(exc), "fonte": ZONEAMENTO_URL
        }
    feats = data.get("features", [])
    zonas = [f.get("attributes", {}) for f in feats]
    # Remove duplicatas exatas de OBJECTID, preservando todos os polígonos distintos.
    seen=set(); unique=[]
    for z in zonas:
        oid=z.get("OBJECTID")
        key=oid if oid is not None else repr(sorted(z.items()))
        if key not in seen:
            seen.add(key); unique.append(z)
    if not unique:
        return {
            "ok": True, "status": "NENHUMA ZONA INTERSECTADA", "quantidade": 0,
            "zonas": [], "fonte": ZONEAMENTO_URL,
            "metodo": "interseção espacial do polígono do lote com a camada oficial de zoneamento"
        }
    return {
        "ok": True, "status": "ZONEAMENTO IDENTIFICADO",
        "quantidade": len(unique), "zonas": unique, "fonte": ZONEAMENTO_URL,
        "metodo": "interseção espacial do polígono do lote com a camada oficial de zoneamento",
        "observacao": (
            "Se houver mais de um polígono, não escolher silenciosamente. Informar a sobreposição "
            "e confirmar qual feição efetivamente cobre a área do lote."
        )
    }


@mcp.tool()
def analisar_lote_sisurb(endereco: str = "", id_lote: str = "", geocodigo: str = "") -> dict:
    """Fluxo integrado: localiza lote, obtém zoneamento espacial e verifica restrições."""
    busca = buscar_lote_sisurb(endereco) if endereco.strip() else consultar_restricoes_por_lote(id_lote=id_lote, geocodigo=geocodigo)
    if not busca.get("ok"):
        # Fallback robusto: a ferramenta espacial de restrições já sabe localizar o lote.
        if endereco.strip():
            busca2 = consultar_restricoes_por_lote(endereco=endereco)
            if not busca2.get("ok"):
                return {"ok": False, "status": "PENDENTE", "erro": "Não foi possível localizar o lote.", "buscar_lote": busca, "fallback": busca2}
            itens = busca2.get("resultados", [])
            if not itens:
                return {"ok": False, "status": "PENDENTE", "erro": "Lote não encontrado.", "fallback": busca2}
            lotes = itens
            geometrias = []
            for item in itens:
                lote=item.get("lote", {})
                if lote.get("OBJECTID") is not None:
                    # A geometria não é exposta pelo fallback antigo; recupere por OBJECTID.
                    try:
                        gd=arcgis_query(LOTES_URL, f"OBJECTID = {int(lote['OBJECTID'])}", "*", return_geometry=True, out_sr=31983, timeout=45)
                        if gd.get("features") and gd["features"][0].get("geometry"):
                            geometrias.append({"lote": lote, "geometry": gd["features"][0]["geometry"]})
                    except Exception:
                        pass
            busca={"ok": bool(geometrias), "resultados": [x.get("lote",{}) for x in geometrias], "geometrias": geometrias, "fonte": LOTES_URL, "fallback_usado": True}
        else:
            return {"ok": False, "status": "PENDENTE", "erro": "Lote não localizado.", "buscar_lote": busca}
    geometrias=busca.get("geometrias", [])
    if not geometrias:
        # consultar_restricoes_por_lote pode devolver o lote mas não a geometria; tente pelos IDs.
        for lote in busca.get("resultados", []):
            oid=lote.get("OBJECTID")
            if oid is None: continue
            try:
                gd=arcgis_query(LOTES_URL, f"OBJECTID = {int(oid)}", "*", return_geometry=True, out_sr=31983, timeout=45)
                if gd.get("features") and gd["features"][0].get("geometry"):
                    geometrias.append({"OBJECTID":oid, "geocodigo":lote.get("geocodigo"), "id_lote":lote.get("id_lote"), "geometry":gd["features"][0]["geometry"]})
            except Exception:
                pass
    saida=[]
    for g in geometrias[:10]:
        z=consultar_zoneamento_por_lote(g.get("geometry",{}))
        r=consultar_restricoes_sisurb(g.get("geometry",{}))
        saida.append({"lote":g, "zoneamento":z, "restricoes":r})
    return {
        "ok": bool(saida), "status": "CONCLUÍDO" if saida else "PENDENTE",
        "lotes": saida, "buscar_lote": busca,
        "observacao": "Fluxo integrado espacial: lote → zoneamento → restrições. Nenhum parâmetro legal é inferido apenas pelo nome da zona."
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
                    "Para M3A, a matriz desta ferramenta adota CA 2,8 como parâmetro aplicável, "
                    "sem condicionar automaticamente o CA à antiga observação de vagas do Anexo 8; "
                    "a LC 54/2016, art. 2º, cancelou a última observação de vagas do Anexo 8."
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
        "A Lei Complementar nº 243/2024 alterou o Anexo 8 em matéria específica de uso institucional/hospitais; "
        "essa alteração não deve ser extrapolada para M3A residencial sem verificar o texto vigente. "
        "A legislação municipal possui alterações posteriores; a análise definitiva deve considerar a legislação vigente "
        "e eventuais leis específicas do trecho/via."
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
        "classificacao": "POTENCIAL TEÓRICO PRELIMINAR, NÃO POTENCIAL EDIFICÁVEL DEFINITIVO",
        "aviso": (
            "Não representa potencial edificável definitivo. O cálculo não incorpora "
            "recuos/afastamentos, envelope construtivo, altura legal confirmada, "
            "restrições espaciais e demais regras específicas."
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
