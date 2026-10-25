import logging
import re
from typing import Optional, List, Tuple
import numpy as np

logger = logging.getLogger(__name__)

class EmbeddingService:
    _instance: Optional['EmbeddingService'] = None
    _model = None
    _is_ready: bool = False
    _model_name: str = "all-MiniLM-L6-v2"
    _error_message: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls) -> 'EmbeddingService':
        if cls._instance is None:
            cls._instance = EmbeddingService()
        return cls._instance

    def initialize_model(self, model_name: str = "all-MiniLM-L6-v2") -> bool:
        """Attempt to load sentence-transformers model; cache it in memory."""
        self._model_name = model_name
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading local embedding model: {model_name}...")
            self._model = SentenceTransformer(model_name)
            self._is_ready = True
            self._error_message = None
            logger.info("SentenceTransformer model loaded successfully.")
            return True
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer ({model_name}): {e}. Using deterministic fallback.")
            self._is_ready = False
            self._error_message = str(e)
            return False

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message

    def compute_similarity(self, text1: str, text2: str) -> Tuple[float, str]:
        """
        Compute semantic similarity between two texts.
        Returns: (similarity_score between 0.0 and 1.0, method_used)
        """
        if not text1.strip() or not text2.strip():
            return 0.0, "empty"

        if self._is_ready and self._model is not None:
            try:
                embeddings = self._model.encode([text1, text2], convert_to_numpy=True, normalize_embeddings=True)
                score = float(np.dot(embeddings[0], embeddings[1]))
                # Clamp to [0, 1]
                score = max(0.0, min(1.0, score))
                return score, "sentence_transformers"
            except Exception as e:
                logger.error(f"Error computing sentence embeddings: {e}. Falling back to n-gram similarity.")

        # Deterministic fallback: Character + word n-gram Jaccard overlap
        fallback_score = self._fallback_ngram_similarity(text1, text2)
        return fallback_score, "deterministic_ngram_fallback"

    def _fallback_ngram_similarity(self, s1: str, s2: str) -> float:
        """Token and bi-gram Jaccard similarity fallback."""
        tokens1 = set(re.findall(r'\b\w+\b', s1.lower()))
        tokens2 = set(re.findall(r'\b\w+\b', s2.lower()))
        if not tokens1 or not tokens2:
            return 0.0

        token_jaccard = len(tokens1.intersection(tokens2)) / len(tokens1.union(tokens2))

        # Bigram overlap
        def get_bigrams(tokens_list):
            return set(zip(tokens_list[:-1], tokens_list[1:]))

        words1 = re.findall(r'\b\w+\b', s1.lower())
        words2 = re.findall(r'\b\w+\b', s2.lower())
        bigrams1 = get_bigrams(words1)
        bigrams2 = get_bigrams(words2)

        if bigrams1 and bigrams2:
            bigram_jaccard = len(bigrams1.intersection(bigrams2)) / len(bigrams1.union(bigrams2))
            return 0.6 * token_jaccard + 0.4 * bigram_jaccard
        
        return token_jaccard


embedding_service = EmbeddingService.get_instance()
