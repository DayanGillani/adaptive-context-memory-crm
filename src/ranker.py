"""
Context ranking layer.

Design decision: this implementation ranks relevance using TF-IDF vectors
and cosine similarity (scikit-learn), not a neural embedding model. That
trade-off is intentional and worth stating plainly rather than glossing
over: TF-IDF is lexical (it matches on shared vocabulary), not truly
semantic (it won't catch that "cancel my plan" and "terminate my
subscription" mean the same thing without shared words). A production
version of this system would likely swap in sentence embeddings from a
model like `sentence-transformers` for genuine semantic matching.

TF-IDF is used here because it has zero external dependencies beyond
scikit-learn, requires no model download, runs deterministically, and is
fast enough to unit test without a GPU or API key — which matters for a
component that needs to be reliably testable. The ranking *interface*
(`rank`) is written so that swapping the underlying similarity method for
real embeddings later does not require any change to callers.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .models import MemoryRecord, RankedMemory


class ContextRanker:
    """Ranks candidate memory records by relevance to a query."""

    def rank(
        self, query: str, candidates: list[MemoryRecord], top_k: int | None = None
    ) -> list[RankedMemory]:
        """Score and sort candidate records by relevance to the query.

        Args:
            query: The current user query or interaction text to rank
                candidates against.
            candidates: Memory records already filtered by ContextRetriever.
            top_k: If provided, only return the top_k highest-scoring
                records. Pass None to return all candidates, ranked.

        Returns:
            A list of RankedMemory, sorted by descending score. Empty list
            if there are no candidates (avoids a fit_transform error on an
            empty corpus).
        """
        if not candidates:
            return []

        corpus = [query] + [c.content for c in candidates]

        vectorizer = TfidfVectorizer(stop_words="english")
        try:
            tfidf_matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            # Raised by scikit-learn when the vocabulary is empty after
            # stop-word removal (e.g. query and all candidates are purely
            # stop words). Fall back to zero relevance rather than crashing
            # the retrieval pipeline over an edge case.
            return [RankedMemory(record=c, score=0.0) for c in candidates]

        query_vector = tfidf_matrix[0:1]
        candidate_vectors = tfidf_matrix[1:]

        similarities = cosine_similarity(query_vector, candidate_vectors)[0]

        ranked = [
            RankedMemory(record=candidate, score=float(score))
            for candidate, score in zip(candidates, similarities)
        ]
        ranked.sort(key=lambda rm: rm.score, reverse=True)

        if top_k is not None:
            ranked = ranked[:top_k]

        return ranked
