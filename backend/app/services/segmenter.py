import re
import logging
from typing import List, Dict, Any, Tuple
from app.models.question import Question

logger = logging.getLogger(__name__)

class AnswerSegmenter:
    """
    Intelligent answer segmentation engine:
    Detects question headings and maps answer content to exam questions.
    """

    # Heading patterns: Q1, Q.1, Question 1, Ans 1, 1(a), 1., etc.
    QUESTION_PATTERNS = [
        r'(?:^|\n)\s*(?:Q(?:uestion)?\.?\s*(\d+[a-z]?|\w+))\s*[:\.\-\)]\s*',
        r'(?:^|\n)\s*(?:Ans(?:wer)?\.?\s*(\d+[a-z]?|\w+))\s*[:\.\-\)]\s*',
        r'(?:^|\n)\s*\(?(\d+[a-z]?)\)\s*[:\.\-]\s*',
        r'(?:^|\n)\s*(\d+)\.\s+',
    ]

    def segment_answers(self, full_text: str, questions: List[Question]) -> Dict[str, Any]:
        """
        Segment the extracted document text into individual answers mapped to question IDs.
        
        Returns:
            {
                "mapped_answers": [
                    {
                        "question_id": int,
                        "question_number": str,
                        "answer_text": str,
                        "confidence": float,
                        "is_missing": bool
                    }
                ],
                "unmatched_text": str,
                "warnings": List[str]
            }
        """
        if not full_text or not full_text.strip():
            return {
                "mapped_answers": [
                    {
                        "question_id": q.id,
                        "question_number": q.question_number,
                        "answer_text": "",
                        "confidence": 0.0,
                        "is_missing": True
                    }
                    for q in questions
                ],
                "unmatched_text": "",
                "warnings": ["The document text is empty. No answers could be segmented."]
            }

        # Build list of candidate blocks by searching for question headers
        found_anchors: List[Tuple[int, int, str]] = [] # (start_idx, end_idx, matched_label)
        
        for pat in self.QUESTION_PATTERNS:
            for match in re.finditer(pat, full_text, flags=re.IGNORECASE):
                label = match.group(1).strip()
                found_anchors.append((match.start(), match.end(), label))

        # Sort anchors by start position
        found_anchors.sort(key=lambda x: x[0])

        # De-duplicate overlapping anchors
        filtered_anchors: List[Tuple[int, int, str]] = []
        last_end = -1
        for start, end, label in found_anchors:
            if start >= last_end:
                filtered_anchors.append((start, end, label))
                last_end = end

        # Extract text blocks between anchors
        segmented_blocks: List[Dict[str, Any]] = []
        unmatched_intro = ""

        if filtered_anchors:
            if filtered_anchors[0][0] > 0:
                unmatched_intro = full_text[:filtered_anchors[0][0]].strip()

            for i in range(len(filtered_anchors)):
                start_content = filtered_anchors[i][1]
                end_content = filtered_anchors[i+1][0] if i + 1 < len(filtered_anchors) else len(full_text)
                label = filtered_anchors[i][2]
                content = full_text[start_content:end_content].strip()
                segmented_blocks.append({
                    "label": label,
                    "content": content
                })
        else:
            # If no clear question markers found, check if only 1 question or split by double newline
            if len(questions) == 1:
                return {
                    "mapped_answers": [{
                        "question_id": questions[0].id,
                        "question_number": questions[0].question_number,
                        "answer_text": full_text.strip(),
                        "confidence": 0.85,
                        "is_missing": False
                    }],
                    "unmatched_text": "",
                    "warnings": ["No question headers found; entire text assigned to single question."]
                }
            else:
                # Fallback: Split by paragraphs across available questions
                paragraphs = [p.strip() for p in re.split(r'\n\s*\n', full_text) if p.strip()]
                mapped = []
                for idx, q in enumerate(questions):
                    ans = paragraphs[idx] if idx < len(paragraphs) else ""
                    mapped.append({
                        "question_id": q.id,
                        "question_number": q.question_number,
                        "answer_text": ans,
                        "confidence": 0.40 if ans else 0.0,
                        "is_missing": not bool(ans)
                    })
                return {
                    "mapped_answers": mapped,
                    "unmatched_text": "\n\n".join(paragraphs[len(questions):]) if len(paragraphs) > len(questions) else "",
                    "warnings": ["No explicit question numbers (e.g. 'Q1:', 'Question 1') detected. Paragraph-based fallback mapping was applied. Please verify question boundaries."]
                }

        # Map segmented blocks to actual exam questions
        mapped_answers = []
        unmatched_blocks = []
        warnings = []

        # Create lookup for questions by normalized question_number
        q_lookup = {}
        for q in questions:
            norm = self._normalize_label(q.question_number)
            q_lookup[norm] = q

        used_block_indices = set()

        for q in questions:
            norm_q = self._normalize_label(q.question_number)
            matched_content = ""
            confidence = 0.0
            
            # Find best matching block
            for b_idx, block in enumerate(segmented_blocks):
                norm_block = self._normalize_label(block["label"])
                if norm_block == norm_q:
                    matched_content = block["content"]
                    confidence = 0.95
                    used_block_indices.add(b_idx)
                    break

            if not matched_content:
                # Try partial match (e.g., "1" matches "1(a)" or similar)
                for b_idx, block in enumerate(segmented_blocks):
                    if b_idx not in used_block_indices:
                        norm_block = self._normalize_label(block["label"])
                        if norm_block in norm_q or norm_q in norm_block:
                            matched_content = block["content"]
                            confidence = 0.70
                            used_block_indices.add(b_idx)
                            break

            is_missing = not bool(matched_content.strip())
            if is_missing:
                warnings.append(f"Answer for Question {q.question_number} was not detected.")

            mapped_answers.append({
                "question_id": q.id,
                "question_number": q.question_number,
                "answer_text": matched_content,
                "confidence": confidence if not is_missing else 0.0,
                "is_missing": is_missing
            })

        # Collect unused text
        unmatched_parts = []
        if unmatched_intro:
            unmatched_parts.append(f"[Document Header]: {unmatched_intro}")
        for b_idx, block in enumerate(segmented_blocks):
            if b_idx not in used_block_indices:
                unmatched_parts.append(f"[Unmapped block '{block['label']}']: {block['content']}")

        return {
            "mapped_answers": mapped_answers,
            "unmatched_text": "\n\n".join(unmatched_parts),
            "warnings": warnings
        }

    def _normalize_label(self, label: str) -> str:
        """Strip 'Q', 'q', dots, parens, spaces."""
        cleaned = re.sub(r'^(?:question|ans|q)\.?\s*', '', label.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r'[\(\)\.\:\-\s]', '', cleaned)
        return cleaned.lower()


answer_segmenter = AnswerSegmenter()
