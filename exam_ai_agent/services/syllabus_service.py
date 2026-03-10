"""
Syllabus service: extracts and structures syllabus information
from search results and scraped content.
"""

import re
from typing import List, Any, Optional

from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


class SyllabusService:
    """
    Processes raw search and scrape data to produce a structured syllabus list.
    Can use LLM for extraction or rule-based parsing.
    """

    def extract_from_search_results(self, search_results: List[Any]) -> List[dict]:
        """
        Extract syllabus-related links and snippets from search results.

        Args:
            search_results: List of SearchResult or dict with title, url, snippet

        Returns:
            List of {"topic": str, "source_url": str, "description": str}
        """
        items = []
        for r in search_results:
            title = getattr(r, "title", None) or (r.get("title") if isinstance(r, dict) else "")
            url = getattr(r, "url", None) or (r.get("url") or r.get("href") or r.get("link") if isinstance(r, dict) else "")
            snippet = getattr(r, "snippet", None) or (r.get("snippet") or r.get("body") if isinstance(r, dict) else "")
            if not title and not snippet:
                continue
            items.append({
                "topic": title[:200] if title else "Syllabus",
                "source_url": url or "",
                "description": (snippet or "")[:500],
            })
        return items[:15]  # Cap for readability

    def extract_from_html(self, html: str, source_url: str = "") -> List[str]:
        """
        Extract syllabus topics by parsing HTML structure (lists and tables).
        
        Args:
            html: Raw HTML content
            source_url: URL this HTML came from

        Returns:
            List of topic strings
        """
        topics: List[str] = []
        if not html:
            return topics

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")

        # Common boilerplate/header/navigation lines to ignore across exam sites.
        bad_substrings = (
            "graduate aptitude test", "organizing institute", "indian institute of technology",
            "ministry of", "copyright", "all rights reserved", "contact us", "website",
            "home page", "login", "log in", "sign in", "sign up", "by logging", "register",
            "application", "brochure", "notification", "important dates", "admit card",
            "result", "gate 20", "click here", "read more", "see also", "share this",
            "follow us", "subscribe", "newsletter", "privacy policy", "terms of", "cookie",
            "advertisement", "sponsored", "related articles", "also read", "get started",
            "download app", "install app",
        )

        nav_words_exact = {
            "courses", "tutorials", "home", "about", "contact", "menu",
            "navigation", "resources", "blog", "news", "forum", "videos",
            "articles", "books", "notes", "jobs", "practice", "quiz",
            "test", "tests", "mock", "mocks", "feedback", "help", "faq",
            "search", "sitemap", "careers", "advertise", "back", "next",
            "previous", "more", "less", "show", "hide", "toggle", "close",
        }

        def _is_valid_topic(text: str) -> bool:
            t = text.strip()
            if len(t) < 5 or len(t) > 200:
                return False
            low = t.lower()
            if any(bs in low for bs in bad_substrings):
                return False
            if low.strip() in nav_words_exact:
                return False
            if low.startswith(("http://", "https://")) or "@" in t:
                return False
            if sum(ch.isalnum() for ch in t) < 4:
                return False
            # Require at least 2 words (or be a long single word like "Thermodynamics")
            words = t.split()
            if len(words) < 2 and len(t) < 10:
                return False
            return True

        # Look for <li> items first, they are the most common container for syllabus topics
        for li in soup.find_all("li"):
            # Ensure it's not a nav menu item
            if li.find_parents(["nav", "footer", "header", "aside"]):
                continue
            text = li.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            if _is_valid_topic(text):
                topics.append(text)

        # If we didn't get much from lists, try looking at table cells (often used for topic -> weightage)
        if len(topics) < 5:
            for td in soup.find_all(["td", "th"]):
                if td.find_parents(["nav", "footer", "header", "aside"]):
                    continue
                text = td.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text)
                if _is_valid_topic(text):
                    topics.append(text)

        deduped = []
        seen = set()
        for t in topics:
            key = t.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(t)

        return deduped[:40]

    def extract_from_text(self, text: str, source_url: str = "") -> List[str]:
        """
        Simple rule-based extraction of bullet/topic lines from scraped text.
        Looks for lines that look like syllabus topics (numbered, bulleted, or short lines).

        Args:
            text: Raw scraped text
            source_url: URL this text came from

        Returns:
            List of topic strings
        """
        topics: List[str] = []
        if not text:
            return topics

        # Common boilerplate/header/navigation lines to ignore across exam sites.
        bad_substrings = (
            "graduate aptitude test",
            "organizing institute",
            "indian institute of technology",
            "ministry of",
            "copyright",
            "all rights reserved",
            "contact us",
            "website",
            "home page",
            "login",
            "log in",
            "sign in",
            "sign up",
            "by logging",
            "register",
            "application",
            "brochure",
            "notification",
            "important dates",
            "admit card",
            "result",
            "gate 20",
            "click here",
            "read more",
            "see also",
            "share this",
            "follow us",
            "subscribe",
            "newsletter",
            "privacy policy",
            "terms of",
            "cookie",
            "advertisement",
            "sponsored",
            "related articles",
            "also read",
            "get started",
            "download app",
            "install app",
        )

        # Standalone navigation words that appear verbatim as menu items.
        nav_words_exact = {
            "courses", "tutorials", "home", "about", "contact", "menu",
            "navigation", "resources", "blog", "news", "forum", "videos",
            "articles", "books", "notes", "jobs", "practice", "quiz",
            "test", "tests", "mock", "mocks", "feedback", "help", "faq",
            "search", "sitemap", "careers", "advertise", "back", "next",
            "previous", "more", "less", "show", "hide", "toggle", "close",
        }

        for line in text.split("\n"):
            line = line.strip()
            if len(line) < 5 or len(line) > 200:
                continue
            low = line.lower()
            if any(bs in low for bs in bad_substrings):
                continue
            # Skip exact navigation words (case-insensitive single-word lines)
            if low.strip() in nav_words_exact:
                continue
            # Skip obvious navigation / URLs
            if low.startswith(("http://", "https://")) or "@" in line:
                continue
            # Skip lines that are mostly punctuation
            if sum(ch.isalnum() for ch in line) < 4:
                continue
            # Skip all-caps banners (common headers)
            letters = [c for c in line if c.isalpha()]
            if letters and (sum(c.isupper() for c in letters) / max(1, len(letters))) > 0.85 and len(line) > 25:
                continue
            # Require at least 2 words to avoid single-word menu items
            words = line.split()
            if len(words) < 2 and len(line) < 20:
                continue
            # Numbered or bulleted
            if re.match(r"^[\d\.\-\*]+\s+\w", line) or line.startswith(("-", "•", "*")):
                cleaned = re.sub(r"^[\d\.\-\*]+\s*", "", line).strip()
                if cleaned and len(cleaned.split()) >= 2:
                    topics.append(cleaned)
            # Short lines that might be section headers
            elif line.isprintable() and not line.endswith((":", ".", ",")) and len(line) < 80:
                # Avoid generic words only
                if line.lower() not in ("syllabus", "topics", "contents", "section", "exam papers", "papers",
                                        "previous papers", "study material", "study plan", "free courses",
                                        "important topics", "exam pattern"):
                    topics.append(line)
        # Dedupe while preserving order, and drop very generic single-word items
        deduped = []
        seen = set()
        for t in topics:
            tt = re.sub(r"\s+", " ", t).strip()
            if len(tt.split()) == 1 and len(tt) < 6:
                continue
            key = tt.lower()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(tt)

        return deduped[:30]

    def merge_syllabus(
        self,
        search_items: List[dict],
        scraped_items: List[dict],
        exam_name: str,
    ) -> List[dict]:
        """
        Merge syllabus from search and scraped content into a single list.

        Returns:
            List of {"topic": str, "source_url": str, "description": str} for syllabus section
        """
        merged: List[dict] = []

        def _norm(s: str) -> str:
            return re.sub(r"\s+", " ", (s or "").strip().lower())

        seen = set()

        # Prefer scraped syllabus topics (these contain the real content).
        for item in scraped_items or []:
            topic = (item.get("topic") or "").strip()
            if not topic:
                continue
            key = _norm(topic)
            if key in seen:
                continue
            seen.add(key)
            # Build a meaningful description: prefer an explicit description, otherwise
            # generate one from the topic itself so each entry looks unique.
            raw_desc = (item.get("description") or "").strip()
            if raw_desc and raw_desc.lower() not in ("extracted from syllabus page", f"extracted from syllabus page for {exam_name.lower()}"):
                description = raw_desc[:800]
            else:
                description = f"{topic} — part of the {exam_name} syllabus. See source link for full details."
            merged.append(
                {
                    "topic": topic[:200],
                    "source_url": (item.get("source_url") or "").strip(),
                    "description": description[:800],
                }
            )

        # Add a small number of search-result items as fallback references (links/snippets).
        for item in (search_items or [])[:8]:
            topic = (item.get("topic") or "").strip()
            if not topic:
                continue
            key = _norm(topic)
            if key in seen:
                continue
            seen.add(key)
            merged.append(
                {
                    "topic": topic[:200],
                    "source_url": (item.get("source_url") or "").strip(),
                    "description": (item.get("description") or "Reference link")[:800],
                }
            )

        return merged[:40]
