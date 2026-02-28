"""Tests for FastAPI app."""
import pytest
from fastapi.testclient import TestClient

from app import app

client = TestClient(app)


def test_index_returns_html():
  r = client.get("/")
  assert r.status_code == 200
  assert "text/html" in r.headers.get("content-type", "")
  assert "Resume Optimizer" in r.text


def test_jd_from_url_requires_body():
  r = client.post("/api/jd/from-url", json={})
  assert r.status_code == 422


def test_jd_from_url_rejects_empty_url():
  r = client.post("/api/jd/from-url", json={"url": "   "})
  assert r.status_code == 400


def test_jd_analyze_requires_body():
  r = client.post("/api/jd/analyze", json={})
  assert r.status_code == 422


def test_jd_analyze_rejects_empty_text():
  r = client.post("/api/jd/analyze", json={"text": "   "})
  assert r.status_code == 400


def test_resume_generate_returns_html():
  r = client.post("/api/resume/generate", json={"screening_result": None})
  assert r.status_code == 200
  data = r.json()
  assert "html" in data
  assert "Sanketh" in data["html"]
