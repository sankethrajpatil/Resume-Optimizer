from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

import jd_extractor


def test_extract_title_prefers_h1_over_title():
  html = """
  <html>
    <head><title>Company Careers</title></head>
    <body>
      <h1>Senior Product Manager - AI Platform</h1>
      <p>Some job description text here.</p>
    </body>
  </html>
  """
  soup = BeautifulSoup(html, "html.parser")
  title = jd_extractor._extract_title(soup)

  assert title == "Senior Product Manager - AI Platform"


def test_extract_main_text_filters_boilerplate():
  html = """
  <html>
    <body>
      <nav>Sign in | Create Account</nav>
      <p>At ACME, we are looking for a Senior Data Scientist.</p>
      <p>Responsibilities include building models and collaborating with product.</p>
      <p>Read our privacy policy and terms of use.</p>
      <ul>
        <li>3+ years of experience with Python</li>
        <li>Experience with SQL and ML frameworks</li>
      </ul>
    </body>
  </html>
  """
  soup = BeautifulSoup(html, "html.parser")
  text = jd_extractor._extract_main_text(soup)

  # Boilerplate should be removed, core JD content should remain.
  assert "Senior Data Scientist" in text
  assert "3+ years of experience with Python" in text
  assert "privacy policy" not in text.lower()
  assert "sign in" not in text.lower()


def test_fetch_job_description_returns_title_and_text(monkeypatch):
  html = """
  <html>
    <head><title>Careers</title></head>
    <body>
      <h1>Senior Data Engineer</h1>
      <p>We are looking for someone with Python and Spark experience.</p>
      <ul><li>5+ years of experience</li></ul>
    </body>
  </html>
  """
  mock_response = MagicMock()
  mock_response.status_code = 200
  mock_response.text = html

  monkeypatch.setattr(jd_extractor.requests, "get", lambda *a, **k: mock_response)

  jd = jd_extractor.fetch_job_description("https://example.com/job/123")

  assert jd.url == "https://example.com/job/123"
  assert jd.title == "Senior Data Engineer"
  assert "Python" in jd.text and "Spark" in jd.text
  assert "5+ years" in jd.text


def test_fetch_job_description_invalid_url_raises():
  with pytest.raises(jd_extractor.JobDescriptionError, match="Invalid URL"):
    jd_extractor.fetch_job_description("not-a-url")

