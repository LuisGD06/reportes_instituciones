import io
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.io import write_image

def kpi_block(container, title: str, value):
    container.metric(label=title, value=value)

def bar_horizontal_pct(df: pd.DataFrame, y: str, x: str, title: str | None = None):
    fig = px.bar(df, x=x, y=y, orientation="h", text=x)
    fig.update_traces(texttemplate="%{x:.1f}%", textposition="outside", cliponaxis=False)
    fig.update_layout(title=title or "", yaxis=dict(autorange="reversed"), xaxis_tickformat=".1f")
    return fig

def donut_chart(df: pd.DataFrame, title: str | None = None):
    if df.empty:
        return go.Figure()
    fig = px.pie(df, values="count", names="label", hole=0.5)
    fig.update_layout(title=title or "")
    return fig

def scatter_xy(df: pd.DataFrame, x: str, y: str, title: str | None = None):
    if df.empty:
        return go.Figure()
    fig = px.scatter(df, x=x, y=y, trendline="ols")
    fig.update_layout(title=title or "")
    return fig

def boxplot(df: pd.DataFrame, y: str, x: str, title: str | None = None):
    if df.empty:
        return go.Figure()
    fig = px.box(df, x=x, y=y, points="all")
    fig.update_layout(title=title or "")
    return fig

def area_timeseries(df: pd.DataFrame, x: str, y: str, title: str | None = None):
    if df.empty:
        return go.Figure()
    fig = px.area(df, x=x, y=y)
    fig.update_layout(title=title or "Altas por mes")
    return fig

def heatmap_matrix(df: pd.DataFrame, title: str | None = None):
    # df columns: skill_name, level, count
    if df.empty:
        return go.Figure()
    pivot = df.pivot(index="skill_name", columns="level", values="count").fillna(0)
    fig = px.imshow(pivot, aspect="auto", labels=dict(x="Nivel", y="Skill", color="Usuarios"))
    fig.update_layout(title=title or "Mapa de calor")
    return fig

def dataframe_download(df: pd.DataFrame, filename: str):
    if df.empty:
        st.warning("No hay datos para exportar.")
        return
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
    st.download_button("Descargar Excel", data=buf.getvalue(), file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
