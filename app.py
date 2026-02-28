"""FastAPI app: JD extraction, analysis, and static frontend."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

import jd_analyzer
import jd_extractor
import openai_client
import resume_generator
import resume_screener

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
    return jd_analyzer.job_analysis_to_dict(analysis)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except openai_client.OpenAIConfigError as e:
    raise HTTPException(status_code=503, detail=str(e))
  except Exception as e:
    raise HTTPException(status_code=502, detail=f"Analysis failed: {str(e)}")


class ResumeScreenRequest(BaseModel):
  text: str


@app.post("/api/resume/screen")
def api_resume_screen(body: ResumeScreenRequest) -> dict:
  """Screen resume projects against the JD; return selected projects, rewritten bullets, gaps."""
  text = (body.text or "").strip()
  if not text:
    raise HTTPException(status_code=400, detail="Job description text is required.")
  try:
    return resume_screener.screen_resume(text)
  except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
  except openai_client.OpenAIConfigError as e:
    raise HTTPException(status_code=503, detail=str(e))
  except Exception as e:
    raise HTTPException(status_code=502, detail=f"Screening failed: {str(e)}")


class GenerateResumeRequest(BaseModel):
  screening_result: dict | None = None


@app.post("/api/resume/generate")
def api_resume_generate(body: GenerateResumeRequest) -> dict:
  """Generate resume HTML from base resume + optional screening result (tailored projects)."""
  try:
    html = resume_generator.generate_resume_html(body.screening_result)
    return {"html": html}
  except Exception as e:
    raise HTTPException(status_code=502, detail=f"Generate failed: {str(e)}")


@app.post("/api/resume/download")
def api_resume_download(body: GenerateResumeRequest) -> Response:
  """Generate resume PDF and return as file download. Uses PDF-optimized template (table layout, single page)."""
  try:
    html = resume_generator.generate_resume_html(body.screening_result, for_pdf=True)
    pdf_bytes = resume_generator.generate_resume_pdf_bytes(html)
  except Exception as e:
    if "weasyprint" in str(e).lower() or "libgobject" in str(e).lower() or "load library" in str(e).lower():
      raise HTTPException(
        status_code=503,
        detail="PDF generation is not available on this server. Use 'Generate resume' and print the preview to PDF.",
      ) from e
    raise HTTPException(status_code=502, detail=f"Download failed: {str(e)}") from e
  return Response(
    content=pdf_bytes,
    media_type="application/pdf",
    headers={"Content-Disposition": "attachment; filename=resume.pdf"},
  )


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
