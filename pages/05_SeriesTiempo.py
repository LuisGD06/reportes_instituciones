import streamlit as st
from src.io_load import load_raw, list_institutions
from src.transforms import registrations_by_month
from src.charts import area_timeseries
from src.comments import make_comment_summary

st.title("⏱️ Series de Tiempo")

raw = load_raw()
institutions = list_institutions(raw["users"])
inst = st.sidebar.selectbox("Institución", options=institutions, index=0, key="ts_inst")

ts = registrations_by_month(raw, inst)
st.plotly_chart(area_timeseries(ts, x="month", y="usuarios"), use_container_width=True)

st.subheader("🗒️ Comentario automático")
comment = make_comment_summary(
    module="Series",
    stats_dict={
        "peak_month": ts.sort_values("usuarios", ascending=False).head(1).to_dict("records")
    }
)
st.write(comment)
