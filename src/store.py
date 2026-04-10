from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._next_index = 0

        try:
            import chromadb

            self._chroma_client = chromadb.Client()
            try:
                # Keep each store instance isolated even when reusing a collection name in tests.
                self._chroma_client.delete_collection(name=collection_name)
            except Exception:
                pass
            self._collection = self._chroma_client.get_or_create_collection(name=collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata)
        metadata.setdefault("doc_id", doc.id)
        record_id = f"{doc.id}::{self._next_index}"
        self._next_index += 1
        return {
            "id": record_id,
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        query_embedding = self._embedding_fn(query)
        scored = []
        for record in records:
            score = _dot(query_embedding, record["embedding"])
            scored.append(
                {
                    "id": record["id"],
                    "content": record["content"],
                    "metadata": record["metadata"],
                    "score": score,
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        records = [self._make_record(doc) for doc in docs]
        if self._use_chroma and self._collection is not None:
            try:
                self._collection.add(
                    ids=[record["id"] for record in records],
                    documents=[record["content"] for record in records],
                    embeddings=[record["embedding"] for record in records],
                    metadatas=[record["metadata"] for record in records],
                )
            except Exception:
                # Graceful fallback keeps classroom/test runs stable.
                self._use_chroma = False
                self._collection = None
                self._store.extend(records)
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if self._use_chroma and self._collection is not None:
            try:
                # Query by embedding to avoid any external embedding call from Chroma.
                query_embedding = self._embedding_fn(query)
                results = self._collection.query(query_embeddings=[query_embedding], n_results=top_k)
                documents = results.get("documents", [[]])[0]
                metadatas = results.get("metadatas", [[]])[0]
                distances = results.get("distances", [[]])[0]
                output: list[dict[str, Any]] = []
                for content, metadata, distance in zip(documents, metadatas, distances):
                    output.append(
                        {
                            "content": content,
                            "metadata": metadata or {},
                            "score": 1.0 - float(distance) if distance is not None else 0.0,
                        }
                    )
                return output
            except Exception:
                self._use_chroma = False
                self._collection = None

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            try:
                return int(self._collection.count())
            except Exception:
                self._use_chroma = False
                self._collection = None
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if metadata_filter is None:
            return self.search(query, top_k=top_k)

        if self._use_chroma and self._collection is not None:
            try:
                results = self._collection.get(where=metadata_filter, include=["documents", "metadatas", "embeddings"])
                ids = results.get("ids") or []
                documents = results.get("documents") or []
                metadatas = results.get("metadatas") or []
                embeddings = results.get("embeddings") or []
                records = [
                    {
                        "id": record_id,
                        "content": content,
                        "metadata": metadata or {},
                        "embedding": embedding,
                    }
                    for record_id, content, metadata, embedding in zip(ids, documents, metadatas, embeddings)
                ]
                return self._search_records(query, records, top_k)
            except Exception:
                self._use_chroma = False
                self._collection = None

        filtered_records = []
        for record in self._store:
            metadata = record.get("metadata", {})
            if all(metadata.get(key) == value for key, value in metadata_filter.items()):
                filtered_records.append(record)
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            try:
                existing = self._collection.get(where={"doc_id": doc_id})
                ids = existing.get("ids") or []
                if not ids:
                    return False
                self._collection.delete(ids=ids)
                return True
            except Exception:
                self._use_chroma = False
                self._collection = None

        before_count = len(self._store)
        self._store = [record for record in self._store if record.get("metadata", {}).get("doc_id") != doc_id]
        return len(self._store) < before_count
