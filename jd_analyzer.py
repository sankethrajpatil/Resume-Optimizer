from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import openai_client


@dataclass
class JobAnalysis:
  """Structured representation of a job description."""

  role_title: str
  seniority_level: Optional[str]
  location: Optional[str]
  employment_type: Optional[str]
  required_skills: List[str]
  preferred_skills: List[str]
  primary_responsibilities: List[str]
  keywords_technical: List[str]
  keywords_tools: List[str]
  keywords_domains: List[str]
  keywords_methodologies: List[str]
  keywords_certifications: List[str]


def analyze_job_description(jd_text: str) -> JobAnalysis:
  """Analyze raw JD text using OpenAI and return structured information.

  This is used when the user pastes a job description directly.
  """
  jd_text = jd_text.strip()
  if not jd_text:
    raise ValueError("Job description text is empty.")

  system_prompt = (
    "You are an assistant that analyzes job descriptions and returns a clean, "
    "JSON-structured summary for resume optimization and ATS alignment.\n\n"
    "Respond with a single JSON object ONLY, no extra commentary."
  )

  user_prompt = f"""
Analyze the following job description and extract structured information
useful for tailoring a resume.

Return a JSON object with exactly these fields:
- role_title: string
- seniority_level: string or null (e.g., 'Junior', 'Mid', 'Senior', 'Lead', 'Director')
- location: string or null
- employment_type: string or null (e.g., 'Full-time', 'Internship', 'Contract')
- required_skills: array of strings
- preferred_skills: array of strings
- primary_responsibilities: array of concise bullet-style strings
- keywords_technical: array of strings (technical skills, programming languages, data tools, etc.)
- keywords_tools: array of strings (named tools, platforms, SaaS products)
- keywords_domains: array of strings (domains/industries like 'healthcare', 'fintech', 'e-commerce')
- keywords_methodologies: array of strings (e.g., 'A/B testing', 'Agile', 'Scrum', 'RAG', 'LLMOps')
- keywords_certifications: array of strings (certifications or formal qualifications if mentioned)

JOB DESCRIPTION:
\"\"\"{jd_text}\"\"\"
"""

  data = openai_client.chat_json(system_prompt, user_prompt)

  # Safely pull fields with sensible defaults.
  def _list(field: str) -> list[str]:
    value = data.get(field) or []
    if isinstance(value, list):
      return [str(v).strip() for v in value if str(v).strip()]
    # If the model returned a string accidentally, wrap it.
    if isinstance(value, str) and value.strip():
      return [value.strip()]
    return []

  return JobAnalysis(
    role_title=str(data.get("role_title", "")).strip(),
    seniority_level=(str(data["seniority_level"]).strip() if data.get("seniority_level") not in (None, "") else None),
    location=(str(data["location"]).strip() if data.get("location") not in (None, "") else None),
    employment_type=(str(data["employment_type"]).strip() if data.get("employment_type") not in (None, "") else None),
    required_skills=_list("required_skills"),
    preferred_skills=_list("preferred_skills"),
    primary_responsibilities=_list("primary_responsibilities"),
    keywords_technical=_list("keywords_technical"),
    keywords_tools=_list("keywords_tools"),
    keywords_domains=_list("keywords_domains"),
    keywords_methodologies=_list("keywords_methodologies"),
    keywords_certifications=_list("keywords_certifications"),
  )

