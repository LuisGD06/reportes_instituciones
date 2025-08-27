from __future__ import annotations
from typing import Dict, Optional, List
import pandas as pd
import numpy as np
from datetime import date, timedelta
from .io_load import filter_by_institution_and_date

MCER_TO_NUM = {"A1":1, "A2":2, "B1":3, "B2":4, "C1":5, "C2":6}

def _now_date() -> date:
    return pd.Timestamp.today().date()

def _experience_years(workexp: pd.DataFrame) -> pd.DataFrame:
    """Suma duración en meses por usuario y convierte a años (float)."""
    if workexp.empty:
        return pd.DataFrame({"user_id": [], "exp_years": []})
    agg = workexp.groupby("user_id", as_index=False)["duration_months"].sum()
    agg["exp_years"] = (agg["duration_months"] / 12.0).round(2)
    return agg[["user_id","exp_years"]]

def _salary_mid(onb: pd.DataFrame) -> pd.Series:
    if onb.empty:
        return pd.Series([], dtype=float)
    mid = (onb["salario_expect_min"].fillna(0) + onb["salario_expect_max"].fillna(0)) / 2.0
    return mid

def compute_kpis_snapshot(dfs: Dict[str, pd.DataFrame], institution: Optional[str], date_range=None) -> Dict[str, float]:
    f = filter_by_institution_and_date(dfs, institution, date_range)
    users = f["users"]; onb = f["onboardings"]; work = f["workexperiences"]

    usuarios_total = int(users.shape[0])
    if usuarios_total == 0:
        return dict(usuarios_total=0, activos_90d_pct=0.0, exp_mediana_anos=0.0, sal_mediana=0.0)

    # activos 90d ~ registro reciente (si no hay 'last_activity_date')
    cutoff = _now_date() - timedelta(days=90)
    activos_90d = users["registration_date"].fillna(date(1970,1,1)).apply(lambda d: d >= cutoff).sum()
    activos_90d_pct = (activos_90d / usuarios_total) * 100.0

    exp = _experience_years(work)
    exp_mediana_anos = float(exp["exp_years"].median()) if not exp.empty else 0.0

    if onb.empty:
        sal_mediana = 0.0
    else:
        sal_mediana = float(_salary_mid(onb).median())

    return dict(
        usuarios_total=usuarios_total,
        activos_90d_pct=activos_90d_pct,
        exp_mediana_anos=exp_mediana_anos,
        sal_mediana=sal_mediana
    )

def dist_situacion_actual(dfs, institution: Optional[str], date_range=None) -> pd.DataFrame:
    f = filter_by_institution_and_date(dfs, institution, date_range)
    onb = f["onboardings"].copy()
    if onb.empty: return pd.DataFrame(columns=["label","count","pct"])
    s = onb["situacion_actual"].value_counts(dropna=False).rename_axis("label").reset_index(name="count")
    total = s["count"].sum()
    s["pct"] = s["count"]*100/total
    return s

def dist_modalidad(dfs, institution: Optional[str], date_range=None) -> pd.DataFrame:
    f = filter_by_institution_and_date(dfs, institution, date_range)
    users = f["users"].copy()
    if users.empty: return pd.DataFrame(columns=["label","count","pct"])
    s = users["modality_preference"].value_counts(dropna=False).rename_axis("label").reset_index(name="count")
    total = s["count"].sum()
    s["pct"] = s["count"]*100/total
    return s

def dist_status_academic(dfs, institution: Optional[str], date_range=None) -> pd.DataFrame:
    f = filter_by_institution_and_date(dfs, institution, date_range)
    users = f["users"].copy()
    if users.empty: return pd.DataFrame(columns=["label","count","pct"])
    s = users["status_academic"].value_counts(dropna=False).rename_axis("label").reset_index(name="count")
    total = s["count"].sum()
    s["pct"] = s["count"]*100/total
    return s

def skills_coverage(dfs, institution: Optional[str], date_range=None, skill_type="hard") -> pd.DataFrame:
    f = filter_by_institution_and_date(dfs, institution, date_range)
    users = f["users"]; skills = f["skills"]
    if skills.empty or users.empty:
        return pd.DataFrame(columns=["skill_name","users","coverage_pct","avg_level"])
    skills = skills[skills["skill_type"] == skill_type].copy()
    if skills.empty:
        return pd.DataFrame(columns=["skill_name","users","coverage_pct","avg_level"])
    # usuarios únicos por skill
    g = skills.groupby("skill_name", as_index=False).agg(users=("user_id","nunique"), avg_level=("level","mean"))
    total_users = users["user_id"].nunique()
    g["coverage_pct"] = (g["users"] * 100.0 / max(1,total_users)).round(2)
    g["avg_level"] = g["avg_level"].round(2)
    g = g.sort_values(["coverage_pct","users"], ascending=[False,False])
    return g

def skills_heatmap(dfs, institution: Optional[str], date_range=None, skill_type="hard") -> pd.DataFrame:
    f = filter_by_institution_and_date(dfs, institution, date_range)
    skills = f["skills"]
    if skills.empty:
        return pd.DataFrame(columns=["skill_name","level","count"])
    df = skills[skills["skill_type"] == skill_type].copy()
    if df.empty:
        return pd.DataFrame(columns=["skill_name","level","count"])
    heat = df.groupby(["skill_name","level"], as_index=False)["user_id"].nunique()
    heat = heat.rename(columns={"user_id":"count"})
    return heat

def _coverage_from(skills: pd.DataFrame, users: pd.DataFrame, skill_type="hard") -> pd.DataFrame:
    df = skills[skills["skill_type"] == skill_type].copy()
    if df.empty or users.empty:
        return pd.DataFrame(columns=["skill_name","coverage_pct"])
    g = df.groupby("skill_name", as_index=False).agg(users=("user_id","nunique"))
    total = users["user_id"].nunique()
    g["coverage_pct"] = (g["users"] * 100.0 / max(1,total)).round(2)
    return g[["skill_name","coverage_pct"]]

def skills_gaps_vs_global(dfs, institution: Optional[str], date_range=None, skill_type="hard") -> pd.DataFrame:
    """gap_pct = coverage_global - coverage_inst (positivo => oportunidad de refuerzo)"""
    f_inst = filter_by_institution_and_date(dfs, institution, date_range)
    f_all = filter_by_institution_and_date(dfs, institution=None, date_range=None)

    cov_inst = _coverage_from(f_inst["skills"], f_inst["users"], skill_type=skill_type)
    cov_global = _coverage_from(f_all["skills"], f_all["users"], skill_type=skill_type)
    if cov_inst.empty or cov_global.empty:
        return pd.DataFrame(columns=["skill_name","gap_pct"])

    m = cov_global.merge(cov_inst, on="skill_name", how="left", suffixes=("_global","_inst"))
    m["coverage_pct_inst"] = m["coverage_pct_inst"].fillna(0.0)
    m["gap_pct"] = (m["coverage_pct_global"] - m["coverage_pct_inst"]).round(2)
    m = m.sort_values("gap_pct", ascending=False)
    return m[["skill_name","gap_pct","coverage_pct_global","coverage_pct_inst"]]

def salaries_experience_df(dfs, institution: Optional[str], date_range=None) -> pd.DataFrame:
    f = filter_by_institution_and_date(dfs, institution, date_range)
    users = f["users"]; onb = f["onboardings"]; work = f["workexperiences"]

    exp = _experience_years(work)
    mid = _salary_mid(onb)
    if onb.empty:
        return pd.DataFrame(columns=["user_id","exp_years","salario_mid","situacion_actual"])

    tmp = onb.assign(salario_mid=mid)
    out = users[["user_id"]].merge(exp, on="user_id", how="left").merge(
        tmp[["user_id","salario_mid","situacion_actual"]], on="user_id", how="left"
    )
    out["exp_years"] = out["exp_years"].fillna(0.0)
    out["salario_mid"] = out["salario_mid"].fillna(0.0)
    return out

def salaries_box_by_group(dfs, institution: Optional[str], date_range=None, group_col="situacion_actual") -> pd.DataFrame:
    df = salaries_experience_df(dfs, institution, date_range)
    if df.empty:
        return pd.DataFrame(columns=[group_col,"salario_mid"])
    df[group_col] = df[group_col].fillna("(sin dato)")
    return df[[group_col,"salario_mid"]]

def languages_distribution(dfs, institution: Optional[str], date_range=None) -> pd.DataFrame:
    f = filter_by_institution_and_date(dfs, institution, date_range)
    lang = f["languages"]
    if lang.empty:
        return pd.DataFrame(columns=["label","count","pct"])
    s = lang["lang_code"].value_counts().rename_axis("label").reset_index(name="count")
    total = s["count"].sum()
    s["pct"] = s["count"] * 100.0 / max(1,total)
    return s

def languages_level_summary(dfs, institution: Optional[str], date_range=None) -> pd.DataFrame:
    f = filter_by_institution_and_date(dfs, institution, date_range)
    lang = f["languages"].copy()
    if lang.empty:
        return pd.DataFrame(columns=["lang_code","level_numeric_mean"])
    lang["num"] = lang["level"].map(MCER_TO_NUM).fillna(0)
    g = lang.groupby("lang_code", as_index=False)["num"].mean()
    g = g.rename(columns={"num":"level_numeric_mean"}).sort_values("level_numeric_mean", ascending=False)
    return g

def registrations_by_month(dfs, institution: Optional[str]) -> pd.DataFrame:
    f = filter_by_institution_and_date(dfs, institution, date_range=None)
    users = f["users"].copy()
    if users.empty:
        return pd.DataFrame(columns=["month","usuarios"])
    users["month"] = pd.to_datetime(users["registration_date"]).dt.to_period("M").astype(str)
    s = users.groupby("month", as_index=False)["user_id"].count().rename(columns={"user_id":"usuarios"})
    return s

def ready_to_hire_table(
    dfs, institution: Optional[str], date_range=None,
    min_exp_years: float = 1.0,
    salary_mid_cap: float = 8000.0,
    lang_required: Optional[List[str]] = None
) -> pd.DataFrame:
    """Segmentación simple: experiencia mínima, salario medio (mid) debajo de umbral, y cobertura de idiomas requerida."""
    from .io_load import filter_by_institution_and_date
    f = filter_by_institution_and_date(dfs, institution, date_range)
    users = f["users"]; onb = f["onboardings"]; work = f["workexperiences"]; lang = f["languages"]

    exp = _experience_years(work)
    onb2 = onb.assign(salario_mid=_salary_mid(onb))
    base = users.merge(exp, on="user_id", how="left").merge(onb2[["user_id","salario_mid","situacion_actual"]], on="user_id", how="left")
    base["exp_years"] = base["exp_years"].fillna(0.0)
    base["salario_mid"] = base["salario_mid"].fillna(0.0)

    # Idiomas
    if lang_required:
        per_user_langs = lang.groupby("user_id")["lang_code"].apply(lambda s: set(s.dropna().unique().tolist())).reset_index()
        base = base.merge(per_user_langs, on="user_id", how="left")
        base["lang_code"] = base["lang_code"].apply(lambda x: x if isinstance(x, set) else set())
        req = set(lang_required)
        base = base[base["lang_code"].apply(lambda s: req.issubset(s))].copy()
        base = base.drop(columns=["lang_code"], errors="ignore")

    out = base[(base["exp_years"] >= min_exp_years) & (base["salario_mid"] > 0) & (base["salario_mid"] <= salary_mid_cap)].copy()
    cols = ["user_id","full_name","current_role","situacion_actual","exp_years","salario_mid","institution_name","modality_preference","status_academic"]
    keep = [c for c in cols if c in out.columns]
    return out[keep].sort_values(["exp_years","salario_mid"], ascending=[False,True])
