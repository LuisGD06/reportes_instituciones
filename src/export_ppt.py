from __future__ import annotations
from typing import Dict
from pathlib import Path
from datetime import datetime
import tempfile
import plotly.io as pio
from pptx import Presentation
from pptx.util import Inches, Pt

TEMPLATES_DIR = Path("templates")
DEFAULT_TEMPLATE = TEMPLATES_DIR / "ppt_template.pptx"

def _ensure_template() -> Path:
    if DEFAULT_TEMPLATE.exists():
        return DEFAULT_TEMPLATE
    # Crea una presentación básica si no hay plantilla
    prs = Presentation()
    tmp = TEMPLATES_DIR / "_auto_template.pptx"
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    prs.save(tmp)
    return tmp

def export_ppt(institution: str, kpis: dict, figs: Dict[str, "plotly.graph_objs._figure.Figure"], comments: str) -> str:
    """Exporta un PPT con portada, KPIs, gráficos y comentarios."""
    prs = Presentation(_ensure_template())

    # Portada
    title_slide_layout = prs.slide_layouts[0] if prs.slide_layouts else prs.slides.add_slide(prs.slide_layouts[5])
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = f"Reporte - {institution}"
    slide.placeholders[1].text = f"Fecha: {datetime.now():%Y-%m-%d}\nGenerado automáticamente"

    # KPIs
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "KPIs"
    body = slide.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(9), Inches(3)).text_frame
    body.word_wrap = True
    body.text = (f"Usuarios: {kpis.get('usuarios_total',0)}\n"
                 f"Activos 90d: {kpis.get('activos_90d_pct',0):.1f}%\n"
                 f"Experiencia mediana: {kpis.get('exp_mediana_anos',0):.1f} años\n"
                 f"Salario mediano: S/ {kpis.get('sal_mediana',0):.0f}")

    # Gráficos
    for title, fig in figs.items():
        slide = prs.slides.add_slide(prs.slide_layouts[5])
        slide.shapes.title.text = title
        # Intentar exportar imagen con kaleido (si está instalado)
        img_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                pio.write_image(fig, tmp.name, width=1280, height=720, scale=2)
                img_path = tmp.name
        except Exception:
            # Si no hay kaleido, insertamos un texto de fallback
            tf = slide.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(9), Inches(3)).text_frame
            tf.text = "(No se pudo exportar el gráfico como imagen. Instala 'kaleido' para incluir gráficos en el PPT.)"
        if img_path:
            slide.shapes.add_picture(img_path, Inches(0.7), Inches(1.5), Inches(9), Inches(5))

    # Comentarios
    slide = prs.slides.add_slide(prs.slide_layouts[5])
    slide.shapes.title.text = "Comentarios"
    tf = slide.shapes.add_textbox(Inches(0.7), Inches(1.2), Inches(9), Inches(4.5)).text_frame
    tf.word_wrap = True
    tf.text = comments

    out = Path(f"Reporte_{institution}.pptx")
    prs.save(out)
    return str(out.absolute())
