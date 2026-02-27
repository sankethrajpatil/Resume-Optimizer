from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import generate_resume


def test_load_resume_has_core_fields():
  resume = generate_resume.load_resume()

  assert isinstance(resume, dict)
  assert resume["name"] == "Sanketh Rajshekhar Patil"
  assert "education" in resume and len(resume["education"]) > 0
  assert "skills" in resume and "data_and_analytics" in resume["skills"]
  assert "experience" in resume and len(resume["experience"]) > 0


def test_render_resume_contains_name_and_sections():
  resume = generate_resume.load_resume()
  html = generate_resume.render_resume_html(resume)

  # Basic sanity checks on rendered HTML
  assert "Sanketh Rajshekhar Patil" in html
  assert "Education" in html
  assert "Skills" in html
  assert "Professional Experience" in html
  assert "Projects" in html
  assert "Awards" in html and "Leadership" in html


def test_generate_pdf_creates_non_empty_file():
  try:
    from weasyprint import HTML  # noqa: F401
  except OSError:
    pytest.skip("WeasyPrint system libraries (e.g. GTK) not available")

  resume = generate_resume.load_resume()
  html = generate_resume.render_resume_html(resume)

  with TemporaryDirectory() as tmpdir:
    pdf_path = Path(tmpdir) / "resume.pdf"

    generate_resume.generate_pdf(html, pdf_path)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0

