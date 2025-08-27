import os
from typing import Dict, Any
from dotenv import load_dotenv

def _fallback_comment(module: str, stats: Dict[str, Any]) -> str:
    """Comentario simple sin LLM."""
    if module == "KPIs":
        return (f"La institución registra {stats.get('usuarios_total',0)} usuarios. "
                f"La actividad de 90 días se estima en {stats.get('activos_90d_pct',0)}%. "
                f"La experiencia mediana es {stats.get('exp_mediana_anos',0)} años y el salario esperado mediano es "
                f"S/ {stats.get('sal_mediana',0)}. Se recomienda profundizar en cohortes recientes y roles predominantes.")
    if module == "Skills":
        tops_h = [x.get('skill_name') for x in stats.get('top_hard',[])]
        tops_s = [x.get('skill_name') for x in stats.get('top_soft',[])]
        gaps = [x.get('skill_name') for x in stats.get('gap_top',[])]
        return (f"Hard skills destacados: {', '.join(tops_h[:3])}. Soft skills destacadas: {', '.join(tops_s[:3])}. "
                f"Oportunidades de refuerzo: {', '.join(gaps[:3])}.")
    if module == "SalariosExp":
        return (f"Existe correlación aproximada experiencia-salario de {stats.get('corr_approx',0)}. "
                f"Salario mediano S/ {stats.get('salario_p50',0)} para una experiencia mediana de {stats.get('exp_p50',0)} años.")
    if module == "Idiomas":
        top = stats.get("top_lang",[{"label":"(sin dato)"}])[0].get("label")
        return f"El idioma más frecuente es {top}. Se observa distribución de niveles acorde al MCER."
    if module == "Series":
        peak = stats.get("peak_month", [{"month":"(sin dato)","usuarios":0}])[0]
        return f"El mayor número de registros ocurrió en {peak.get('month')} con {peak.get('usuarios')} usuarios."
    return "Resumen no disponible."

def _try_gemini_comment(prompt: str) -> str:
    try:
        load_dotenv()
        from google import genai  # requiere google-genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return ""
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return getattr(resp, "text", "").strip()
    except Exception:
        return ""

def make_comment_summary(module: str, stats_dict: Dict[str, Any]) -> str:
    """Intenta con Gemini si hay API; si no, usa fallback."""
    prompt = (
        "Eres un analista de datos. Redacta un comentario breve (3-5 oraciones), claro y accionable, "
        f"sobre el módulo {module} con base en este resumen estadístico:\n{stats_dict}\n"
        "Incluye 1 recomendación concreta al final. Evita lenguaje sensacionalista."
    )
    txt = _try_gemini_comment(prompt)
    if txt:
        return txt
    return _fallback_comment(module, stats_dict)
