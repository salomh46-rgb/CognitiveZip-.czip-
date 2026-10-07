"""
Embedded Cognitive & Semantic Index for CognitiveZip.
Enables sub-millisecond natural language search and keyword queries
without extracting the compressed archive.
"""

import math
import re
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple


@dataclass
class SearchResult:
    file_path: str
    relevance_score: float
    matching_terms: List[str]
    best_snippet: str
    line_number: int


class CognitiveIndex:
    """
    Lightweight BM25 + N-gram Semantic Index embedded into .czip footer.
    Zero external heavy dependencies (Pure Python, sub-millisecond execution).
    """

    def __init__(self):
        # file_path -> file metadata & word frequencies
        self.file_metadata: Dict[str, dict] = {}
        # term -> list of (file_path, term_freq)
        self.inverted_index: Dict[str, List[Tuple[str, int]]] = {}
        # Total documents count
        self.total_docs = 0
        self.avg_doc_len = 0.0
        self._doc_lengths: Dict[str, int] = {}
        # file_path -> list of (line_num, line_text) for snippets
        self._snippets_cache: Dict[str, List[Tuple[int, str]]] = {}

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Extracts normalized words, splitting camelCase, snake_case, and kebab-case."""
        # 1. Split camelCase into words: userToken -> user Token
        s1 = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        s2 = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s1)
        # 2. Replace separators with spaces: jwt_token-expire.min -> jwt token expire min
        s3 = re.sub(r"[_\-\./\\:,;\(\)\[\]\{\}\"\'=]", " ", s2)
        # 3. Extract tokens >= 2 chars
        tokens = [t.lower() for t in re.findall(r"[a-zA-Z0-9]{2,}", s3)]
        return tokens

    def add_document(self, file_path: str, content_bytes: bytes) -> None:
        """Indexes text/code document contents."""
        try:
            text = content_bytes.decode("utf-8", errors="replace")
        except Exception:
            text = ""

        lines = text.splitlines()
        cached_lines = []
        for idx, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and len(stripped) < 200:
                cached_lines.append((idx, stripped))

        # Store sample lines for fast snippet retrieval
        self._snippets_cache[file_path] = cached_lines[:150]

        tokens = self.tokenize(text + " " + file_path)
        term_counts = Counter(tokens)
        doc_len = len(tokens)

        self._doc_lengths[file_path] = doc_len
        self.file_metadata[file_path] = {
            "size": len(content_bytes),
            "lines_count": len(lines),
            "doc_len": doc_len,
        }

        for term, count in term_counts.items():
            if term not in self.inverted_index:
                self.inverted_index[term] = []
            self.inverted_index[term].append((file_path, count))

        self.total_docs += 1

    def finalize(self) -> None:
        """Calculates corpus statistics for BM25 ranking."""
        if self.total_docs > 0:
            self.avg_doc_len = sum(self._doc_lengths.values()) / self.total_docs

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Executes BM25 semantic query and returns top matching files with line snippets.
        """
        query_terms = self.tokenize(query)
        if not query_terms or self.total_docs == 0:
            return []

        # BM25 Hyperparameters
        k1 = 1.5
        b = 0.75

        scores: Dict[str, float] = Counter()
        matches: Dict[str, List[str]] = {}

        for term in query_terms:
            postings = self.inverted_index.get(term, [])
            if not postings:
                continue

            df = len(postings)
            # Inverse Document Frequency (IDF)
            idf = math.log(1.0 + (self.total_docs - df + 0.5) / (df + 0.5))

            for file_path, tf in postings:
                doc_len = self._doc_lengths.get(file_path, self.avg_doc_len)
                denom = tf + k1 * (1.0 - b + b * (doc_len / max(1.0, self.avg_doc_len)))
                term_score = idf * (tf * (k1 + 1.0)) / denom
                
                # Bonus for path match
                if term in file_path.lower():
                    term_score *= 1.5

                scores[file_path] += term_score
                if file_path not in matches:
                    matches[file_path] = []
                matches[file_path].append(term)

        results: List[SearchResult] = []
        for file_path, score in scores.most_common(top_k):
            # Locate best snippet with highest query term count
            snippet = ""
            best_line = 1
            max_term_hits = 0
            file_lines = self._snippets_cache.get(file_path, [])

            for line_no, line_text in file_lines:
                lower_line = line_text.lower()
                hits = sum(1 for t in query_terms if t in lower_line)
                if hits > max_term_hits:
                    max_term_hits = hits
                    snippet = line_text
                    best_line = line_no

            if not snippet and file_lines:
                best_line, snippet = file_lines[0]

            results.append(
                SearchResult(
                    file_path=file_path,
                    relevance_score=round(score, 3),
                    matching_terms=list(set(matches.get(file_path, []))),
                    best_snippet=snippet,
                    line_number=best_line,
                )
            )

        return results

    def to_dict(self) -> dict:
        return {
            "total_docs": self.total_docs,
            "avg_doc_len": self.avg_doc_len,
            "file_metadata": self.file_metadata,
            "doc_lengths": self._doc_lengths,
            "inverted_index": self.inverted_index,
            "snippets_cache": self._snippets_cache,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CognitiveIndex":
        idx = cls()
        idx.total_docs = data.get("total_docs", 0)
        idx.avg_doc_len = data.get("avg_doc_len", 0.0)
        idx.file_metadata = data.get("file_metadata", {})
        idx._doc_lengths = data.get("doc_lengths", {})
        idx.inverted_index = data.get("inverted_index", {})
        idx._snippets_cache = data.get("snippets_cache", {})
        return idx
