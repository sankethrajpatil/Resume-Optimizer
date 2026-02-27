from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "base_resume.json"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"


def load_resume() -> dict:
  """Load base resume data from JSON."""
  with DATA_PATH.open(encoding="utf-8") as f:
    return json.load(f)


def render_resume_html(resume: dict) -> str:
  """Render resume HTML from template and data."""
  env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
  )
  template = env.get_template("resume.html")
  return template.render(resume=resume)


def generate_pdf(html: str, output_path: Path) -> None:
  """Generate a PDF file from rendered HTML."""
  from weasyprint import HTML

  output_path.parent.mkdir(parents=True, exist_ok=True)
  HTML(string=html).write_pdf(str(output_path))


def main() -> None:
  resume = load_resume()
  html = render_resume_html(resume)

  # Also save HTML for quick inspection / debugging
  OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
  html_path = OUTPUT_DIR / "resume.html"
  pdf_path = OUTPUT_DIR / "resume.pdf"

  html_path.write_text(html, encoding="utf-8")
  generate_pdf(html, pdf_path)

  print(f"Generated HTML: {html_path}")
  print(f"Generated PDF: {pdf_path}")


if __name__ == "__main__":
  main()

