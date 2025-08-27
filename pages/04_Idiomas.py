import streamlit as st
from src.io_load import load_raw, list_institutions
from src.transforms import languages_distribution, languages_level_summary
from src.charts import donut_chart, bar_horizontal_pct
from src.comments import make_comment_summary

st.title("🗣️ Idiomas")

raw = load_raw()
institutions = list_institutions(raw["users"])
inst = st.sidebar.selectbox("Institución", options=institutions, index=0, key="lang_inst")
date_range = st.sidebar.date_input("Rango de registro (opcional)", value=None, key="lang_dates")

dist = languages_distribution(raw, inst, date_range)
st.plotly_chart(donut_chart(dist, "Idiomas (usuarios con idioma)"), use_container_width=True)

lvl = languages_level_summary(raw, inst, date_range)
st.plotly_chart(bar_horizontal_pct(lvl, "lang_code", "level_numeric_mean"), use_container_width=True)

st.subheader("🗒️ Comentario automático")
comment = make_comment_summary(
    module="Idiomas",
    stats_dict={
        "top_lang": dist.head(1).to_dict("records"),
        "avg_levels": lvl.to_dict("records")
    }
)
st.write(comment)
