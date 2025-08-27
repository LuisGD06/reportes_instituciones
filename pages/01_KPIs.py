import streamlit as st
from src.io_load import load_raw, list_institutions
from src.transforms import (
    compute_kpis_snapshot, dist_situacion_actual, dist_modalidad, dist_status_academic
)
from src.charts import kpi_block, bar_horizontal_pct, donut_chart
from src.comments import make_comment_summary
from src.export_ppt import export_ppt

st.title("📌 KPIs")

raw = load_raw()
institutions = list_institutions(raw["users"])
inst = st.sidebar.selectbox("Institución", options=institutions, index=0, key="kpis_inst")

date_range = st.sidebar.date_input("Rango de registro (opcional)", value=None, key="kpis_dates")

kpis = compute_kpis_snapshot(raw, institution=inst, date_range=date_range)
c1, c2, c3, c4 = st.columns(4)
kpi_block(c1, "Usuarios", kpis["usuarios_total"])
kpi_block(c2, "Activos 90d", f"{kpis['activos_90d_pct']:.1f}%")
kpi_block(c3, "Experiencia mediana (años)", f"{kpis['exp_mediana_anos']:.1f}")
kpi_block(c4, "Salario esperado mediano", f"S/ {kpis['sal_mediana']:.0f}")

# Distribuciones clave
dist1 = dist_situacion_actual(raw, inst, date_range)
dist2 = dist_modalidad(raw, inst, date_range)
dist3 = dist_status_academic(raw, inst, date_range)

fig1 = donut_chart(dist1, "Situación actual")
fig2 = donut_chart(dist2, "Preferencia de modalidad")
fig3 = donut_chart(dist3, "Estado académico")

c5, c6, c7 = st.columns(3)
c5.plotly_chart(fig1, use_container_width=True)
c6.plotly_chart(fig2, use_container_width=True)
c7.plotly_chart(fig3, use_container_width=True)

# Comentario
st.subheader("🗒️ Comentario automático")
summary_text = make_comment_summary(module="KPIs", stats_dict={
    "usuarios_total": kpis["usuarios_total"],
    "activos_90d_pct": round(kpis["activos_90d_pct"], 1),
    "exp_mediana_anos": round(kpis["exp_mediana_anos"], 1),
    "sal_mediana": round(kpis["sal_mediana"], 0),
    "top_situacion": dist1.head(1).to_dict("records"),
    "top_modalidad": dist2.head(1).to_dict("records")
})
st.write(summary_text)

# Exportar PPT
st.subheader("📤 Exportar")
if st.button("Exportar reporte a PowerPoint"):
    path = export_ppt(
        institution=inst,
        kpis=kpis,
        figs={"Situación actual": fig1, "Modalidad": fig2, "Estado académico": fig3},
        comments=summary_text
    )
    st.success(f"Reporte creado: {path}")
