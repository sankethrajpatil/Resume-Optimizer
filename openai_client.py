from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


class OpenAIConfigError(RuntimeError):
  """Raised when OpenAI configuration (e.g., API key) is missing."""


_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
  """Get a singleton OpenAI client instance."""
  global _client

  if _client is None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
      raise OpenAIConfigError(
        "OPENAI_API_KEY environment variable is not set. "
        "Set it in your environment or in a .env file."
      )
    _client = OpenAI(api_key=api_key)

  return _client


def chat_json(
  system_prompt: str,
  user_prompt: str,
  *,
  model: Optional[str] = None,
  temperature: float = 0.1,
) -> Dict[str, Any]:
  """Call OpenAI chat completion API and parse a JSON object response.

  The model is expected to return a single JSON object as the message content.
  """
  client = get_client()

  response = client.chat.completions.create(
    model=model or os.getenv("OPENAI_MODEL", "gpt-4o"),
    response_format={"type": "json_object"},
    temperature=temperature,
    messages=[
      {"role": "system", "content": system_prompt},
      {"role": "user", "content": user_prompt},
    ],
  )

  content = response.choices[0].message.content
  if content is None:
    raise RuntimeError("OpenAI response had empty content.")

  try:
    return json.loads(content)
  except json.JSONDecodeError as exc:
    raise RuntimeError(f"Failed to parse JSON from OpenAI response: {content!r}") from exc

