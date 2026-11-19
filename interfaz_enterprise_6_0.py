import os
import json
import uuid
import hashlib
from io import BytesIO
from datetime import datetime
import streamlit as st
import pandas as pd

try:
    from motor_forense_universal import (
        PERFILES_ENTIDAD,
        calcular_nivel_riesgo,
        analizar_compras_dinamico,
        cruzar_debida_diligencia,
        generar_acta_custodia_docx,
        generar_informe_pericial_docx,
    )
except Exception:
    PERFILES_ENTIDAD = {
        "Institución Pública / Gubernamental": {"peso_transparencia": 0.35, "peso_controles": 0.40, "peso_forense": 0.25},
        "Empresa Privada Corporativa": {"peso_transparencia": 0.20, "peso_controles": 0.50, "peso_forense": 0.30},
        "Entidad Financiera / Bancaria": {"peso_transparencia": 0.20, "peso_controles": 0.45, "peso_forense": 0.35},
        "ONG / Fundación Sin Fines de Lucro": {"peso_transparencia": 0.35, "peso_controles": 0.40, "peso_forense": 0.25},
    }

    def calcular_nivel_riesgo(val: float) -> str:
        if val >= 20:
            return "Crítico"
        if val >= 15:
            return "Muy alto"
        if val >= 10:
            return "Moderado"
        if val >= 5:
            return "Bajo"
        return "Mínimo"

    def analizar_compras_dinamico(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
        cols_num = df.select_dtypes(include="number").columns.tolist()
        if not cols_num:
            return pd.DataFrame()
        col_m = cols_num[0]
        umbral = float(df[col_m].mean() + 2 * df[col_m].std()) if len(df) > 1 else float(df[col_m].max())
        alertas = df[df[col_m] >= umbral].copy()
        if not alertas.empty:
            alertas["alerta_forense"] = "Monto atípico superior a 2 desviaciones estándar"
        return alertas

    def cruzar_debida_diligencia(df_emp: pd.DataFrame, df_prov: pd.DataFrame) -> pd.DataFrame:
        if df_emp.empty or df_prov.empty:
            return pd.DataFrame()
        c1, c2 = df_emp.columns[0], df_prov.columns[0]
        m = pd.merge(df_emp, df_prov, left_on=c1, right_on=c2, how="inner")
        if not m.empty:
            m["hallazgo_dd"] = "Coincidencia directa Empleado / Proveedor"
        return m

    def generar_acta_custodia_docx(*args, **kwargs) -> bytes:
        return b"Acta de Custodia Digital SHA-256"

    def generar_informe_pericial_docx(*args, **kwargs) -> bytes:
        return b"Informe Pericial Forense ISO 37001"

try:
    from asistente_ruta_100 import renderizar_guia_ia
except Exception:
    def renderizar_guia_ia(nombre_entidad, periodo_auditado, tiene_control, casos, evs):
        pasos = [
            bool(nombre_entidad),
            bool(periodo_auditado),
            bool(tiene_control),
            len(casos) > 0,
            len(evs) > 0,
        ]
        pct = int((sum(pasos) / len(pasos)) * 100)
        with st.expander(f"🧭 Ruta 100% Certificación ISO 37001:2025 — Avance actual: {pct}%", expanded=False):
            st.progress(pct / 100.0)
            st.caption("Complete expediente, evaluación documental, casos/hallazgos y evidencias SHA-256 para alcanzar el dictamen óptimo.")

try:
    from evaluador_certificacion_ia import (
        calcular_calificacion_imparcial,
        generar_guia_investigacion_ia,
        emitir_certificado_oficial_docx,
        emitir_certificado_oficial_pdf,
    )
except Exception:
    def calcular_calificacion_imparcial(ef_actual, casos, evs, n_af, n_dd):
        nota_c = round(min(100.0, max(0.0, float(ef_actual))), 1)
        nota_p = round(sum(float(c.avance_pac or 0) for c in casos) / len(casos), 1) if casos else 0.0
        nota_e = round(min(100.0, len(evs) * 15.0), 1)
        penalizacion = min(35.0, (n_af * 4.0) + (n_dd * 7.0))
        nota_f = round(max(0.0, 100.0 - penalizacion), 1)
        nota_g = round((nota_c * 0.35) + (nota_f * 0.25) + (nota_p * 0.25) + (nota_e * 0.15), 1)
        dictamen = "CERTIFICABLE ISO 37001" if nota_g >= 85 else ("EN PROCESO DE ADECUACIÓN" if nota_g >= 65 else "RIESGO ALTO / NO CONFORME")
        return {
            "nota_global": nota_g,
            "nota_controles": nota_c,
            "nota_forense": nota_f,
            "nota_pac": nota_p,
            "nota_evidencias": nota_e,
            "dictamen": dictamen,
        }

    def generar_guia_investigacion_ia(eval_ia, casos):
        return f"Dictamen actual: {eval_ia['dictamen']} ({eval_ia['nota_global']}%). Priorizar cierre de {len([c for c in casos if c.estado != 'Cerrado'])} hallazgos abiertos."

    def emitir_certificado_oficial_docx(entidad, periodo, eval_ia, codigo_cert):
        txt = f"CERTIFICADO OFICIAL ISO 37001:2025\nCodigo: {codigo_cert}\nEntidad: {entidad}\nPeriodo: {periodo}\nNota Global: {eval_ia['nota_global']}%\nDictamen: {eval_ia['dictamen']}"
        return txt.encode("utf-8")

    def emitir_certificado_oficial_pdf(entidad, periodo, eval_ia, codigo_cert):
        return emitir_certificado_oficial_docx(entidad, periodo, eval_ia, codigo_cert)

try:
    from ingesta_multiformato_b4 import (
        extraer_texto_multiformato,
        analizar_portal_transparencia_url,
        evaluar_brechas_documentales_ia,
        generar_politica_y_plan_90_dias_docx,
    )
except Exception:
    def extraer_texto_multiformato(archivo) -> str:
        raw = archivo.read()
        archivo.seek(0)
        return raw.decode("utf-8", errors="ignore")[:8000]

    def analizar_portal_transparencia_url(url: str) -> dict:
        import urllib.request
        import re
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        texto = re.sub(r"<[^>]+>", " ", html)
        texto = re.sub(r"\s+", " ", texto).strip()
        claves = ["antisoborno", "iso 37001", "ética", "transparencia", "denuncia", "compliance", "soborno", "integridad"]
        halladas = [k for k in claves if k in texto.lower()]
        score = round((len(halladas) / len(claves)) * 100, 1)
        return {
            "url": url,
            "palabras_clave": halladas,
            "porcentaje": score,
            "riesgo": "Bajo" if score >= 75 else ("Moderado" if score >= 45 else "Alto"),
            "resumen": texto[:1200],
            "sha256": hashlib.sha256(texto.encode("utf-8")).hexdigest(),
        }

    def evaluar_brechas_documentales_ia(texto_consolidado: str) -> dict:
        requisitos = {
            "4.5 Evaluación de Riesgos de Soborno": "riesgo",
            "5.1 Liderazgo y Compromiso": "dirección",
            "5.3 Función de Cumplimiento Antisoborno": "cumplimiento",
            "7.2 Competencia y Debida Diligencia": "diligencia",
            "8.7 Regalos, Hospitalidad y Donaciones": "regalo",
            "8.9 Planteamiento de Inquietudes (Canal Ético)": "denuncia",
        }
        filas = []
        cumplidos = 0
        low = texto_consolidado.lower()
        for req, kw in requisitos.items():
            ok = kw in low
            if ok:
                cumplidos += 1
            filas.append({
                "Cláusula ISO 37001": req,
                "Estado": "Evidenciado" if ok else "Brecha Detectada",
                "Nivel Riesgo": "Bajo" if ok else "Alto",
                "Acción Requerida": "Mantener monitoreo" if ok else f"Documentar e implementar control para {req}",
            })
        pct = round((cumplidos / len(requisitos)) * 100, 1)
        return {"efectividad": pct, "matriz": pd.DataFrame(filas)}

    def generar_politica_y_plan_90_dias_docx(entidad: str, horizonte: str, brechas_df: pd.DataFrame) -> bytes:
        lineas = [f"POLITICA ANTISOBORNO ISO 37001:2025 Y PLAN ({horizonte}) - {entidad}", "=" * 60]
        if brechas_df is not None and not brechas_df.empty:
            for _, r in brechas_df.iterrows():
                lineas.append(f"- {r.iloc[0]}: {r.iloc[1]} -> {r.iloc[-1]}")
        return "\n".join(lineas).encode("utf-8")

try:
    from modulo_comercial_legal import generar_contrato_saas_docx, generar_brochure_propuesta_docx
except Exception:
    def generar_contrato_saas_docx(cliente: str, monto: float) -> bytes:
        return f"CONTRATO LICENCIAMIENTO SAAS SIG ANTISOBORNO\nCliente: {cliente}\nInversion: USD {monto:,.2f}".encode("utf-8")

    def generar_brochure_propuesta_docx(cliente: str) -> bytes:
        return f"PROPUESTA TECNICA Y COMERCIAL BIG-4 SUITE\nEntidad: {cliente}".encode("utf-8")

from motor_mejora_continua_ia import inicializar_motor_mejora_continua, renderizar_modulo_mejora_continua

USUARIOS = {
    "admin": {"pass": os.getenv("SIG_ADMIN_PASSWORD", "Admin123!"), "rol": "Socio Director / Admin"},
    "oficial": {"pass": os.getenv("SIG_OFICIAL_PASSWORD", "Oficial123!"), "rol": "Oficial de Cumplimiento"},
    "auditor": {"pass": os.getenv("SIG_AUDITOR_PASSWORD", "Auditor123!"), "rol": "Auditor Forense Senior"},
    "cliente": {"pass": os.getenv("SIG_CLIENTE_PASSWORD", "Cliente123!"), "rol": "Cliente Evaluado (Autogestión)"},
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def riesgo(p: int, i: int) -> int:
    return int(max(1, min(5, p)) * max(1, min(5, i)))


def residual(inh: float, ef: float) -> float:
    return round(max(0.0, inh * (1 - max(0.0, min(100.0, float(ef))) / 100.0)), 2)


def colorear_matriz_5x5(val):
    if val >= 20:
        return "background-color: #8B0000; color: white; font-weight: bold;"
    elif val >= 15:
        return "background-color: #D9534F; color: white; font-weight: bold;"
    elif val >= 10:
        return "background-color: #F0AD4E; color: black; font-weight: bold;"
    elif val >= 5:
        return "background-color: #FFF3CD; color: black;"
    return "background-color: #DFF0D8; color: black;"


def ejecutar_suite_enterprise(SessionLocal, Caso, CicloEvaluacion, Historico, Evidencia, Denuncia, Conocimiento, EXPORT_DIR, EVIDENCE_DIR, VERSION):
