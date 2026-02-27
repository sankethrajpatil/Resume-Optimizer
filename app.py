"""FastAPI app: JD extraction, analysis, and static frontend."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

import jd_analyzer
import jd_extractor

app = FastAPI(title="Resume Optimizer", version="0.1.0")

STATIC_DIR = Path(__file__).parent / "static"

app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)


# ----- API request/response models -----


class JdFromUrlRequest(BaseModel):
  url: str


class JdAnalyzeRequest(BaseModel):
  text: str


def _job_analysis_to_dict(a: jd_analyzer.JobAnalysis) -> dict:
  return {
    "role_title": a.role_title,
    "seniority_level": a.seniority_level,
    "location": a.location,
    "employment_type": a.employment_type,
    "required_skills": a.required_skills,
    "preferred_skills": a.preferred_skills,
    "primary_responsibilities": a.primary_responsibilities,
    "keywords_technical": a.keywords_technical,
    "keywords_tools": a.keywords_tools,
    "keywords_domains": a.keywords_domains,
    "keywords_methodologies": a.keywords_methodologies,
    "keywords_certifications": a.keywords_certifications,
  }


# ----- API routes -----


@app.post("/api/jd/from-url")
def api_jd_from_url(body: JdFromUrlRequest) -> dict:
  """Fetch job description from a URL and return title + extracted text."""
  url = (body.url or "").strip()
  if not url:
    raise HTTPException(status_code=400, detail="URL is required.")
  try:
    jd = jd_extractor.fetch_job_description(url)
    return {"url": jd.url, "title": jd.title, "text": jd.text}
  except jd_extractor.JobDescriptionError as e:
    raise HTTPException(status_code=422, detail=str(e))


@app.post("/api/jd/analyze")
def api_jd_analyze(body: JdAnalyzeRequest) -> dict:
  """Analyze pasted JD text and return structured fields (skills, keywords, etc.)."""
  text = (body.text or "").strip()
  if not text:
    raise HTTPException(status_code=400, detail="Job description text is required.")
  try:
    analysis = jd_analyzer.analyze_job_description(text)
    return _job_analysis_to_dict(analysis)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))


# ----- Frontend -----


@app.get("/")
def index():
  """Serve the single-page frontend."""
  path = STATIC_DIR / "index.html"
  if not path.exists():
    raise HTTPException(status_code=404, detail="Frontend not found.")
  return FileResponse(path)


@app.get("/static/{path:path}")
def static_file(path: str):
  """Serve static assets (CSS, JS, etc.)."""
  file_path = STATIC_DIR / path
  if not file_path.is_file():
    raise HTTPException(status_code=404)
  return FileResponse(file_path)
