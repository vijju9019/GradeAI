import re
import math
import logging
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional
import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except Exception as e:
    SKLEARN_AVAILABLE = False

from app.core.config import settings
from app.ml.embeddings import embedding_service
from app.models.question import Question, MarkingRubric

logger = logging.getLogger(__name__)

class NLPEvaluationEngine:
    """
    Modular, transparent, and explainable NLP evaluation engine for GradeAI.
    Combines keyword coverage, TF-IDF lexical cosine similarity,
    dense semantic embeddings, and granular rubric evaluations.
    """

    def __init__(
        self,
        weight_keyword: float = settings.DEFAULT_KEYWORD_WEIGHT,
        weight_cosine: float = settings.DEFAULT_COSINE_WEIGHT,
        weight_semantic: float = settings.DEFAULT_SEMANTIC_WEIGHT,
        weight_rubric: float = settings.DEFAULT_RUBRIC_WEIGHT
    ):
        self.weight_keyword = weight_keyword
        self.weight_cosine = weight_cosine
        self.weight_semantic = weight_semantic
        self.weight_rubric = weight_rubric

        # Normalize weights to sum to 1.0
        total_w = self.weight_keyword + self.weight_cosine + self.weight_semantic + self.weight_rubric
        if total_w > 0:
            self.weight_keyword /= total_w
            self.weight_cosine /= total_w
            self.weight_semantic /= total_w
            self.weight_rubric /= total_w

    def preprocess_text(self, text: str) -> str:
        """
        Normalize text while preserving technical punctuation, symbols, formulas, and negations.
        """
        if not text:
            return ""
        # Normalize multiple spaces, tabs, newlines
        cleaned = re.sub(r'[\r\t]+', ' ', text)
        cleaned = re.sub(r'\n+', '\n', cleaned)
        cleaned = re.sub(r' +', ' ', cleaned)
        return cleaned.strip()

    def evaluate_answer(
        self,
        student_answer: str,
        question: Question,
        rubrics: Optional[List[MarkingRubric]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single student answer against the model answer and marking scheme.
        Returns a complete structured evaluation dict with explainability indicators.
        """
        preprocessed_student = self.preprocess_text(student_answer)
        preprocessed_model = self.preprocess_text(question.model_answer)
        max_marks = float(question.max_marks)

        # 1. Edge Case: Empty Answer
        if not preprocessed_student or len(preprocessed_student.strip()) == 0:
            return {
                "suggested_marks": 0.0,
                "max_marks": max_marks,
                "confidence_level": "high",
                "confidence_score": 1.0,
                "keyword_coverage_score": 0.0,
                "cosine_similarity_score": 0.0,
                "semantic_similarity_score": 0.0,
                "rubric_score": 0.0,
                "matched_keywords": [],
                "missing_keywords": question.required_keywords or [],
                "matched_concepts": [],
                "missing_concepts": question.important_concepts or [],
                "rubric_breakdown": [
                    {
                        "rubric_id": r.id if hasattr(r, 'id') else None,
                        "criterion_title": r.criterion_title,
                        "allocated_marks": float(r.allocated_marks),
                        "awarded_marks": 0.0,
                        "met": False,
                        "explanation": "No answer provided by student."
                    }
                    for r in (rubrics or question.rubrics or [])
                ],
                "evidence_snippets": [],
                "uncertainty_reasons": ["Student answer is empty or missing. Zero marks awarded."]
            }

        # 2. Check Alternative Answers if any
        model_candidates = [preprocessed_model]
        if question.alternative_answers:
            model_candidates.extend([self.preprocess_text(alt) for alt in question.alternative_answers if alt.strip()])

        # 3. Keyword Coverage Calculation
        matched_kw, missing_kw, kw_score = self._compute_keyword_coverage(
            preprocessed_student, question.required_keywords or []
        )

        # 4. Concept Coverage Calculation
        matched_concepts, missing_concepts, concept_score = self._compute_concept_coverage(
            preprocessed_student, question.important_concepts or []
        )

        # 5. TF-IDF Lexical Cosine Similarity
        tfidf_score = self._compute_tfidf_similarity(preprocessed_student, model_candidates)

        # 6. Dense Semantic Embedding Similarity
        semantic_score, embed_method = self._compute_semantic_similarity(preprocessed_student, model_candidates)

        # 7. Rubric Criteria Evaluation
        rubric_breakdown, rubric_score, rubric_points_awarded, total_rubric_allocated = self._evaluate_rubrics(
            preprocessed_student, rubrics or question.rubrics or []
        )

        # 8. Composite Mark Calculation
        # If rubrics are defined, they can guide the final mark directly or combine with NLP signals
        has_rubrics = bool(rubrics or question.rubrics)
        
        if has_rubrics and total_rubric_allocated > 0:
            # Weighted mix with rubric emphasis
            raw_ratio = (
                (self.weight_keyword * kw_score) +
                (self.weight_cosine * tfidf_score) +
                (self.weight_semantic * semantic_score) +
                (self.weight_rubric * rubric_score)
            )
            # Rubric factor acts as a validator
            combined_ratio = (raw_ratio * 0.5) + (rubric_score * 0.5)
        else:
            # If no rubrics configured, keyword + cosine + semantic weights re-normalized
            denom = self.weight_keyword + self.weight_cosine + self.weight_semantic
            w_k = self.weight_keyword / denom if denom > 0 else 0.33
            w_c = self.weight_cosine / denom if denom > 0 else 0.33
            w_s = self.weight_semantic / denom if denom > 0 else 0.34
            combined_ratio = (w_k * kw_score) + (w_c * tfidf_score) + (w_s * semantic_score)

        # Length / Conciseness sanity check
        # A concise correct answer should not be penalized, but a 3-word answer for a 10-mark essay should be checked
        word_count = len(re.findall(r'\b\w+\b', preprocessed_student))
        length_penalty_applied = False
        if max_marks >= 5 and word_count < 8 and combined_ratio > 0.4:
            combined_ratio *= 0.6  # Scale down if clearly too terse for an essay question
            length_penalty_applied = True

        # Bound suggested marks between 0.0 and max_marks
        suggested_marks = round(max(0.0, min(max_marks, combined_ratio * max_marks)), 2)

        # 9. Uncertainty and Confidence Analysis
        uncertainty_reasons: List[str] = []
        
        # Check signal disagreement
        signal_diff = abs(tfidf_score - semantic_score)
        if signal_diff >= 0.40:
            uncertainty_reasons.append(
                f"High divergence between lexical similarity ({round(tfidf_score*100)}%) and semantic similarity ({round(semantic_score*100)}%)."
            )

        if missing_kw and len(missing_kw) >= max(1, len(question.required_keywords or []) // 2):
            uncertainty_reasons.append(
                f"Missing {len(missing_kw)} expected key terms: {', '.join(missing_kw[:3])}."
            )

        if length_penalty_applied:
            uncertainty_reasons.append(
                f"Answer is very brief ({word_count} words) relative to maximum marks ({max_marks})."
            )

        if embed_method == "deterministic_ngram_fallback":
            uncertainty_reasons.append(
                "Evaluated using fallback lexical/n-gram heuristics because the dense embedding model is not yet loaded."
            )

        # Confidence level computation
        confidence_score = 1.0 - (min(0.8, (len(uncertainty_reasons) * 0.25) + (signal_diff * 0.3)))
        confidence_score = max(0.1, min(1.0, confidence_score))

        if confidence_score >= settings.CONFIDENCE_HIGH_THRESHOLD and not uncertainty_reasons:
            confidence_level = "high"
        elif confidence_score >= settings.CONFIDENCE_MEDIUM_THRESHOLD:
            confidence_level = "medium"
        else:
            confidence_level = "low"

        # Evidence Snippets: find matching sentence fragments
        evidence_snippets = self._extract_evidence_snippets(preprocessed_student, matched_kw)

        return {
            "suggested_marks": suggested_marks,
            "max_marks": max_marks,
            "confidence_level": confidence_level,
            "confidence_score": round(confidence_score, 2),
            "keyword_coverage_score": round(kw_score, 3),
            "cosine_similarity_score": round(tfidf_score, 3),
            "semantic_similarity_score": round(semantic_score, 3),
            "rubric_score": round(rubric_score, 3),
            "matched_keywords": matched_kw,
            "missing_keywords": missing_kw,
            "matched_concepts": matched_concepts,
            "missing_concepts": missing_concepts,
            "rubric_breakdown": rubric_breakdown,
            "evidence_snippets": evidence_snippets,
            "uncertainty_reasons": uncertainty_reasons
        }

    def _compute_keyword_coverage(self, student_text: str, required_keywords: List[str]) -> Tuple[List[str], List[str], float]:
        if not required_keywords:
            return [], [], 1.0

        lower_student = student_text.lower()
        matched = []
        missing = []

        for kw in required_keywords:
            kw_clean = kw.strip().lower()
            if not kw_clean:
                continue
            # Regex word boundary check for single words, or substring for multi-word phrases
            if ' ' in kw_clean:
                if kw_clean in lower_student:
                    matched.append(kw)
                else:
                    missing.append(kw)
            else:
                pattern = r'\b' + re.escape(kw_clean) + r'(?:s|es|ed|ing)?\b'
                if re.search(pattern, lower_student):
                    matched.append(kw)
                else:
                    missing.append(kw)

        total = len(required_keywords)
        coverage_score = len(matched) / total if total > 0 else 1.0
        return matched, missing, coverage_score

    def _compute_concept_coverage(self, student_text: str, concepts: List[str]) -> Tuple[List[str], List[str], float]:
        if not concepts:
            return [], [], 1.0

        lower_student = student_text.lower()
        matched = []
        missing = []

        for c in concepts:
            c_clean = c.strip().lower()
            if not c_clean:
                continue
            # Check presence or partial phrase overlap
            words = [w for w in re.findall(r'\b\w+\b', c_clean) if len(w) > 3]
            if words:
                overlap = sum(1 for w in words if w in lower_student)
                if overlap >= max(1, len(words) // 2):
                    matched.append(c)
                else:
                    missing.append(c)
            else:
                if c_clean in lower_student:
                    matched.append(c)
                else:
                    missing.append(c)

        score = len(matched) / len(concepts) if concepts else 1.0
        return matched, missing, score

    def _compute_tfidf_similarity(self, student_text: str, model_candidates: List[str]) -> float:
        """Calculate max cosine similarity against model answer or alternative explanations."""
        max_sim = 0.0
        for candidate in model_candidates:
            if not candidate.strip():
                continue
            sim = 0.0
            if SKLEARN_AVAILABLE:
                try:
                    vectorizer = TfidfVectorizer(
                        ngram_range=(1, 2),
                        stop_words='english',
                        token_pattern=r'(?u)\b\w+\b'
                    )
                    tfidf_matrix = vectorizer.fit_transform([student_text, candidate])
                    sim = float(cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0])
                except Exception as e:
                    sim = self._numpy_tfidf_cosine(student_text, candidate)
            else:
                sim = self._numpy_tfidf_cosine(student_text, candidate)

            if sim > max_sim:
                max_sim = sim

        return min(1.0, max(0.0, max_sim))

    def _numpy_tfidf_cosine(self, doc1: str, doc2: str) -> float:
        """Pure NumPy implementation of TF-IDF Cosine Similarity with unigrams and bigrams."""
        def get_tokens(text):
            words = re.findall(r'\b\w+\b', text.lower())
            tokens = list(words)
            for i in range(len(words) - 1):
                tokens.append(f"{words[i]}_{words[i+1]}")
            return tokens

        tokens1 = get_tokens(doc1)
        tokens2 = get_tokens(doc2)
        if not tokens1 or not tokens2:
            return 0.0

        vocab = sorted(list(set(tokens1 + tokens2)))
        if not vocab:
            return 0.0

        c1 = Counter(tokens1)
        c2 = Counter(tokens2)
        N = 2
        v1 = np.zeros(len(vocab), dtype=np.float32)
        v2 = np.zeros(len(vocab), dtype=np.float32)

        for i, term in enumerate(vocab):
            df = (1 if term in c1 else 0) + (1 if term in c2 else 0)
            idf = math.log((1 + N) / (1 + df)) + 1.0
            v1[i] = (c1[term] / len(tokens1)) * idf
            v2[i] = (c2[term] / len(tokens2)) * idf

        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def _compute_semantic_similarity(self, student_text: str, model_candidates: List[str]) -> Tuple[float, str]:
        best_score = 0.0
        best_method = "none"

        for candidate in model_candidates:
            if not candidate.strip():
                continue
            score, method = embedding_service.compute_similarity(student_text, candidate)
            if score > best_score:
                best_score = score
                best_method = method

        return best_score, best_method

    def _evaluate_rubrics(
        self,
        student_text: str,
        rubrics: List[MarkingRubric]
    ) -> Tuple[List[Dict[str, Any]], float, float, float]:
        """
        Evaluate criteria defined in the marking rubric.
        Returns (rubric_breakdown, normalized_score [0..1], points_awarded, total_allocated).
        """
        if not rubrics:
            return [], 1.0, 0.0, 0.0

        breakdown = []
        total_allocated = 0.0
        total_awarded = 0.0
        lower_student = student_text.lower()

        for r in rubrics:
            alloc = float(r.allocated_marks)
            total_allocated += alloc
            title_clean = r.criterion_title.strip()
            desc_clean = (r.description or "").strip()
            
            # Extract keywords from title and description
            crit_text = f"{title_clean} {desc_clean}".lower()
            crit_words = set(re.findall(r'\b\w{4,}\b', crit_text))
            
            # Common stop words removal for rubric evaluation
            stopwords = {"with", "that", "this", "from", "have", "must", "each", "show", "give", "explain", "state", "include"}
            filtered_crit = crit_words - stopwords

            if not filtered_crit:
                # If short, check direct inclusion
                met = title_clean.lower() in lower_student
                ratio = 1.0 if met else 0.0
            else:
                matches = sum(1 for w in filtered_crit if w in lower_student)
                ratio = matches / len(filtered_crit)
                met = ratio >= 0.45

            # Partial credit: award proportional marks
            awarded = round(alloc * min(1.0, max(0.0, ratio if met else (ratio * 0.5))), 2)
            total_awarded += awarded

            breakdown.append({
                "rubric_id": getattr(r, 'id', None),
                "criterion_title": title_clean,
                "allocated_marks": alloc,
                "awarded_marks": awarded,
                "met": met,
                "explanation": f"Satisfied {round(ratio*100)}% of criteria indicators for '{title_clean}'."
            })

        normalized_score = total_awarded / total_allocated if total_allocated > 0 else 1.0
        return breakdown, normalized_score, total_awarded, total_allocated

    def _extract_evidence_snippets(self, student_text: str, matched_keywords: List[str]) -> List[str]:
        """Extract supporting sentences from student text containing matched keywords."""
        if not student_text:
            return []
        sentences = re.split(r'(?<=[.!?])\s+', student_text)
        snippets = []
        for s in sentences:
            s_clean = s.strip()
            if not s_clean:
                continue
            lower_s = s_clean.lower()
            if any(kw.lower() in lower_s for kw in matched_keywords):
                snippets.append(s_clean)
                if len(snippets) >= 3:
                    break
        return snippets


nlp_evaluator = NLPEvaluationEngine()
