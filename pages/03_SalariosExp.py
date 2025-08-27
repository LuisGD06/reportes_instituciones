import streamlit as st
from src.io_load import load_raw, list_institutions
from src.transforms import salaries_experience_df, salaries_box_by_group
from src.charts import scatter_xy, boxplot
from src.comments import make_comment_summary

st.title("💰 Salarios & Experiencia")

raw = load_raw()
institutions = list_institutions(raw["users"])
inst = st.sidebar.selectbox("Institución", options=institutions, index=0, key="sal_inst")
date_range = st.sidebar.date_input("Rango de registro (opcional)", value=None, key="sal_dates")

df = salaries_experience_df(raw, inst, date_range)
st.plotly_chart(scatter_xy(df, x="exp_years", y="salario_mid", title="Dispersión: experiencia vs salario esperado"), use_container_width=True)

box = salaries_box_by_group(raw, inst, date_range, group_col="situacion_actual")
st.plotly_chart(boxplot(box, y="salario_mid", x="situacion_actual", title="Salario esperado por situación actual"), use_container_width=True)

st.subheader("🗒️ Comentario automático")
comment = make_comment_summary(
    module="SalariosExp",
    stats_dict={
        "corr_approx": round(df["exp_years"].corr(df["salario_mid"]), 2) if not df.empty else 0,
        "salario_p50": round(df["salario_mid"].median(), 0) if not df.empty else 0,
        "exp_p50": round(df["exp_years"].median(), 1) if not df.empty else 0
    }
)
st.write(comment)
