import pytest

import jd_analyzer
import openai_client


def test_analyze_job_description_shapes_data(monkeypatch):
  # Arrange: stub OpenAI response.
  sample_response = {
    "role_title": "Senior Product Manager - AI Platform",
    "seniority_level": "Senior",
    "location": "Remote, US",
    "employment_type": "Full-time",
    "required_skills": ["Product management", "AI/ML", "Roadmapping"],
    "preferred_skills": ["SQL", "Experimentation"],
    "primary_responsibilities": [
      "Own the roadmap for AI platform features.",
      "Collaborate with data science and engineering.",
    ],
    "keywords_technical": ["Python", "ML", "LLMs"],
    "keywords_tools": ["JIRA", "Figma"],
    "keywords_domains": ["SaaS", "AI platforms"],
    "keywords_methodologies": ["A/B testing", "Agile"],
    "keywords_certifications": ["CSPO"],
  }

  def fake_chat_json(system_prompt: str, user_prompt: str, **kwargs):
    return sample_response

  monkeypatch.setattr(openai_client, "chat_json", fake_chat_json)

  # Act
  jd_text = "We are hiring a Senior Product Manager for our AI platform..."
  analysis = jd_analyzer.analyze_job_description(jd_text)

  # Assert: fields should be mapped correctly.
  assert analysis.role_title == "Senior Product Manager - AI Platform"
  assert analysis.seniority_level == "Senior"
  assert analysis.location == "Remote, US"
  assert "Product management" in analysis.required_skills
  assert "A/B testing" in analysis.keywords_methodologies


def test_analyze_job_description_empty_text_raises():
  with pytest.raises(ValueError, match="empty"):
    jd_analyzer.analyze_job_description("   ")

