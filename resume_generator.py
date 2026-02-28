"""Build resume dict from base resume + optional screening result (tailored projects)."""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List

import generate_resume

BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "base_resume.json"


def _load_base_resume() -> dict:
  with DATA_PATH.open(encoding="utf-8") as f:
    return json.load(f)


def build_resume_from_screening(screening_result: Dict[str, Any] | None) -> dict:
  """Build resume dict: base resume with projects replaced by screening selected_projects if provided."""
  resume = _load_base_resume()
  if not screening_result or not screening_result.get("selected_projects"):
    return resume

  selected: List[Dict[str, Any]] = screening_result["selected_projects"]
  projects = []
  for p in selected:
    title = p.get("project_title") or p.get("project_id") or "Project"
    bullets = p.get("rewritten_bullets")
    if not bullets or not isinstance(bullets, list):
      bullets = []
    projects.append({"name": title, "stack": None, "bullets": [str(b).strip() for b in bullets if str(b).strip()]})
  resume = copy.deepcopy(resume)
  resume["projects"] = projects
  return resume


def generate_resume_html(screening_result: Dict[str, Any] | None = None, for_pdf: bool = False) -> str:
  """Render resume HTML. If screening_result has selected_projects, use tailored projects. Use for_pdf=True for PDF download (table-based layout, single page)."""
  resume = build_resume_from_screening(screening_result)
  return generate_resume.render_resume_html(resume, for_pdf=for_pdf)


def generate_resume_pdf_bytes(html: str) -> bytes:
  """Return PDF as bytes. Tries WeasyPrint first, then xhtml2pdf (works on Windows without GTK)."""
  from io import BytesIO

  # Try WeasyPrint first (better layout, requires GTK on Windows)
  try:
    from weasyprint import HTML
    buf = BytesIO()
    HTML(string=html).write_pdf(buf)
    buf.seek(0)
    return buf.read()
  except (OSError, ImportError, Exception):
    pass

  # Fallback: xhtml2pdf (pure Python, works on Windows)
  try:
    from xhtml2pdf import pisa
    buf = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=buf, encoding="utf-8")
    buf.seek(0)
    if pisa_status.err:
      raise RuntimeError("xhtml2pdf failed to generate PDF")
    return buf.read()
  except Exception as e:
    raise RuntimeError(f"PDF generation failed: {e}") from e
