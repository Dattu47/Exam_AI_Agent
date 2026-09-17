"""
Trust Scoring & Relevance Evaluation Engine for ExamGenie AI.
Implements multi-tier domain categorization, semantic acronym/synonym matching,
and high-recall relevance scoring that embraces verified educational platforms.
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

# ── Tier 2: Established Educational Platforms & Learning Repositories ──────────
# Broad set of recognized competitive exam and academic preparation platforms
TIER_2_EDUCATIONAL_DOMAINS = {
    # Engineering & Coding
    "geeksforgeeks.org",
    "prepinsta.com",
    "javatpoint.com",
    "sanfoundry.com",
    "tutorialspoint.com",
    "gateoverflow.in",
    "nesoacademy.org",
    "madeeasy.in",
    "aceenggacademy.com",
    "nptel.ac.in",
    # Competitive & General Prep
    "testbook.com",
    "adda247.com",
    "unacademy.com",
    "pw.live",
    "physicswallah.live",
    "byjus.com",
    "shiksha.com",
    "careers360.com",
    "studyiq.com",
    "oliveboard.in",
    "cracku.in",
    "gradeup.co",
    "collegedunia.com",
    "jagranjosh.com",
    "freejobalert.com",
    "sarkariresult.com",
    # Civil Services & State Exams
    "visionias.in",
    "drishtiias.com",
    "insightsonindia.com",
    "mrunal.org",
    "clearias.com",
    # Global / Institutional Learning
    "khanacademy.org",
    "coursera.org",
    "edx.org",
    "mit.edu",
    "stanford.edu",
    "ncert.nic.in",
}

# ── Tier 4: Spam / Malicious / Clickbait Scrapers to Deprioritize ───────────────
TIER_4_SPAM_PATTERNS = [
    r"blogspot\.com",
    r"wordpress\.com",
    r"cheat",
    r"leak",
    r"crackexam",
    r"modapk",
    r"downloadfreepdf",
    r"freepdfhub",
    r"sarkariresults\.info",  # fake copycats
]

# ── Exam Acronym & Synonym Dictionary for Semantic Token Matching ──────────────
EXAM_SYNONYMS = {
    "cse": ["computer science", "cs", "software", "information technology", "it"],
    "cs": ["computer science", "cse", "software"],
    "ece": ["electronics", "communication", "telecom"],
    "me": ["mechanical", "mechanical engineering"],
    "ce": ["civil", "civil engineering"],
    "ee": ["electrical", "electrical engineering"],
    "gate": ["graduate aptitude test in engineering", "iit gate"],
    "upsc": ["civil services", "ias", "ips", "ifs", "prelims", "mains", "cse"],
    "jee": ["joint entrance examination", "iit jee", "jee main", "jee advanced"],
    "neet": ["national eligibility cum entrance test", "medical entrance"],
    "ssc": ["staff selection commission", "cgl", "chsl", "cpo"],
    "cat": ["common admission test", "iim cat", "mba entrance"],
    "nda": ["national defence academy", "defence exam"],
    "cds": ["combined defence services"],
    "bank": ["ibps", "sbi", "po", "clerk", "rbi"],
}

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
    "resource": [
        "notes", "tutorial", "guide", "preparation", "practice", "questions",
        "formulas", "quick revision", "concept", "study material", "mock"
    ],
}


def get_domain_tier(url: str) -> Tuple[int, str, float]:
    """
    Classify a URL into a source tier:
      Tier 1: Official (.gov.in, .nic.in, .ac.in, official bodies) -> +45 pts
      Tier 2: Established Educational Platform -> +25 pts
      Tier 3: General Source -> +15 pts
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

    # Check Tier 4 (Spam / Fake blogs)
    for pattern in TIER_4_SPAM_PATTERNS:
        if re.search(pattern, netloc, re.IGNORECASE) or re.search(pattern, url, re.IGNORECASE):
            return 4, "Low Quality", -50.0

    # Check Tier 1 (Official)
    for pattern in TIER_1_OFFICIAL_PATTERNS:
        if re.search(pattern, netloc, re.IGNORECASE):
            return 1, "Official Authority", 45.0

    # Check Tier 2 (Established Educational Platforms)
    if any(netloc == domain or netloc.endswith(f".{domain}") for domain in TIER_2_EDUCATIONAL_DOMAINS):
        return 2, "Verified Educational Platform", 25.0

    # Check YouTube
    if "youtube.com" in netloc or "youtu.be" in netloc:
        return 2, "Verified Video Source", 20.0

    # Default to Tier 3 (General Source)
    return 3, "General Source", 15.0


def calculate_relevance_score(
    title: str,
    url: str,
    snippet: str,
    exam_name: str,
    resource_type: str = "general",
) -> float:
    """
    Calculate high-recall relevance score for a resource candidate.
    Uses semantic acronym & synonym expansion so valid educational resources
    (e.g., "GATE Computer Science Operating Systems Notes" for "GATE CSE") receive strong scores.
    """
    score = 0.0

    # 1. Domain Tier Score
    tier, _, tier_weight = get_domain_tier(url)
    score += tier_weight
    if tier == 4:
        return -50.0  # Immediate rejection for confirmed spam

    title_clean = (title or "").lower()
    snippet_clean = (snippet or "").lower()
    url_clean = (url or "").lower()
    combined_text = f"{title_clean} {snippet_clean} {url_clean}"

    # 2. Semantic Exam & Token Matching
    clean_exam = exam_name.lower().strip()
    exam_tokens = [t for t in re.split(r"[\s\-_]+", clean_exam) if len(t) > 1]

    # Full exact phrase match
    if clean_exam in combined_text:
        score += 35.0
    else:
        # Match tokens or their recognized synonyms
        matched_tokens = 0
        for token in exam_tokens:
            if token in combined_text:
                matched_tokens += 1
            else:
                # Check acronym synonyms (e.g. "cse" -> "computer science")
                synonyms = EXAM_SYNONYMS.get(token, [])
                if any(syn in combined_text for syn in synonyms):
                    matched_tokens += 1

        if exam_tokens:
            score += (matched_tokens / len(exam_tokens)) * 30.0

    # Exact token in title is a high relevance signal
    if any(token in title_clean for token in exam_tokens):
        score += 15.0
    else:
        for token in exam_tokens:
            if any(syn in title_clean for syn in EXAM_SYNONYMS.get(token, [])):
                score += 15.0
                break

    # 3. Resource Keyword Matching
    target_keywords = KEYWORD_TARGETS.get(resource_type.lower(), [])
    if not target_keywords and resource_type in ("resource", "edtech"):
        target_keywords = KEYWORD_TARGETS["resource"]

    matched_keywords = sum(1 for kw in target_keywords if kw in combined_text)
    if matched_keywords > 0:
        score += min(matched_keywords * 5.0, 20.0)

    # 4. Resource Type Specific Bonuses
    is_pdf = url_clean.endswith(".pdf") or "pdf" in url_clean
    if resource_type in ("pyq", "syllabus"):
        if is_pdf:
            score += 20.0  # Direct downloadable PDF
        if any(w in title_clean for w in ("solved", "question paper", "answer key", "pyq")):
            score += 10.0

    if resource_type == "video":
        if "playlist" in url_clean or "list=" in url_clean:
            score += 20.0  # Structured courses
        if any(w in title_clean for w in ("complete", "course", "playlist", "full", "lecture")):
            score += 10.0

    return max(score, 0.0)


def filter_and_rank_resources(
    items: List[Dict[str, Any]],
    exam_name: str,
    resource_type: str = "general",
    min_score: float = 10.0,
    top_k: int = 15,
) -> List[Dict[str, Any]]:
    """
    High-recall ranking: retains all genuine educational resources,
    deduplicating by canonical URL path (preserving distinct pages on the same domain).
    """
    if not items:
        return []

    scored_items = []
    seen_canonical = set()

    for item in items:
        url = item.get("url") or item.get("href") or item.get("link") or ""
        if not url:
            continue

        # Canonical deduplication by URL path (NOT domain)
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

        # Drop only confirmed Tier 4 spam or zero-relevance results
        if tier == 4 or score < min_score:
            continue

        seen_canonical.add(canon_key)

        enriched = dict(item)
        enriched["relevance_score"] = round(score, 1)
        enriched["trust_tier"] = tier
        enriched["trust_label"] = tier_label
        enriched["is_official"] = (tier == 1)
        scored_items.append(enriched)

    # Sort descending by relevance score
    scored_items.sort(key=lambda x: x["relevance_score"], reverse=True)
    return scored_items[:top_k]
