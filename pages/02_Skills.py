import streamlit as st
from src.io_load import load_raw, list_institutions
from src.transforms import skills_coverage, skills_heatmap, skills_gaps_vs_global
from src.charts import bar_horizontal_pct, heatmap_matrix
from src.comments import make_comment_summary

st.title("🧩 Skills (hard & soft)")

raw = load_raw()
institutions = list_institutions(raw["users"])
inst = st.sidebar.selectbox("Institución", options=institutions, index=0, key="skills_inst")
date_range = st.sidebar.date_input("Rango de registro (opcional)", value=None, key="skills_dates")
top_n = st.sidebar.slider("Top-N habilidades", min_value=5, max_value=30, value=15)

# Cobertura de hard y soft
hard_cov = skills_coverage(raw, inst, date_range, skill_type="hard").head(top_n)
soft_cov = skills_coverage(raw, inst, date_range, skill_type="soft").head(top_n)

st.subheader("Hard skills (cobertura)")
st.plotly_chart(bar_horizontal_pct(hard_cov, "skill_name", "coverage_pct"), use_container_width=True)

st.subheader("Soft skills (cobertura)")
st.plotly_chart(bar_horizontal_pct(soft_cov, "skill_name", "coverage_pct"), use_container_width=True)

# Heatmap de niveles (si hay level)
st.subheader("Mapa de calor de niveles por skill (hard)")
hard_heat = skills_heatmap(raw, inst, date_range, skill_type="hard")
st.plotly_chart(heatmap_matrix(hard_heat, title="Hard skills × Nivel"), use_container_width=True)

# Gaps vs. global (oportunidades de mejora)
st.subheader("Oportunidades de mejora (gaps) vs. global")
gaps = skills_gaps_vs_global(raw, inst, date_range, skill_type="hard").head(15)
st.plotly_chart(bar_horizontal_pct(gaps, "skill_name", "gap_pct"), use_container_width=True)

# Comentario
st.subheader("🗒️ Comentario automático")
comment = make_comment_summary(
    module="Skills",
    stats_dict={
        "top_hard": hard_cov.head(3).to_dict("records"),
        "top_soft": soft_cov.head(3).to_dict("records"),
        "gap_top": gaps.head(3).to_dict("records")
    }
)
st.write(comment)
