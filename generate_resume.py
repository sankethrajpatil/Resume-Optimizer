from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


BASE_DIR = Path(__file__).parent
DATA_PATH = BASE_DIR / "data" / "base_resume.json"
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"

# Rule: Every bullet/line on the resume must be ≤ this many characters (incl. spaces and bullet spacing).
# When truncating, the result must be a complete sentence (cut at sentence end, then clause, then word).
BULLET_MAX_CHARS = 120


def truncate_to_chars(s: str, max_chars: int = BULLET_MAX_CHARS) -> str:
  """Truncate to at most max_chars, keeping a complete sentence. Prefer last . ! ? then , then space."""
  if not s or len(s) <= max_chars:
    return s
  segment = s[: max_chars + 1]
  # Prefer last sentence end before limit so the line stays complete
  last_sent_end = -1
  for sep in ".!?":
    idx = segment.rfind(sep)
    if idx > 0 and idx > last_sent_end:
      last_sent_end = idx
  if last_sent_end > 0:
    return segment[: last_sent_end + 1].strip()
  # Then clause boundary
  idx = segment.rfind(",")
  if idx > 0:
    return segment[: idx + 1].strip()
  # Then word boundary
  last_space = segment.rfind(" ")
  if last_space > 0:
    return segment[:last_space].rstrip()
  return segment[:max_chars].rstrip()


def load_resume() -> dict:
  """Load base resume data from JSON."""
  with DATA_PATH.open(encoding="utf-8") as f:
    return json.load(f)


def render_resume_html(resume: dict, for_pdf: bool = False) -> str:
  """Render resume HTML. Use for_pdf=True to get PDF-safe layout (tables, no flexbox)."""
  env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"]),
    trim_blocks=True,
    lstrip_blocks=True,
  )
  env.filters["truncate_bullet"] = lambda s: truncate_to_chars(s or "", BULLET_MAX_CHARS)
  template_name = "resume_pdf.html" if for_pdf else "resume.html"
  template = env.get_template(template_name)
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

