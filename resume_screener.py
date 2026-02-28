"""Resume screening: match projects to JD and get tailored bullets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import openai_client

BASE_DIR = Path(__file__).parent
PROJECTS_CATALOG_PATH = BASE_DIR / "data" / "projects_catalog.json"

SCREENING_SYSTEM = (
  "You are a hiring manager screening resumes. "
  "You select which projects best match the role, explain why, suggest removals, identify gaps, "
  "and tailor project bullets by replacing only keywords with terms from the JD while keeping metrics and accomplishments. "
  "Respond with a single JSON object ONLY, no extra commentary. "
  "Think: if you saw this resume, would you interview the person?"
)

SCREENING_USER_TEMPLATE = """I will give you:
1) A job description
2) A list of my projects and experiences

Your task:

- Select which projects best match the role.
- Explain WHY each one fits using the employer's needs.
- Suggest which projects should be removed.
- Identify missing signals or gaps.
- For each selected project, produce exactly 2 resume bullets. Do NOT rewrite the whole bullet. Only replace keywords/phrases with equivalent terms from the job description. Keep the original accomplishment, structure, and especially the METRICS (numbers, percentages, time saved, etc.). Metrics are compulsory in every bullet—if the original has none, add one plausible metric that fits the accomplishment.

Rules for every bullet you write:
- Each bullet must include at least one metric (%, number, or concrete outcome). Metrics are mandatory.
- Only swap in JD keywords/terminology; preserve the original meaning and accomplishment.
- Each bullet must be ONE complete sentence (do not cut mid-sentence).
- Hard limit: each bullet must be ≤ 120 characters including spaces. Count characters and stay under 120.
- One line only; no overflow to the next line. Concise, high-impact phrasing.

Return a JSON object with:
- selected_projects: array of objects, each with: project_id, project_title, why_it_fits (string), rewritten_bullets (array of exactly 2 strings, each with metrics, keywords aligned to JD, ≤120 characters)
- remove_projects: array of objects with project_id, project_title, reason (string)
- gaps: array of strings (missing signals or gaps)
- interview_verdict: string (one short sentence: would you interview this person and why/why not)

JOB DESCRIPTION:
\"\"\"
{jd_text}
\"\"\"

MY PROJECTS (JSON array):
{projects_json}
"""


def _load_projects() -> List[Dict[str, Any]]:
  with PROJECTS_CATALOG_PATH.open(encoding="utf-8") as f:
    return json.load(f)


def _projects_for_prompt(projects: List[Dict[str, Any]]) -> str:
  """Format projects for the prompt: id, title, stack, bullets, tags."""
  out = []
  for p in projects:
    entry = {
      "id": p.get("id", ""),
      "title": p.get("title", ""),
      "stack": p.get("stack", []),
      "bullets": p.get("bullets", []),
      "tags": p.get("tags", []),
    }
    out.append(entry)
  return json.dumps(out, indent=2)


def screen_resume(jd_text: str) -> Dict[str, Any]:
  """Run resume screening: match projects to JD, return selected + rewritten bullets + gaps."""
  jd_text = jd_text.strip()
  if not jd_text:
    raise ValueError("Job description text is required for screening.")

  projects = _load_projects()
  projects_json = _projects_for_prompt(projects)

  user_prompt = SCREENING_USER_TEMPLATE.format(
    jd_text=jd_text,
    projects_json=projects_json,
  )
  data = openai_client.chat_json(SCREENING_SYSTEM, user_prompt)

  # Normalize response
  selected = data.get("selected_projects") or []
  remove = data.get("remove_projects") or []
  gaps = data.get("gaps") or []
  if isinstance(gaps, list):
    gaps = [str(g).strip() for g in gaps if str(g).strip()]
  else:
    gaps = [str(gaps).strip()] if str(gaps).strip() else []

  verdict = str(data.get("interview_verdict", "")).strip()

  return {
    "selected_projects": selected,
    "remove_projects": remove,
    "gaps": gaps,
    "interview_verdict": verdict,
  }
