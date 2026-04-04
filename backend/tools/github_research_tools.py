import asyncio
import base64
import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from backend.agents.state import EvidenceItem
from backend.config import settings

GITHUB_REPO_URL_RE = re.compile(
    r"github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)"
)
GITHUB_REPO_SLUG_RE = re.compile(
    r"\b(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+)\b"
)


def _get_json(url: str, headers: dict[str, str]) -> dict[str, Any]:
    request = Request(url, headers=headers, method="GET")
    with urlopen(request, timeout=20) as response:
        return json.loads(response.read().decode("utf-8"))


def _build_headers(runtime_keys: dict[str, str] | None = None) -> dict[str, str]:
    token = (runtime_keys or {}).get("github_token") or settings.github_token
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AI-Canvas",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _decode_readme(payload: dict[str, Any]) -> str:
    content = str(payload.get("content", ""))
    encoding = str(payload.get("encoding", ""))
    if encoding == "base64" and content:
        try:
            return base64.b64decode(content).decode("utf-8", errors="ignore")
        except Exception:
            return ""
    return content


def detect_github_repo(query: str) -> tuple[str, str] | None:
    url_match = GITHUB_REPO_URL_RE.search(query)
    if url_match:
        return url_match.group("owner"), url_match.group("repo").removesuffix(".git")

    lowered = query.lower()
    if "github" not in lowered and "repo" not in lowered and "repository" not in lowered:
        return None

    slug_match = GITHUB_REPO_SLUG_RE.search(query)
    if slug_match:
        return slug_match.group("owner"), slug_match.group("repo")
    return None


async def get_github_repo_evidence(
    query: str,
    runtime_keys: dict[str, str] | None = None,
) -> list[EvidenceItem]:
    repo_ref = detect_github_repo(query)
    if not repo_ref:
        return []

    owner, repo = repo_ref
    headers = _build_headers(runtime_keys)
    repo_url = f"{settings.github_api_base_url.rstrip('/')}/repos/{quote(owner)}/{quote(repo)}"
    readme_url = f"{repo_url}/readme"

    try:
        repo_payload = await asyncio.to_thread(_get_json, repo_url, headers)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return []

    readme_text = ""
    try:
        readme_payload = await asyncio.to_thread(_get_json, readme_url, headers)
        readme_text = _decode_readme(readme_payload)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        readme_text = ""

    summary_lines = [
        f"Repository: {repo_payload.get('full_name', f'{owner}/{repo}')}",
        f"Description: {repo_payload.get('description', '')}",
        f"Primary language: {repo_payload.get('language', '')}",
        f"Default branch: {repo_payload.get('default_branch', '')}",
        f"Stars: {repo_payload.get('stargazers_count', '')}",
        f"Topics: {', '.join(repo_payload.get('topics', []) or [])}",
    ]
    content = "\n".join(line for line in summary_lines if line.strip())
    if readme_text:
        content = f"{content}\n\nREADME:\n{readme_text[:7000]}"

    html_url = str(repo_payload.get("html_url", f"https://github.com/{owner}/{repo}"))
    return [
        {
            "title": str(repo_payload.get("full_name", f"{owner}/{repo}")),
            "url": html_url,
            "content": content,
            "source_type": "github",
        }
    ]
