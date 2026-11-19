import os
import json
import uuid
import hashlib
from datetime import datetime
import streamlit as st
import pandas as pd

from motor_forense_universal import (
    PERFILES_ENTIDAD,
    calcular_nivel_riesgo,
    analizar_compras_dinamico,
    cruzar_debida_diligencia,
    generar_acta_custodia_docx,
    generar_informe_pericial_docx,
)
from asistente_ruta_100 import renderizar_guia_ia
from evaluador_certificacion_ia import (
    calcular_calificacion_imparcial,
    generar_guia_investigacion_ia,
    emitir_certificado_oficial_docx,
    emitir_certificado_oficial_pdf,
)
from ingesta_multiformato_b4 import (
    extraer_texto_multiformato,
    analizar_portal_transparencia_url,
    evaluar_brechas_documentales_ia,
    generar_politica_y_plan_90_dias_docx,
)
from modulo_comercial_legal import (
    generar_contrato_saas_docx,
    generar_brochure_propuesta_docx,
)

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


def ejecutar_suite_enterprise(
    SessionLocal,
    Caso,
    CicloEvaluacion,
    Historico,
    Evidencia,
    Denuncia,
    Conocimiento,
    EXPORT_DIR,
    EVIDENCE_DIR,
    VERSION,
):
    def cur_user():
        return st.session_state.get("usuario", "admin")

    def mark_save():
        st.session_state["ultimo_guardado"] = datetime.now().strftime("%H:%M:%S")

    def registrar(cod, acc, det, ea="", en="", ra="", rn=""):
        db = SessionLocal()
        prev = db.query(Historico).order_by(Historico.id.desc()).first()
        ph = prev.hash_sha256 if prev else "GENESIS"
        payload = json.dumps({"c": cod, "u": cur_user(), "a": acc, "d": det, "t": str(datetime.utcnow())})
        h = hashlib.sha256((ph + payload).encode()).hexdigest()
        db.add(
            Historico(
                codigo=cod,
                usuario=cur_user(),
                accion=acc,
                detalle=det,
                estado_anterior=ea,
                estado_nuevo=en,
                riesgo_anterior=ra,
                riesgo_actual=rn,
                hash_sha256=h,
            )
        )
        db.commit()
        db.close()
        mark_save()

    if not st.session_state.get("autenticado"):
        st.title(f"🛡️ SIG Antisoborno Audit Enterprise {VERSION}")
        st.caption("Plataforma Big-4 de Auditoría Forense, Control Interno ISO 37001:2025, Transparencia y Certificación Online")
        with st.form("login"):
            u = st.text_input("Usuario (admin / oficial / auditor / cliente)", value="admin")
            p = st.text_input("Contraseña", type="password", value="")
            if st.form_submit_button("Ingresar al Sistema", type="primary"):
                if u in USUARIOS and p == USUARIOS[u]["pass"]:
                    st.session_state.update(autenticado=True, usuario=u, rol=USUARIOS[u]["rol"])
                    registrar("SYSTEM", "LOGIN", f"Acceso perfil {USUARIOS[u]['rol']}")
                    st.rerun()
                else:
                    st.error("Credenciales inválidas")
        st.stop()

    st.sidebar.title(f"🛡️ SIG {VERSION} Enterprise")
    st.sidebar.write(f"**Usuario:** {cur_user()}  \n**Perfil:** {st.session_state.get('rol', '')}")
    if st.session_state.get("ultimo_guardado"):
        st.sidebar.success(f"💾 Autoguardado activo ({st.session_state['ultimo_guardado']})")

    with st.sidebar.expander("🏢 Expediente / Cliente Evaluado", expanded=True):
        modalidad_op = st.radio("Modalidad", ["Operación Control Interno", "Evaluación Externa / Cliente"], key="mod_op", on_change=mark_save)
        tipo_entidad = st.selectbox("Tipo de Entidad", list(PERFILES_ENTIDAD.keys()), key="t_ent", on_change=mark_save)
        nombre_entidad = st.text_input("Nombre de Empresa / Entidad", value=st.session_state.get("nombre_entidad", ""), on_change=mark_save)
        frecuencia_eval = st.selectbox("Frecuencia de Ciclo", ["Trimestral", "Semestral", "Anual", "Especial / Inicial"], key="freq_ev", on_change=mark_save)
        periodo_auditado = st.text_input("Período Evaluado", value=st.session_state.get("periodo_auditado", ""), placeholder="Ej. Q1-2026 o 2025-2026", on_change=mark_save)
        st.session_state["nombre_entidad"] = nombre_entidad
        st.session_state["periodo_auditado"] = periodo_auditado

    perfil = PERFILES_ENTIDAD[tipo_entidad]
    MODULOS_POR_ROL = {
        "admin": [
            "1. Dashboard y Mapa de Calor",
            "2. Ingesta Multiformato & Control Social Web",
            "3. Generador IA Políticas & Plan 90 Días",
            "4. Pruebas Forenses (Transacciones)",
            "5. Debida Diligencia (Cruces)",
            "6. Histórico Vivo & Planes de Fortalecimiento",
            "7. Evidencias SHA-256 & Custodia",
            "8. Canal Ético & Denuncias",
            "9. Comparativa Histórica entre Ciclos",
            "10. Certificación Online & Informes Gerenciales",
            "11. Bitácora Inmutable SHA-256",
            "12. Contratos SaaS & Brochure Comercial",
            "13. Mejora Continua Autónoma (IA)",
        ],
        "oficial": [
            "1. Dashboard y Mapa de Calor",
            "2. Ingesta Multiformato & Control Social Web",
            "3. Generador IA Políticas & Plan 90 Días",
            "4. Pruebas Forenses (Transacciones)",
            "5. Debida Diligencia (Cruces)",
            "6. Histórico Vivo & Planes de Fortalecimiento",
            "7. Evidencias SHA-256 & Custodia",
            "8. Canal Ético & Denuncias",
            "9. Comparativa Histórica entre Ciclos",
            "10. Certificación Online & Informes Gerenciales",
            "11. Bitácora Inmutable SHA-256",
            "13. Mejora Continua Autónoma (IA)",
        ],
        "auditor": [
            "1. Dashboard y Mapa de Calor",
            "2. Ingesta Multiformato & Control Social Web",
            "3. Generador IA Políticas & Plan 90 Días",
            "4. Pruebas Forenses (Transacciones)",
            "5. Debida Diligencia (Cruces)",
            "6. Histórico Vivo & Planes de Fortalecimiento",
            "7. Evidencias SHA-256 & Custodia",
            "8. Canal Ético & Denuncias",
            "9. Comparativa Histórica entre Ciclos",
            "10. Certificación Online & Informes Gerenciales",
            "11. Bitácora Inmutable SHA-256",
            "13. Mejora Continua Autónoma (IA)",
        ],
        "cliente": [
            "1. Dashboard y Mapa de Calor",
            "2. Ingesta Multiformato & Control Social Web",
            "6. Histórico Vivo & Planes de Fortalecimiento",
            "7. Evidencias SHA-256 & Custodia",
            "8. Canal Ético & Denuncias",
            "9. Comparativa Histórica entre Ciclos",
            "10. Certificación Online & Informes Gerenciales",
            "13. Mejora Continua Autónoma (IA)",
        ],
    }
    menu = st.sidebar.radio("Suite de Producción", MODULOS_POR_ROL.get(cur_user(), MODULOS_POR_ROL["cliente"]))

    if st.sidebar.button("Cerrar sesión"):
        st.session_state.clear()
        st.rerun()

    db = SessionLocal()
    casos = db.query(Caso).filter(Caso.eliminado == False).all()
    evs = db.query(Evidencia).all()
    ciclos_previos = db.query(CicloEvaluacion).order_by(CicloEvaluacion.id.desc()).all()
    db.close()

    ef_actual = float(st.session_state.get("efectividad_control_calculada", 0.0))
    n_af = len(st.session_state["ultimas_alertas_forenses"]) if "ultimas_alertas_forenses" in st.session_state else 0
    n_dd = len(st.session_state["ultimos_cruces_dd"]) if "ultimos_cruces_dd" in st.session_state else 0
    eval_ia = calcular_calificacion_imparcial(ef_actual, casos, evs, n_af, n_dd)

    renderizar_guia_ia(nombre_entidad, periodo_auditado, ef_actual > 0, casos, evs)

    # =========================================================================
    # MÓDULO 1: DASHBOARD Y MAPA DE CALOR
    # =========================================================================
    if menu == "1. Dashboard y Mapa de Calor":
        st.title("📊 Dashboard Ejecutivo y Mapa de Calor 5×5")
        df = pd.DataFrame(
            [
                {
                    "codigo": c.codigo,
                    "estado": c.estado,
                    "inherente": c.riesgo_inherente,
                    "residual": c.riesgo_residual,
                    "nivel": c.nivel_residual,
                    "pac": c.avance_pac,
                    "inversion": c.monto_inversion,
                }
                for c in casos
            ]
        )
        t = len(df)
        a, b, c, d, e = st.columns(5)
        a.metric("Calificación Global", f"{eval_ia['nota_global']}%")
        b.metric("Incidencias / Casos", t)
        c.metric("Críticos / Muy Altos", int(df["nivel"].isin(["Crítico", "Muy alto"]).sum()) if t else 0)
        d.metric("Cumplimiento PAC", f"{float(df['pac'].mean()):.1f}%" if t else "0.0%")
