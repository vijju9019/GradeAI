from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_teacher
from app.models.user import User
from app.models.submission import StudentSubmission, SubmissionStatus
from app.models.question import Question
from app.models.evaluation import ExtractedAnswer, EvaluationResult, ApprovedMark, ModelVersion
from app.services.nlp_evaluator import nlp_evaluator
from app.ml.trainable_scorer import trainable_scorer
from app.schemas.evaluation import (
    EvaluationResultResponse,
    TrainModelRequest
)

router = APIRouter()

@router.post("/submissions/{submission_id}/evaluate")
def evaluate_submission(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Run modular AI/NLP evaluation engine across all segmented answers.
    Combines keyword/concept coverage, TF-IDF cosine similarity,
    dense semantic embeddings, and granular rubric evaluations into an explainable score.
    """
    submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Student submission not found")

    answers = db.query(ExtractedAnswer).filter(ExtractedAnswer.submission_id == submission.id).all()
    if not answers:
        raise HTTPException(status_code=400, detail="No segmented answers found. Run segmentation first.")

    total_suggested = 0.0
    evaluated_count = 0

    for ans in answers:
        question = ans.question
        if not question:
            continue

        student_text = ans.corrected_answer_text or ans.raw_answer_text or ""
        
        # Evaluate using NLP engine
        eval_data = nlp_evaluator.evaluate_answer(
            student_answer=student_text,
            question=question,
            rubrics=question.rubrics
        )

        # Check existing result
        existing_result = db.query(EvaluationResult).filter(
            EvaluationResult.extracted_answer_id == ans.id
        ).first()

        if existing_result:
            existing_result.suggested_marks = eval_data["suggested_marks"]
            existing_result.confidence_level = eval_data["confidence_level"]
            existing_result.confidence_score = eval_data["confidence_score"]
            existing_result.keyword_coverage_score = eval_data["keyword_coverage_score"]
            existing_result.cosine_similarity_score = eval_data["cosine_similarity_score"]
            existing_result.semantic_similarity_score = eval_data["semantic_similarity_score"]
            existing_result.rubric_score = eval_data["rubric_score"]
            existing_result.matched_keywords = eval_data["matched_keywords"]
            existing_result.missing_keywords = eval_data["missing_keywords"]
            existing_result.matched_concepts = eval_data["matched_concepts"]
            existing_result.missing_concepts = eval_data["missing_concepts"]
            existing_result.rubric_breakdown = eval_data["rubric_breakdown"]
            existing_result.evidence_snippets = eval_data["evidence_snippets"]
            existing_result.uncertainty_reasons = eval_data["uncertainty_reasons"]
        else:
            result = EvaluationResult(
                extracted_answer_id=ans.id,
                question_id=question.id,
                suggested_marks=eval_data["suggested_marks"],
                max_marks=eval_data["max_marks"],
                confidence_level=eval_data["confidence_level"],
                confidence_score=eval_data["confidence_score"],
                keyword_coverage_score=eval_data["keyword_coverage_score"],
                cosine_similarity_score=eval_data["cosine_similarity_score"],
                semantic_similarity_score=eval_data["semantic_similarity_score"],
                rubric_score=eval_data["rubric_score"]
            )
            result.matched_keywords = eval_data["matched_keywords"]
            result.missing_keywords = eval_data["missing_keywords"]
            result.matched_concepts = eval_data["matched_concepts"]
            result.missing_concepts = eval_data["missing_concepts"]
            result.rubric_breakdown = eval_data["rubric_breakdown"]
            result.evidence_snippets = eval_data["evidence_snippets"]
            result.uncertainty_reasons = eval_data["uncertainty_reasons"]
            db.add(result)

        total_suggested += eval_data["suggested_marks"]
        evaluated_count += 1

    submission.total_suggested_marks = round(total_suggested, 2)
    submission.status = SubmissionStatus.EVALUATED.value
    db.commit()

    return {
        "submission_id": submission.id,
        "evaluated_questions": evaluated_count,
        "total_suggested_marks": round(total_suggested, 2),
        "status": submission.status
    }

@router.get("/submissions/{submission_id}/evaluation-results", response_model=List[EvaluationResultResponse])
def get_evaluation_results(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Get detailed evaluation and review workspace items:
    Returns student answers, model answers, rubric breakdown, keyword/concept matches,
    evidence snippets, suggested marks, and approved marks.
    """
    submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Student submission not found")

    answers = db.query(ExtractedAnswer).filter(
        ExtractedAnswer.submission_id == submission_id
    ).join(Question).order_by(Question.order_index).all()

    results = []
    for ans in answers:
        q = ans.question
        eval_res = ans.evaluation_result
        if not eval_res:
            continue

        app_mark = eval_res.approved_mark

        results.append(EvaluationResultResponse(
            id=eval_res.id,
            extracted_answer_id=ans.id,
            question_id=q.id,
            question_number=q.question_number,
            question_text=q.question_text,
            max_marks=q.max_marks,
            suggested_marks=eval_res.suggested_marks,
            confidence_level=eval_res.confidence_level,
            confidence_score=eval_res.confidence_score,
            keyword_coverage_score=eval_res.keyword_coverage_score,
            cosine_similarity_score=eval_res.cosine_similarity_score,
            semantic_similarity_score=eval_res.semantic_similarity_score,
            rubric_score=eval_res.rubric_score,
            matched_keywords=eval_res.matched_keywords,
            missing_keywords=eval_res.missing_keywords,
            matched_concepts=eval_res.matched_concepts,
            missing_concepts=eval_res.missing_concepts,
            rubric_breakdown=eval_res.rubric_breakdown,
            evidence_snippets=eval_res.evidence_snippets,
            uncertainty_reasons=eval_res.uncertainty_reasons,
            evaluated_at=eval_res.evaluated_at,
            teacher_marks=app_mark.teacher_marks if app_mark else None,
            review_notes=app_mark.review_notes if app_mark else None,
            is_overridden=app_mark.is_overridden if app_mark else False,
            reviewer_name=app_mark.reviewer.full_name if (app_mark and app_mark.reviewer) else None,
            approved_at=app_mark.approved_at if app_mark else None,
            student_answer=ans.corrected_answer_text or ans.raw_answer_text,
            model_answer=q.model_answer
        ))

    return results

@router.post("/evaluation/train")
def train_scoring_model(
    train_in: TrainModelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Train optional calibrated regression model on validated teacher marks.
    Requires minimum 5 teacher-approved answers across the database.
    """
    # Fetch all approved marks with evaluation results
    approved = db.query(ApprovedMark).join(EvaluationResult).all()

    samples = []
    for app_m in approved:
        ev = app_m.evaluation_result
        if not ev:
            continue
        ans = ev.extracted_answer
        q = ev.question
        student_text = ans.corrected_answer_text or ans.raw_answer_text if ans else ""
        model_text = q.model_answer if q else ""

        samples.append({
            "keyword_coverage": ev.keyword_coverage_score,
            "tfidf_similarity": ev.cosine_similarity_score,
            "semantic_similarity": ev.semantic_similarity_score,
            "rubric_score": ev.rubric_score,
            "student_length": len(student_text.split()),
            "model_length": len(model_text.split()),
            "max_marks": ev.max_marks,
            "teacher_awarded_marks": app_m.teacher_marks
        })

    train_res = trainable_scorer.train(samples)
    if train_res.get("success"):
        # Persist version in DB
        mv = ModelVersion(
            model_name=train_in.model_name or "gradeai_rf_v1",
            model_type="RandomForestRegressor",
            file_path=str(trainable_scorer.MODEL_PATH),
            is_active=True,
            trained_by_id=current_user.id
        )
        mv.metrics = train_res["metrics"]
        db.add(mv)
        db.commit()

    return train_res
