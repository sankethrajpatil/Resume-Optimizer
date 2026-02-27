import os

import pytest

import openai_client


def test_get_client_raises_when_api_key_missing(monkeypatch):
  monkeypatch.setattr(openai_client, "_client", None)

  def no_api_key(key, default=None):
    if key == "OPENAI_API_KEY":
      return None
    return os.environ.get(key, default)

  monkeypatch.setattr(openai_client.os, "getenv", no_api_key)

  with pytest.raises(openai_client.OpenAIConfigError, match="OPENAI_API_KEY"):
    openai_client.get_client()
