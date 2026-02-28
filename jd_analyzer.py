"""Job description analysis using the recruiter-style prompt."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import openai_client

JD_ANALYSIS_SYSTEM = (
  "You are an expert technical recruiter and hiring manager. "
  "You decode the signal behind the words in job descriptions. "
  "Respond with a single JSON object ONLY, no extra commentary. "
  "Be precise. Avoid generic advice. Think like someone who must decide in 10 seconds whether to interview."
)

JD_ANALYSIS_USER_TEMPLATE = """I will paste a job description.
Your task is to decode the signal behind the words.

Return a JSON object with exactly these fields (all arrays of strings unless noted):
1) top_skills - hard skills / tools / methods
2) core_competencies - behaviors, ways of working
3) primary_problems - primary problems the team is trying to solve
4) metrics_outcomes - metrics or outcomes they care about
5) seniority_signals - ownership level, autonomy, stakeholder scope
6) hidden_ats_keywords - keywords that ATS systems will likely search for
7) perfect_candidate_signals - what a perfect candidate probably did in past roles
8) keyword_rankings - an object with three arrays: "critical", "important", "nice_to_have" (ranked by importance)

Be precise. Avoid generic advice.

JOB DESCRIPTION:
\"\"\"
{jd_text}
\"\"\"
"""


@dataclass
class KeywordRankings:
  critical: List[str] = field(default_factory=list)
  important: List[str] = field(default_factory=list)
  nice_to_have: List[str] = field(default_factory=list)


@dataclass
class JobAnalysis:
  top_skills: List[str]
  core_competencies: List[str]
  primary_problems: List[str]
  metrics_outcomes: List[str]
  seniority_signals: List[str]
  hidden_ats_keywords: List[str]
  perfect_candidate_signals: List[str]
  keyword_rankings: KeywordRankings


def _list(value: Any) -> List[str]:
  if not value:
    return []
  if isinstance(value, list):
    return [str(v).strip() for v in value if str(v).strip()]
  if isinstance(value, str) and value.strip():
    return [value.strip()]
  return []


def _rankings(value: Any) -> KeywordRankings:
  if not isinstance(value, dict):
    return KeywordRankings()
  return KeywordRankings(
    critical=_list(value.get("critical")),
    important=_list(value.get("important")),
    nice_to_have=_list(value.get("nice_to_have")),
  )


def analyze_job_description(jd_text: str) -> JobAnalysis:
  """Analyze raw JD text using the recruiter-style prompt."""
  jd_text = jd_text.strip()
  if not jd_text:
    raise ValueError("Job description text is empty.")

  user_prompt = JD_ANALYSIS_USER_TEMPLATE.format(jd_text=jd_text)
  data = openai_client.chat_json(JD_ANALYSIS_SYSTEM, user_prompt)

  return JobAnalysis(
    top_skills=_list(data.get("top_skills")),
    core_competencies=_list(data.get("core_competencies")),
    primary_problems=_list(data.get("primary_problems")),
    metrics_outcomes=_list(data.get("metrics_outcomes")),
    seniority_signals=_list(data.get("seniority_signals")),
    hidden_ats_keywords=_list(data.get("hidden_ats_keywords")),
    perfect_candidate_signals=_list(data.get("perfect_candidate_signals")),
    keyword_rankings=_rankings(data.get("keyword_rankings")),
  )


def job_analysis_to_dict(a: JobAnalysis) -> Dict[str, Any]:
  """Serialize for API/JSON."""
  return {
    "top_skills": a.top_skills,
    "core_competencies": a.core_competencies,
    "primary_problems": a.primary_problems,
    "metrics_outcomes": a.metrics_outcomes,
    "seniority_signals": a.seniority_signals,
    "hidden_ats_keywords": a.hidden_ats_keywords,
    "perfect_candidate_signals": a.perfect_candidate_signals,
    "keyword_rankings": {
      "critical": a.keyword_rankings.critical,
      "important": a.keyword_rankings.important,
      "nice_to_have": a.keyword_rankings.nice_to_have,
    },
  }
