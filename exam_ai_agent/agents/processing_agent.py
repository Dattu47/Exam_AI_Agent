"""
Processing Agent: Cleans text, runs extraction services, removes duplicates, and finds important topics.
"""

from typing import List, Dict, Any, Tuple
from exam_ai_agent.services.syllabus_service import SyllabusService
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)

def _slice_gate_cs_section(text: str) -> str:
    """Heuristic for isolating CS syllabus portion from GATE pages."""
    if not text:
        return ""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    if not lines:
        return ""
    markers = ("computer science and information technology", "computer science & information technology", "computer science", "cs and it")
    idx = -1
    for i, ln in enumerate(lines):
        if any(m in ln.lower() for m in markers):
            idx = i
            break
    if idx == -1:
        return text
    start, end = max(0, idx - 10), min(len(lines), idx + 260)
    return "\n".join(lines[start:end])


class ProcessingAgent:
    def __init__(self, syllabus_service: SyllabusService = None):
        self.syllabus_service = syllabus_service or SyllabusService()

    def extract_and_process(self, exam_name: str, scraped_pages: List[Dict[str, Any]], syllabus_urls: List[str], pattern_results: List[Any]) -> Tuple[List[Dict[str, str]], List[str], List[str]]:
        """
        Parses text for syllabus items, extracts snippets, dedupes topics, and packages them up.
        Returns: (Syllabus List, Important Topics List, Raw Text Chunks for Vector DB)
        """
        logger.info("[ProcessingAgent] Processing scraped data for exam: %s", exam_name)
        
        all_text_for_vector = []
        scraped_syllabus_topics = []
        scraped_syllabus_items = []
        topics_per_url = {}

        for item in scraped_pages:
            all_text_for_vector.append(item["text"])
            
            # Only process as syllabus if it was specifically targeted as a syllabus link
            if item["url"] in syllabus_urls:
                text_for_topics = item["text"]
                
                # GATE CSE/CS special-case: 
                low_exam = exam_name.lower()
                if "gate" in low_exam and ("cse" in low_exam or "cs" in low_exam):
                    text_for_topics = _slice_gate_cs_section(text_for_topics)
                
                # Extract hierarchical dictionary list
                topics_dict_list = self.syllabus_service.extract_from_html(item.get("html", ""), item["url"])
                if len(topics_dict_list) < 3:
                    topics_dict_list.extend(self.syllabus_service.extract_from_text(text_for_topics, item["url"]))
                    # Quick dedupe on topic keys
                    seen_t = set()
                    deduped_dicts = []
                    for d in topics_dict_list:
                        k = d["topic"].lower()
                        if k not in seen_t:
                            seen_t.add(k)
                            deduped_dicts.append(d)
                    topics_dict_list = deduped_dicts
                
                # Context snippets
                lines_for_context = text_for_topics.split("\n")
                for topic_obj in topics_dict_list:
                    t = topic_obj["topic"]
                    subs = topic_obj["subtopics"]
                    scraped_syllabus_topics.append(t)
                    
                    snippet = ""
                    t_lower = t.lower()
                    for li, ln in enumerate(lines_for_context):
                        if t_lower in ln.lower():
                            ctx_start = max(0, li)
                            ctx_lines = [lines_for_context[j].strip() for j in range(ctx_start, min(len(lines_for_context), ctx_start + 4)) if lines_for_context[j].strip()]
                            snippet = " | ".join(ctx_lines)[:300]
                            break
                            
                    scraped_syllabus_items.append({
                        "topic": t,
                        "subtopics": subs,
                        "source_url": item["url"],
                        "description": snippet if snippet else f"{t} — syllabus topic for {exam_name}.",
                    })
                    topics_per_url[item["url"]] = topics_per_url.get(item["url"], 0) + 1

        # Use the single best syllabus source
        if topics_per_url:
            best_url = max(topics_per_url, key=topics_per_url.get)
            scraped_syllabus_items = [x for x in scraped_syllabus_items if x["source_url"] == best_url][:40]
            scraped_syllabus_topics = [x["topic"] for x in scraped_syllabus_items]

        # Important topics logic: prefer extracted topics, fallback to snippets from exam pattern
        important = []
        for t in scraped_syllabus_topics:
            if t and t not in important:
                important.append(t)
            if len(important) >= 20:
                break
        
        if len(important) < 5:
            for r in pattern_results[:6]:
                sn = getattr(r, "snippet", None) or (r.get("snippet") if isinstance(r, dict) else "")
                s = sn.strip() if sn else ""
                if s and s not in important:
                    important.append(s[:180])
                if len(important) >= 15:
                    break
                    
        return scraped_syllabus_items, important[:20], all_text_for_vector
