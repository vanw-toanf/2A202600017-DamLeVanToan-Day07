from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        # TODO: split into sentences, group into chunks
        text = text.strip()
        if not text:
            return []

        sentences = re.findall(r"[^.!?]+(?:[.!?](?:\s+|$)|$)", text, flags=re.MULTILINE)
        cleaned_sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
        if not cleaned_sentences:
            return [text]

        chunks: list[str] = []
        for start in range(0, len(cleaned_sentences), self.max_sentences_per_chunk):
            chunk = " ".join(cleaned_sentences[start : start + self.max_sentences_per_chunk]).strip()
            if chunk:
                chunks.append(chunk)
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        # TODO: implement recursive splitting strategy
        return self._split(text, list(self.separators))

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        # TODO: recursive helper used by RecursiveChunker.chunk
        text = current_text.strip()
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]
        if not remaining_separators:
            return [text[i : i + self.chunk_size].strip() for i in range(0, len(text), self.chunk_size) if text[i : i + self.chunk_size].strip()]

        separator = remaining_separators[0]
        if not separator:
            return [text[i : i + self.chunk_size].strip() for i in range(0, len(text), self.chunk_size) if text[i : i + self.chunk_size].strip()]

        if separator not in text:
            return self._split(text, remaining_separators[1:])

        parts = text.split(separator)
        pieces: list[str] = []
        for index, part in enumerate(parts):
            piece = part + (separator if index < len(parts) - 1 else "")
            piece = piece.strip()
            if not piece:
                continue
            if len(piece) > self.chunk_size and remaining_separators[1:]:
                pieces.extend(self._split(piece, remaining_separators[1:]))
            elif len(piece) > self.chunk_size:
                pieces.extend([piece[i : i + self.chunk_size].strip() for i in range(0, len(piece), self.chunk_size) if piece[i : i + self.chunk_size].strip()])
            else:
                pieces.append(piece)

        if not pieces:
            return []

        merged: list[str] = []
        current_chunk = ""
        for piece in pieces:
            if not current_chunk:
                current_chunk = piece
                continue
            if len(current_chunk) + len(piece) <= self.chunk_size:
                current_chunk += piece
            else:
                merged.append(current_chunk.strip())
                current_chunk = piece

        if current_chunk:
            merged.append(current_chunk.strip())

        return [chunk for chunk in merged if chunk]


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    # TODO: implement cosine similarity formula
    dot_product = _dot(vec_a, vec_b)
    magnitude_a = math.sqrt(_dot(vec_a, vec_a))
    magnitude_b = math.sqrt(_dot(vec_b, vec_b))
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0
    return dot_product / (magnitude_a * magnitude_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        # TODO: call each chunker, compute stats, return comparison dict
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=max(0, chunk_size // 10)),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict[str, dict] = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            avg_length = (sum(len(chunk) for chunk in chunks) / len(chunks)) if chunks else 0.0
            comparison[name] = {
                "count": len(chunks),
                "avg_length": avg_length,
                "chunks": chunks,
            }

        return comparison
