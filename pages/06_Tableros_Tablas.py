import streamlit as st
from src.io_load import load_raw, list_institutions
from src.transforms import ready_to_hire_table
from src.charts import dataframe_download

st.title("📋 Tablas y Segmentaciones")

raw = load_raw()
institutions = list_institutions(raw["users"])
inst = st.sidebar.selectbox("Institución", options=institutions, index=0, key="tab_inst")
date_range = st.sidebar.date_input("Rango de registro (opcional)", value=None, key="tab_dates")

min_exp = st.sidebar.slider("Mín. años experiencia", 0.0, 15.0, 1.0, 0.5)
salary_cap = st.sidebar.number_input("Tope salario esperado (mid)", min_value=0, max_value=50000, value=8000, step=500)
lang_req = st.sidebar.multiselect("Idiomas requeridos", options=["es","en","pt","fr","de"], default=["es","en"])

df = ready_to_hire_table(
    raw, institution=inst, date_range=date_range,
    min_exp_years=min_exp, salary_mid_cap=salary_cap, lang_required=lang_req
)
st.dataframe(df, use_container_width=True)

dataframe_download(df, filename=f"ready_to_hire_{inst}.xlsx")
