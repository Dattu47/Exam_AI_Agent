"""
Vector store using FAISS for storing and retrieving exam research knowledge.
Uses Google Generative AI embeddings when configured; falls back safely to in-memory embeddings.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any

from exam_ai_agent.config import settings
from exam_ai_agent.utils.logger import get_logger

logger = get_logger(__name__)


try:
    from langchain_core.embeddings import Embeddings
except ImportError:
    from langchain_community.embeddings import Embeddings


class ResilientEmbeddings(Embeddings):
    """Wrapper that tries Google embeddings and gracefully falls back to deterministic embeddings."""

    def __init__(self, primary=None, fallback=None):
        self.primary = primary
        self.fallback = fallback

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self.primary:
            try:
                return self.primary.embed_documents(texts)
            except Exception as e:
                logger.debug("Primary embeddings failed (%s); using fallback.", e)
        return self.fallback.embed_documents(texts)

    def embed_query(self, text: str) -> List[float]:
        if self.primary:
            try:
                return self.primary.embed_query(text)
            except Exception as e:
                logger.debug("Primary query embedding failed (%s); using fallback.", e)
        return self.fallback.embed_query(text)

    def __call__(self, text: str) -> List[float]:
        return self.embed_query(text)


def _get_embeddings():
    """
    Create resilient embeddings model:
    Uses Google Generative AI embeddings when supported;
    falls back cleanly to FakeEmbeddings for offline/testing resilience.
    """
    try:
        from langchain_core.embeddings import FakeEmbeddings
    except ImportError:
        from langchain_community.embeddings import FakeEmbeddings
    fallback = FakeEmbeddings(size=768)

    api_key = settings.resolve_gemini_key()
    if api_key:
        try:
            from langchain_google_genai import GoogleGenerativeAIEmbeddings
            model = settings.EMBEDDING_MODEL
            if not model.startswith("models/"):
                model = f"models/{model}"
            primary = GoogleGenerativeAIEmbeddings(model=model, google_api_key=api_key)
            return ResilientEmbeddings(primary=primary, fallback=fallback)
        except Exception as e:
            logger.warning("Failed to initialize Google embeddings: %s. Using fallback.", e)

    return fallback


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
        """Load existing FAISS index or initialize empty store."""
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
                logger.warning("Could not load FAISS index: %s. Re-initializing.", e)
        self._store = None

    def add_texts(
        self,
        texts: List[str],
        metadatas: Optional[List[dict]] = None,
        exam_name: Optional[str] = None,
    ) -> None:
        """
        Add text chunks to the vector store with semantic splitting and metadata.
        Splits documents into coherent passages and persists index to disk.
        """
        from langchain_community.vectorstores import FAISS
        from langchain_core.documents import Document
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        if not texts:
            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        docs: List[Document] = []
        for i, text in enumerate(texts):
            if not text or not text.strip():
                continue
            meta = (metadatas[i] if metadatas and i < len(metadatas) else {}).copy()
            if exam_name:
                meta["exam_name"] = exam_name.strip()

            chunks = splitter.split_text(text)
            for chunk_idx, chunk in enumerate(chunks):
                chunk_meta = meta.copy()
                chunk_meta["chunk_index"] = chunk_idx
                docs.append(Document(page_content=chunk, metadata=chunk_meta))

        if not docs:
            return

        try:
            if self._store is None:
                self._store = FAISS.from_documents(docs, self._embeddings)
            else:
                try:
                    self._store.add_documents(docs)
                except Exception as dim_err:
                    logger.warning("Index mismatch (%s). Recreating index.", dim_err)
                    self._store = FAISS.from_documents(docs, self._embeddings)

            # Persist FAISS index to disk
            self._store.save_local(str(self.persist_path))
            logger.info("Added and indexed %d document chunks for exam '%s'", len(docs), exam_name or "unknown")
        except Exception as e:
            logger.warning("Vector store add_texts failed: %s", e)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter_dict: Optional[dict] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content matching query.

        Args:
            query: Search query string
            k: Number of results
            filter_dict: Optional metadata filter (e.g. {"exam_name": "GATE CSE"})

        Returns:
            List of {"content": str, "metadata": dict}
        """
        if self._store is None or not query.strip():
            return []
        try:
            results = self._store.similarity_search(query, k=k, filter=filter_dict)
            return [
                {"content": r.page_content, "metadata": r.metadata}
                for r in results
            ]
        except Exception as e:
            logger.warning("Vector search failed for query '%s': %s", query[:50], e)
            return []

    def clear(self) -> None:
        """Reset and remove persisted vector index."""
        self._store = None
        import shutil
        if self.persist_path.exists():
            shutil.rmtree(self.persist_path, ignore_errors=True)
            self.persist_path.mkdir(parents=True, exist_ok=True)
            logger.info("Cleared vector store at %s", self.persist_path)
