from __future__ import annotations
from typing import Dict, Any
from pathlib import Path
from jinja2 import Template

def export_pdf(context: Dict[str, Any], template_path: str = "templates/pdf_template.html", out_path: str = "Reporte.pdf"):
    """Requiere weasyprint instalado en el sistema (y dependencias del SO)."""
    try:
        from weasyprint import HTML
    except Exception as e:
        raise RuntimeError("Para exportar a PDF instala weasyprint y sus dependencias.") from e

    tpl = Path(template_path).read_text(encoding="utf-8")
    html = Template(tpl).render(**context)
    HTML(string=html).write_pdf(out_path)
    return str(Path(out_path).absolute())
