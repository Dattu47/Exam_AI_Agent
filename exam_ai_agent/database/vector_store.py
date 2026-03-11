"""
Vector store using FAISS for storing and retrieving exam research knowledge.
Uses Ollama embeddings when available; falls back to a simple in-memory store.
"""

from pathlib import Path
from typing import List, Optional

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


def _get_embeddings():
    """Create embeddings model: returns FakeEmbeddings since Ollama is removed."""
    try:
        from langchain_core.embeddings import FakeEmbeddings
    except ImportError:
        from langchain_community.embeddings import FakeEmbeddings
    return FakeEmbeddings(size=384)


class VectorStore:
    """
    FAISS-backed vector store for exam-related documents.
    Persists to disk under config VECTOR_STORE_PATH.
    """

    def __init__(self, persist_path: Optional[str] = None):
        self.persist_path = Path(persist_path or settings.VECTOR_STORE_PATH)
        self.persist_path.mkdir(parents=True, exist_ok=True)
        self._embeddings = _get_embeddings()
        self._store = None
        self._load_or_new()

    def _load_or_new(self):
        """Load existing FAISS index or create new one."""
        from langchain_community.vectorstores import FAISS
        index_file = self.persist_path / "index.faiss"
        if index_file.exists():
            try:
                self._store = FAISS.load_local(
                    str(self.persist_path),
                    self._embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info("Loaded existing FAISS index from %s", self.persist_path)
                return
            except Exception as e:
                logger.warning("Could not load FAISS index: %s. Creating new.", e)
        self._store = None

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        exam_name: Optional[str] = None,
    ) -> None:
        """
        Add text chunks to the vector store.

        Args:
            texts: List of text strings to embed and store
            metadatas: Optional list of metadata dicts (one per text)
            exam_name: If provided, added to each metadata as 'exam_name'
        """
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document

        if not texts:
            return
        docs = []
        for i, t in enumerate(texts):
            if not t or not t.strip():
                continue
            meta = (metadatas[i] if metadatas and i < len(metadatas) else {}).copy()
            if exam_name:
                meta["exam_name"] = exam_name
            docs.append(Document(page_content=t[:8000], metadata=meta))
        if not docs:
            return
        try:
            if self._store is None:
                self._store = FAISS.from_documents(docs, self._embeddings)
            else:
                self._store.add_documents(docs)
            self._store.save_local(str(self.persist_path))
            logger.info("Added %d chunks to vector store", len(docs))
        except Exception as e:
            # Do not fail the main research flow if embeddings/indexing fails.
            logger.warning("Vector store add_texts failed (skipping persistence): %s", e)
            return

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[dict] = None,
    ) -> List[dict]:
        """
        Search for similar content.

        Args:
            query: Search query
            k: Number of results
            filter_dict: Optional metadata filter (e.g. {"exam_name": "GATE CSE"})

        Returns:
            List of {"content": str, "metadata": dict}
        """
        if self._store is None:
            return []
        try:
            results = self._store.similarity_search(query, k=k, filter=filter_dict)
            return [
                {"content": r.page_content, "metadata": r.metadata}
                for r in results
            ]
        except Exception as e:
            logger.warning("Vector search failed: %s", e)
            return []
