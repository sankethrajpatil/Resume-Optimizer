import pytest

import jd_analyzer
import openai_client


def test_analyze_job_description_shapes_data(monkeypatch):
  sample_response = {
    "top_skills": ["Product management", "AI/ML", "Roadmapping"],
    "core_competencies": ["Stakeholder alignment", "Cross-functional collaboration"],
    "primary_problems": ["Scale AI platform adoption"],
    "metrics_outcomes": ["DAU", "Conversion rate"],
    "seniority_signals": ["Own roadmap", "Lead cross-team initiatives"],
    "hidden_ats_keywords": ["Python", "SQL", "A/B testing"],
    "perfect_candidate_signals": ["Shipped 0→1 AI products", "Led discovery research"],
    "keyword_rankings": {
      "critical": ["Product management", "AI/ML"],
      "important": ["SQL", "Experimentation"],
      "nice_to_have": ["CSPO"],
    },
  }

  def fake_chat_json(system_prompt: str, user_prompt: str, **kwargs):
    return sample_response

  monkeypatch.setattr(openai_client, "chat_json", fake_chat_json)

  analysis = jd_analyzer.analyze_job_description("We are hiring a Senior PM...")

  assert "Product management" in analysis.top_skills
  assert "Stakeholder alignment" in analysis.core_competencies
  assert analysis.keyword_rankings.critical == ["Product management", "AI/ML"]
  assert analysis.keyword_rankings.important == ["SQL", "Experimentation"]

  out = jd_analyzer.job_analysis_to_dict(analysis)
  assert out["top_skills"] == analysis.top_skills
  assert out["keyword_rankings"]["critical"] == analysis.keyword_rankings.critical


def test_analyze_job_description_empty_text_raises():
  with pytest.raises(ValueError, match="empty"):
    jd_analyzer.analyze_job_description("   ")
