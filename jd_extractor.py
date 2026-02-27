from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


USER_AGENT = (
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
  "AppleWebKit/537.36 (KHTML, like Gecko) "
  "Chrome/120.0 Safari/537.36"
)


@dataclass
class JobDescription:
  url: str
  title: str
  text: str


class JobDescriptionError(Exception):
  """Raised when a job description cannot be fetched or parsed."""


def _validate_url(url: str) -> None:
  parsed = urlparse(url)
  if not parsed.scheme or not parsed.netloc:
    raise JobDescriptionError(f"Invalid URL: {url!r}")


def _extract_title(soup: BeautifulSoup) -> str:
  """Try to extract a meaningful job title."""
  # Prefer h1 tags, which many job sites use for role titles.
  h1 = soup.find("h1")
  if h1 and h1.get_text(strip=True):
    return h1.get_text(strip=True)

  # Fallback to the document title tag.
  if soup.title and soup.title.get_text(strip=True):
    return soup.title.get_text(strip=True)

  return ""


def _extract_main_text(soup: BeautifulSoup) -> str:
  """Extract main textual JD content from HTML.

  Heuristics:
  - Remove script/style/nav/footer tags.
  - Join remaining paragraph- and list-like text into a single block.
  """
  for tag_name in ["script", "style", "nav", "header", "footer", "noscript"]:
    for tag in soup.find_all(tag_name):
      tag.decompose()

  texts = []
  # Common containers for job descriptions: div, section, article, li, p
  for elem in soup.find_all(["p", "li"]):
    text = elem.get_text(" ", strip=True)
    if not text:
      continue

    # Filter out obvious boilerplate.
    lowered = text.lower()
    if any(
      phrase in lowered
      for phrase in [
        "cookies",
        "privacy policy",
        "terms of use",
        "sign in",
        "create account",
      ]
    ):
      continue

    texts.append(text)

  # Deduplicate consecutive lines and join with newlines.
  deduped: list[str] = []
  for t in texts:
    if not deduped or deduped[-1] != t:
      deduped.append(t)

  return "\n".join(deduped)


def fetch_job_description(url: str, timeout: float = 15.0) -> JobDescription:
  """Fetch a job description page and extract title + text.

  This will be the first step after the user pastes a JD link.
  """
  _validate_url(url)

  try:
    response = requests.get(
      url,
      headers={"User-Agent": USER_AGENT},
      timeout=timeout,
    )
  except requests.RequestException as exc:
    raise JobDescriptionError(f"Failed to fetch URL: {exc}") from exc

  if not (200 <= response.status_code < 300):
    raise JobDescriptionError(
      f"Non-success status code {response.status_code} for URL {url!r}"
    )

  soup = BeautifulSoup(response.text, "html.parser")
  title = _extract_title(soup)
  text = _extract_main_text(soup)

  if not text.strip():
    raise JobDescriptionError("Could not extract any job description text.")

  return JobDescription(url=url, title=title, text=text)

