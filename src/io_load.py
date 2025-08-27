from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import pandas as pd
import numpy as np
import os
import streamlit as st

DATA_DIR = Path("data")
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

REQUIRED = {
    "users": [
        "user_id", "full_name", "email", "phone",
        "institution_id", "institution_name", "campus",
        "country", "region", "city", "gender",
        "current_role", "status_academic", "registration_date",
        "modality_preference", "highest_education", "program_or_major",
    ],
    "workexperiences": [
        "user_id", "position_title", "industry_sector", "company_name",
        "start_date", "end_date", "duration_months",
    ],
    "educations": [
        "user_id", "institution_academic", "degree_level", "program_or_major",
        "start_date", "end_date", "gpa",
    ],
    "onboardings": [
        "user_id", "situacion_actual", "oportunidad_buscada",
        "salario_expect_min", "salario_expect_max", "rol_identificado",
    ],
    "skills": [
        "user_id", "skill_name", "skill_type", "level",
    ],
    "languages": [
        "user_id", "lang_code", "level",
    ],
}

@st.cache_data(show_spinner=False)
def _read_excel(path: Path, sheet: Optional[str] = None) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet or 0)
    return df

def _coerce_dates(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce").dt.date
    return df

def _coerce_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

def _fillna_text(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = df[c].fillna("").astype(str)
    return df

def _validate_columns(df: pd.DataFrame, required: List[str], name: str):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en {name}: {missing}")

@st.cache_data(show_spinner=False)
def load_raw() -> Dict[str, pd.DataFrame]:
    """Carga los 6 Excel a DataFrames con tipado/validación básica y cache de Streamlit."""
    paths = {
        "users": DATA_DIR / "users.xlsx",
        "workexperiences": DATA_DIR / "workexperiences.xlsx",
        "educations": DATA_DIR / "educations.xlsx",
        "onboardings": DATA_DIR / "onboardings.xlsx",
        "skills": DATA_DIR / "skills.xlsx",
        "languages": DATA_DIR / "languages.xlsx",
    }
    dfs = {k: _read_excel(p) for k, p in paths.items()}

    # Validar
    for name, df in dfs.items():
        _validate_columns(df, REQUIRED[name], name)

    # Tipado: fechas y numericos
    dfs["users"] = _coerce_dates(dfs["users"], ["registration_date"])
    dfs["workexperiences"] = _coerce_dates(dfs["workexperiences"], ["start_date", "end_date"])
    dfs["educations"] = _coerce_dates(dfs["educations"], ["start_date", "end_date"])

    dfs["workexperiences"] = _coerce_numeric(dfs["workexperiences"], ["duration_months"])
    dfs["educations"] = _coerce_numeric(dfs["educations"], ["gpa"])
    dfs["onboardings"] = _coerce_numeric(dfs["onboardings"], ["salario_expect_min", "salario_expect_max"])
    dfs["skills"] = _coerce_numeric(dfs["skills"], ["level"])

    # Texto: no nulos
    dfs["users"] = _fillna_text(dfs["users"], ["full_name","email","phone","institution_name","gender",
                                               "current_role","status_academic","modality_preference",
                                               "highest_education","program_or_major","campus","country","region","city"])
    dfs["skills"] = _fillna_text(dfs["skills"], ["skill_name","skill_type"])
    dfs["languages"] = _fillna_text(dfs["languages"], ["lang_code","level"])

    return dfs

def list_institutions(users_df: pd.DataFrame) -> List[str]:
    lst = sorted([x for x in users_df["institution_name"].dropna().unique().tolist() if str(x).strip()])
    return lst or ["(sin datos)"]

def filter_by_institution_and_date(dfs: Dict[str, pd.DataFrame], institution: Optional[str], date_range=None) -> Dict[str, pd.DataFrame]:
    """Filtra todos los DFs por institución y rango de registro en users."""
    users = dfs["users"].copy()
    if institution:
        users = users[users["institution_name"] == institution].copy()

    if date_range and isinstance(date_range, (list, tuple)) and len(date_range) == 2 and all(date_range):
        start, end = pd.to_datetime(date_range[0]).date(), pd.to_datetime(date_range[1]).date()
        users = users[(users["registration_date"] >= start) & (users["registration_date"] <= end)].copy()

    user_ids = set(users["user_id"].unique().tolist())

    out = {
        "users": users,
        "workexperiences": dfs["workexperiences"][dfs["workexperiences"]["user_id"].isin(user_ids)].copy(),
        "educations": dfs["educations"][dfs["educations"]["user_id"].isin(user_ids)].copy(),
        "onboardings": dfs["onboardings"][dfs["onboardings"]["user_id"].isin(user_ids)].copy(),
        "skills": dfs["skills"][dfs["skills"]["user_id"].isin(user_ids)].copy(),
        "languages": dfs["languages"][dfs["languages"]["user_id"].isin(user_ids)].copy(),
    }
    return out
