"""
Trust Scoring & Relevance Evaluation Engine for ExamGenie AI.
Implements 4-tier domain source prioritization, multi-factor relevance scoring,
and early rejection of spam/low-quality websites.
"""

import re
from typing import List, Dict, Any, Tuple
from urllib.parse import urlparse

# ── Tier 1: Official Government, Educational Authorities & Universities ─────────
TIER_1_OFFICIAL_PATTERNS = [
    r"\.gov\.in$",
    r"\.nic\.in$",
    r"\.ac\.in$",
    r"\.edu\.in$",
    r"(^|\.)nta\.ac\.in$",
    r"(^|\.)upsc\.gov\.in$",
    r"(^|\.)ssc\.nic\.in$",
    r"(^|\.)ibps\.in$",
    r"(^|\.)gate[a-z0-9]*\.ac\.in$",
    r"(^|\.)jeemain\.nta\.nic\.in$",
    r"(^|\.)neet\.nta\.nic\.in$",
    r"(^|\.)cbse\.gov\.in$",
    r"(^|\.)ncert\.nic\.in$",
    r"(^|\.)ugc\.ac\.in$",
    r"(^|\.)aiims\.edu$",
]

# ── Tier 2: Established Educational Platforms & Recognized Creators ───────────
TIER_2_EDUCATIONAL_DOMAINS = {
    "nptel.ac.in",
    "unacademy.com",
    "pw.live",
    "physicswallah.live",
    "testbook.com",
    "shiksha.com",
    "careers360.com",
    "visionias.in",
    "drishtiias.com",
    "gateoverflow.in",
    "geeksforgeeks.org",
    "studyiq.com",
    "khanacademy.org",
    "byjus.com",
    "adda247.com",
    "nesoacademy.org",
    "oliveboard.in",
    "collegedunia.com",
    "jagranjosh.com",
    "madeeasy.in",
}

# ── Tier 4: Low-Quality, Scraped, or Spam Domains to Deprioritize/Reject ────────
TIER_4_SPAM_PATTERNS = [
    r"blogspot\.com",
    r"wordpress\.com",
    r"freepdf",
    r"downloadpdf",
    r"pdfdrive",
    r"cheat",
    r"leak",
    r"crackexam",
    r"modapk",
    r"sarkariresults\.info",  # fake copycats
]

# Resource type target keywords
KEYWORD_TARGETS = {
    "syllabus": [
        "syllabus", "curriculum", "bulletin", "notification", "scheme",
        "topics", "unit", "detailed syllabus", "exam pattern"
    ],
    "pyq": [
        "question paper", "previous year", "pyq", "solved paper", "shift",
        "answer key", "question papers", "mock paper", "model paper", "past paper"
    ],
    "video": [
        "playlist", "lecture", "course", "complete", "revision", "full course",
        "marathon", "crash course", "explanation", "chapter"
    ],
    "book": [
        "books", "reference book", "topper", "study material", "ncert",
        "textbook", "standard book", "recommended books", "author"
    ],
    "authority": [
        "official", "portal", "conducting body", "application", "notification",
        "admit card", "registration", "bulletin", "overview"
    ],
}


def get_domain_tier(url: str) -> Tuple[int, str, float]:
    """
    Classify a URL into a source tier:
      Tier 1: Official (.gov.in, .nic.in, .ac.in, official bodies) -> +45 pts
      Tier 2: Established Educational Platform -> +25 pts
      Tier 3: General informational website -> +10 pts
      Tier 4: Deprioritized / Spam website -> -50 pts
    Returns (tier_number, tier_label, score_weight).
    """
    if not url:
        return 4, "Invalid", -50.0

    try:
        parsed = urlparse(url.strip())
        netloc = parsed.netloc.lower().replace("www.", "")
    except Exception:
        return 4, "Invalid", -50.0

    # Check Tier 4 first (Spam / Fake blogs)
    for pattern in TIER_4_SPAM_PATTERNS:
        if re.search(pattern, netloc, re.IGNORECASE) or re.search(pattern, url, re.IGNORECASE):
            return 4, "Low Quality", -50.0

    # Check Tier 1 (Official)
    for pattern in TIER_1_OFFICIAL_PATTERNS:
        if re.search(pattern, netloc, re.IGNORECASE):
            return 1, "Official Authority", 45.0

    # Check Tier 2 (Established Edu)
    if netloc in TIER_2_EDUCATIONAL_DOMAINS:
        return 2, "Verified Educational Platform", 25.0

    # Check for youtube.com / youtu.be
    if "youtube.com" in netloc or "youtu.be" in netloc:
        return 2, "Verified Video Source", 20.0

    # Default to Tier 3 (General)
    return 3, "General Source", 10.0


def calculate_relevance_score(
    title: str,
    url: str,
    snippet: str,
    exam_name: str,
    resource_type: str = "general",
) -> float:
    """
    Calculate deterministic relevance score for a resource candidate.
    Factors:
      - Domain Tier (+45 / +25 / +10 / -50)
      - Exam Name Matching in Title (+30) and Snippet (+15)
      - Resource Keyword Matching (+20)
      - PDF / Deep Link bonus for syllabi & papers (+20)
    """
    score = 0.0

    # 1. Domain Tier Score
    tier, _, tier_weight = get_domain_tier(url)
    score += tier_weight
    if tier == 4:
        return -50.0  # Immediate rejection

    title_clean = (title or "").lower()
    snippet_clean = (snippet or "").lower()
    url_clean = (url or "").lower()
    combined_text = f"{title_clean} {snippet_clean} {url_clean}"

    # 2. Exam Name Token Matching
    clean_exam = exam_name.lower().strip()
    exam_tokens = [t for t in re.split(r"[\s\-_]+", clean_exam) if len(t) > 1]

    if clean_exam in combined_text:
        score += 35.0  # Exact full phrase match
    else:
        # Token match ratio
        matched_tokens = sum(1 for token in exam_tokens if token in combined_text)
        if exam_tokens:
            score += (matched_tokens / len(exam_tokens)) * 25.0

    # Exact token in title is high signal
    if any(token in title_clean for token in exam_tokens):
        score += 15.0

    # 3. Resource Keyword Matching
    target_keywords = KEYWORD_TARGETS.get(resource_type.lower(), [])
    matched_keywords = sum(1 for kw in target_keywords if kw in combined_text)
    if matched_keywords > 0:
        score += min(matched_keywords * 6.0, 24.0)

    # 4. Resource Type Specific Bonuses
    is_pdf = url_clean.endswith(".pdf") or "pdf" in url_clean
    if resource_type in ("pyq", "syllabus"):
        if is_pdf:
            score += 20.0  # Direct downloadable PDF is highly desirable
        if any(w in title_clean for w in ("solved", "official", "download", "question paper")):
            score += 10.0

    if resource_type == "video":
        if "playlist" in url_clean or "list=" in url_clean:
            score += 20.0  # Structured full courses preferred over single isolated clips
        if any(w in title_clean for w in ("complete", "course", "playlist", "full")):
            score += 10.0

    # 5. Penalties for clickbait or irrelevant noise
    if any(w in title_clean for w in ("free download full crack", "leak", "cheat", "scam")):
        score -= 40.0

    return max(score, 0.0)


def filter_and_rank_resources(
    items: List[Dict[str, Any]],
    exam_name: str,
    resource_type: str = "general",
    min_score: float = 25.0,
    top_k: int = 12,
) -> List[Dict[str, Any]]:
    """
    Deterministically score, filter out low-relevance candidates, and rank top resources.
    Attaches 'relevance_score', 'trust_tier', and 'is_official' attributes to each item.
    """
    if not items:
        return []

    scored_items = []
    seen_canonical = set()

    for item in items:
        url = item.get("url") or item.get("href") or item.get("link") or ""
        if not url:
            continue

        # Basic canonical deduplication key
        canon_key = url.split("?")[0].split("#")[0].rstrip("/").lower()
        if canon_key in seen_canonical:
            continue

        title = item.get("title") or ""
        snippet = item.get("snippet") or item.get("body") or ""

        score = calculate_relevance_score(
            title=title,
            url=url,
            snippet=snippet,
            exam_name=exam_name,
            resource_type=resource_type,
        )

        tier, tier_label, _ = get_domain_tier(url)

        # Skip Tier 4 and scores below threshold
        if tier == 4 or score < min_score:
            continue

        seen_canonical.add(canon_key)

        enriched = dict(item)
        enriched["relevance_score"] = round(score, 1)
        enriched["trust_tier"] = tier
        enriched["trust_label"] = tier_label
        enriched["is_official"] = (tier == 1)
        scored_items.append(enriched)

    # Sort primarily by relevance score descending
    scored_items.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_items[:top_k]
