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

    def extract_from_html(self, html: str, source_url: str = "") -> List[dict]:
        """
        Extract syllabus topics by parsing HTML structure (lists and tables).
        Returns a hierarchical list of topics with discovered subtopics based on heading vs <li> depth.
        
        Args:
            html: Raw HTML content
            source_url: URL this HTML came from

        Returns:
            List of {"topic": "Topic Name", "subtopics": ["Sub 1", "Sub 2"]}
        """
        hierarchy: List[dict] = []
        if not html:
            return hierarchy

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
            if any(bs in low for bs in bad_substrings) or low.strip() in nav_words_exact:
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

        # Heuristic HTML parsing for hierarchy: Look for headings H2/H3 for topics, and lists for subtopics.
        current_topic = None
        
        # Traverse all relevant elements sequentially
        for elem in soup.find_all(['h2', 'h3', 'h4', 'li', 'td', 'th']):
            if elem.find_parents(["nav", "footer", "header", "aside"]):
                continue
                
            text = elem.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text)
            
            if not _is_valid_topic(text):
                continue
                
            if elem.name in ['h2', 'h3', 'h4']:
                current_topic = {"topic": text, "subtopics": []}
                hierarchy.append(current_topic)
            elif elem.name in ['li', 'td', 'th']:
                if current_topic:
                    if text not in current_topic["subtopics"]:
                        current_topic["subtopics"].append(text)
                else:
                    # If we find list items before a heading, make them their own topic
                    current_topic = {"topic": text, "subtopics": []}
                    hierarchy.append(current_topic)

        deduped = []
        seen = set()
        for section in hierarchy:
            topic_key = section["topic"].lower()
            if topic_key in seen:
                continue
            seen.add(topic_key)
            deduped.append(section)

        # Fallback to Text extraction logic if BS4 tags completely fail for this site
        if len(deduped) < 3:
            return self.extract_from_text(soup.get_text(separator="\n", strip=True), source_url)

        return deduped[:40]

    def extract_from_text(self, text: str, source_url: str = "") -> List[dict]:
        """
        Simple rule-based extraction of bullet/topic lines from scraped text.
        Returns a hierarchical list of topics with discovered subtopics.

        Args:
            text: Raw scraped text
            source_url: URL this text came from

        Returns:
            List of {"topic": "Topic Name", "subtopics": ["Sub 1", "Sub 2"]}
        """
        hierarchy: List[dict] = []
        if not text:
            return hierarchy

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

        current_topic = None
        
        for line in text.split("\n"):
            original_line = line
            line = line.strip()
            if len(line) < 5 or len(line) > 200:
                continue
            low = line.lower()
            if any(bs in low for bs in bad_substrings) or low.strip() in nav_words_exact:
                continue
            if low.startswith(("http://", "https://")) or "@" in line:
                continue
            if sum(ch.isalnum() for ch in line) < 4:
                continue
            
            letters = [c for c in line if c.isalpha()]
            is_all_caps = letters and (sum(c.isupper() for c in letters) / max(1, len(letters))) > 0.85 and len(line) > 15
            
            words = line.split()
            if len(words) < 2 and len(line) < 20:
                continue

            cleaned = re.sub(r"^[\d\.\-\*]+\s*", "", line).strip()
            
            # Heuristic for hierarchical parsing:
            # 1. If it's all caps, it's a major topic
            # 2. If it's indented with spaces/tabs in the original raw line, it's a subtopic
            # 3. If it starts with a Roman numeral or letter (a., b.), it's a subtopic
            
            is_indented = len(original_line) - len(original_line.lstrip()) >= 2
            is_sub_bullet = re.match(r"^[a-zivx]+\.\s", line.lower())
            
            if is_all_caps or (not is_indented and not is_sub_bullet and current_topic is None):
                # New Major Topic
                # Filter out generic headers
                if cleaned.lower() not in ("syllabus", "topics", "contents", "section", "exam papers", "papers", "previous papers", "study material", "study plan", "free courses", "important topics", "exam pattern"):
                    current_topic = {"topic": cleaned, "subtopics": []}
                    hierarchy.append(current_topic)
            else:
                # Subtopic (or flat topic if we haven't found a major one yet)
                if cleaned and len(cleaned.split()) >= 2:
                    if current_topic:
                        if cleaned not in current_topic["subtopics"]:
                            current_topic["subtopics"].append(cleaned)
                    else:
                        # Treat as standalone topic if no parent exists
                        if cleaned.lower() not in ("syllabus", "topics", "contents", "section"):
                            current_topic = {"topic": cleaned, "subtopics": []}
                            hierarchy.append(current_topic)

        # Merge and deduplicate
        seen = set()
        deduped = []
        for section in hierarchy:
            topic_key = section["topic"].lower()
            if topic_key in seen:
                continue
            seen.add(topic_key)
            deduped.append(section)

        return deduped[:20]

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
            
        def _base_url(u: str) -> str:
            if not u: return ""
            return u.split('?')[0].split('#')[0].rstrip('/')

        seen_topics = set()
        seen_urls = set()

        # Prefer scraped syllabus topics (these contain the real content).
        for item in scraped_items or []:
            topic = (item.get("topic") or "").strip()
            if not topic:
                continue
                
            key = _norm(topic)
            url_base = _base_url(item.get("source_url", ""))
            
            # Allow multiple topics from the exact same URL (since 1 page has many topics)
            # but don't allow the exact same topic text twice
            if key in seen_topics:
                continue
                
            seen_topics.add(key)
            if url_base:
                seen_urls.add(url_base)
                
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
                    "subtopics": item.get("subtopics", []),
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
            url_base = _base_url(item.get("source_url", ""))
            
            # For fallback search links, we want to skip if we already have the topic OR the exact link
            if key in seen_topics or (url_base and url_base in seen_urls):
                continue
                
            seen_topics.add(key)
            if url_base:
                seen_urls.add(url_base)
                
            merged.append(
                {
                    "topic": topic[:200],
                    "subtopics": [],
                    "source_url": (item.get("source_url") or "").strip(),
                    "description": (item.get("description") or "Reference link")[:800],
                }
            )

        return merged[:40]
