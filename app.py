import os
import streamlit as st
from src.io_load import list_institutions, load_raw
from src.transforms import compute_kpis_snapshot
from src.charts import kpi_block

st.set_page_config(
    page_title="Reportes por Institución",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("📊 Reportes por Institución")

# Sidebar: selección de institución
raw = load_raw()  # Carga y cachea los 6 Excel
institutions = list_institutions(raw["users"])
inst = st.sidebar.selectbox("Institución", options=institutions, index=0)

# Rango de fechas (para registrar sólo por registration_date)
date_range = st.sidebar.date_input(
    "Rango de registro (opcional)",
    value=None
)

st.sidebar.caption("Usa las páginas del menú (izquierda) para navegar por KPIs, Skills, Salarios, Idiomas, Series, Tablas.")

# Portada rápida con KPIs esenciales
kpi_vals = compute_kpis_snapshot(raw, institution=inst, date_range=date_range)
c1, c2, c3, c4 = st.columns(4)
kpi_block(c1, "Usuarios", kpi_vals["usuarios_total"])
kpi_block(c2, "Activos 90d", f"{kpi_vals['activos_90d_pct']:.1f}%")
kpi_block(c3, "Experiencia mediana (años)", f"{kpi_vals['exp_mediana_anos']:.1f}")
kpi_block(c4, "Salario esperado mediano", f"S/ {kpi_vals['sal_mediana']:.0f}")

st.info(
    "👉 Usa el menú de la izquierda (páginas) para ver gráficos y comentarios. "
    "Puedes exportar el reporte desde la página de KPIs."
)
