import re
from urllib.parse import urlparse

ALLOWED_DOMAINS = [
    "langchain-ai.github.io",
    "python.langchain.com",
    "docs.smith.langchain.com",
]


def extract_links(markdown: str) -> list[tuple]:
    """Extract all URLs from markdown link syntax [text](url)."""
    pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    matches = re.findall(pattern, markdown)
    return [(text, url) for text, url in matches]


def filter_allowed_links(links: list[tuple]) -> list[tuple]:
    """Keep only links from allowed LangChain domains."""
    allowed = []
    for text, url in links:
        domain = urlparse(url).netloc
        if any(domain == d or domain.endswith("." + d) for d in ALLOWED_DOMAINS):
            allowed.append((text, url))
    return allowed


def score_links_by_query(links: list[tuple], query: str) -> list[tuple]:
    """Score links by keyword overlap with the user query. Returns sorted list."""
    query_words = set(query.lower().split())
    scored = []
    for text, url in links:
        link_words = set(text.lower().replace("-", " ").split())
        path_words = set(url.lower().replace("/", " ").replace("-", " ").split())
        overlap = len(query_words & (link_words | path_words))
        scored.append((overlap, text, url))
    scored.sort(reverse=True)
    return [(text, url) for _, text, url in scored]


def get_links_to_resolve(markdown: str, query: str, max_links: int = 2) -> list[str]:
    """Extract, filter, score, and return top N URLs to follow."""
    all_links = extract_links(markdown)
    allowed = filter_allowed_links(all_links)
    scored = score_links_by_query(allowed, query)
    seen = set()
    result = []
    for text, url in scored:
        if url not in seen and len(result) < max_links:
            seen.add(url)
            result.append(url)
    return result
