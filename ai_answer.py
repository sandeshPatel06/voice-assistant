"""
Free AI answering — no API keys or authentication required.

Supported backends (tried in order; first hit wins):

1. **DuckDuckGo Instant Answer API**  (``https://api.duckduckgo.com``)
   – Returns curated topic answers, definitions, etc.

2. **Wikipedia** – Searches and returns a summary extract.

3. **Ollama** – Queries a local LLM (e.g. llama3, mistral).
   Requires Ollama to be running locally (``ollama serve``).
   No API key needed.

4. **DuckDuckGo HTML search** – Falls back to scraping search results
   when none of the above provide a direct answer.
"""

import html
import logging
import re
from typing import Optional

import requests

from config import AI_BACKENDS, OLLAMA_MODEL, OLLAMA_BASE_URL

log = logging.getLogger("jarvis.ai_answer")

DDG_INSTANT_URL = "https://api.duckduckgo.com/"
DDG_HTML_URL = "https://html.duckduckgo.com/html/"
REQUEST_TIMEOUT = 10


class AIAnswer:
    """Answer free-form questions using free, key-less services."""

    def __init__(self, backends: Optional[list[str]] = None) -> None:
        self.backends = backends or AI_BACKENDS
        # Track backends that have permanently failed (e.g. missing deps)
        # so we don't keep retrying them on every question.
        self._permanently_disabled: set[str] = set()

    # ── Public API ──────────────────────────────────────────────────
    def answer(self, query: str) -> str:
        """Return an answer string for *query*, trying every backend."""
        for backend in self.backends:
            if backend in self._permanently_disabled:
                continue
            try:
                method = getattr(self, f"_query_{backend}")
            except AttributeError:
                log.warning("Unknown backend %s, skipping", backend)
                self._permanently_disabled.add(backend)
                continue

            # Each backend call is isolated — failures don't affect others.
            try:
                answer = method(query)
            except requests.exceptions.ConnectionError:
                log.debug("Backend '%s' unreachable (connection error)", backend)
                continue
            except requests.exceptions.Timeout:
                log.debug("Backend '%s' timed out", backend)
                continue
            except Exception:
                log.debug("Backend '%s' failed unexpectedly", backend, exc_info=True)
                continue

            if answer and answer.strip():
                return f"According to {backend}: {answer}"

        return "I'm sorry, I couldn't find an answer to that."

    # ── Backend 1: DuckDuckGo Instant Answer ─────────────────────────
    def _query_duckduckgo(self, query: str) -> str:
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "no_redirect": "1",
            "skip_disambig": "1",
            "l": "en_US",
        }
        resp = requests.get(DDG_INSTANT_URL, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        try:
            data = resp.json()
        except (ValueError, requests.exceptions.JSONDecodeError):
            # DDG sometimes returns HTML instead of JSON
            return ""

        # Direct abstract answer
        abstract = data.get("AbstractText", "").strip()
        if abstract:
            return abstract

        # Topic answer from RelatedTopics
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict):
                text = topic.get("Text", "").strip()
                if text:
                    return text

        return ""

    # ── Backend 2: Wikipedia ─────────────────────────────────────────
    _WIKI_API_URL = "https://en.wikipedia.org/w/api.php"
    _WIKI_SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
    _WIKI_HEADERS = {
        "User-Agent": "JarvisAI/1.0 (personal voice assistant; not a bot)"
    }

    # Words to strip before searching Wikipedia (prevents disambiguation noise)
    _QUESTION_WORDS = re.compile(
        r"^(who is|who are|what is|what are|where is|where are|when is|when are|"
        r"why is|why are|how is|how are|define|definition of|tell me about|explain)",
        re.I,
    )

    def _clean_wiki_query(self, query: str) -> str:
        """Remove leading question words so Wikipedia returns the right page."""
        return self._QUESTION_WORDS.sub("", query).strip()

    def _query_wikipedia(self, query: str) -> str:
        """Fetch a Wikipedia article summary via the REST API with proper UA."""
        search_term = self._clean_wiki_query(query) or query

        try:
            # Step 1: search for the page title
            search_resp = requests.get(
                self._WIKI_API_URL,
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": search_term,
                    "srlimit": 3,
                    "format": "json",
                },
                headers=self._WIKI_HEADERS,
                timeout=REQUEST_TIMEOUT,
            )
            search_resp.raise_for_status()
            search_data = search_resp.json()
            search_results = search_data.get("query", {}).get("search", [])
            if not search_results:
                return ""

            # Try up to 3 search results to find one with a real summary
            for result in search_results:
                title = result["title"]
                # Skip obvious disambiguation pages
                if "(" in title and "disambiguation" not in title.lower():
                    continue

                # Step 2: use the REST summary endpoint for a clean extract
                summary_resp = requests.get(
                    self._WIKI_SUMMARY_URL.format(title=title.replace(" ", "_")),
                    headers=self._WIKI_HEADERS,
                    timeout=REQUEST_TIMEOUT,
                )
                if summary_resp.status_code == 200:
                    data = summary_resp.json()
                    extract = data.get("extract", "").strip()
                    if extract:
                        return extract

            return ""
        except Exception:
            log.debug("Wikipedia query failed", exc_info=True)
            return ""

    # ── Backend 3: Ollama (local LLM) ────────────────────────────────
    def _query_ollama(self, query: str) -> str:
        url = f"{OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": OLLAMA_MODEL,
            "prompt": query,
            "stream": False,
        }
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
        return data.get("response", "").strip()

    # ── Backend 4: DuckDuckGo HTML search ────────────────────────────
    def _query_web_search(self, query: str) -> str:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            )
        }
        resp = requests.get(
            DDG_HTML_URL,
            params={"q": query, "kl": "us-en"},
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        # Parse result snippets from the HTML.
        # DDG lite HTML wraps snippets in <a class="result__snippet" ...>
        snippet_pattern = re.compile(
            r'result__snippet[^>]*>(.*?)</a>', re.DOTALL
        )
        matches = snippet_pattern.findall(resp.text)
        snippets = []
        for raw in matches[:3]:
            clean = re.sub(r"<[^>]+>", "", raw)
            clean = html.unescape(clean).strip()
            if clean:
                snippets.append(clean)

        return " ".join(snippets)


# Module-level singleton
ai_answer = AIAnswer()
