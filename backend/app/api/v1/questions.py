from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_teacher
from app.models.user import User
from app.models.examination import Examination, ExamStatus
from app.models.question import Question, MarkingRubric
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse
)

router = APIRouter()

@router.post("/examinations/{exam_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def add_question(
    exam_id: int,
    q_in: QuestionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Add a question with rubrics and marking scheme to an exam."""
    exam = db.query(Examination).filter(Examination.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    # Validate that rubric allocations do not exceed question max marks
    if q_in.rubrics:
        total_rubric = sum(r.allocated_marks for r in q_in.rubrics)
        if total_rubric > q_in.max_marks:
            raise HTTPException(
                status_code=400,
                detail=f"Total marks allocated in rubrics ({total_rubric}) exceeds question max marks ({q_in.max_marks})."
            )

    # Validate that total question marks do not exceed exam total marks
    current_sum = sum(q.max_marks for q in exam.questions)
    if current_sum + q_in.max_marks > exam.total_marks:
        raise HTTPException(
            status_code=400,
            detail=f"Adding this question ({q_in.max_marks} marks) would bring total question marks ({current_sum + q_in.max_marks}) above the examination limit ({exam.total_marks})."
        )

    # Order index
    order_idx = q_in.order_index if q_in.order_index > 0 else (len(exam.questions) + 1)

    question = Question(
        examination_id=exam.id,
        question_number=q_in.question_number,
        question_text=q_in.question_text,
        max_marks=q_in.max_marks,
        model_answer=q_in.model_answer,
        order_index=order_idx
    )
    question.required_keywords = q_in.required_keywords
    question.important_concepts = q_in.important_concepts
    question.alternative_answers = q_in.alternative_answers

    db.add(question)
    db.commit()
    db.refresh(question)

    # Add rubrics
    if q_in.rubrics:
        for idx, r in enumerate(q_in.rubrics):
            rubric = MarkingRubric(
                question_id=question.id,
                criterion_title=r.criterion_title,
                description=r.description,
                allocated_marks=r.allocated_marks,
                order_index=r.order_index or (idx + 1)
            )
            db.add(rubric)
        db.commit()
        db.refresh(question)

    # If exam was draft, mark as ready when total marks matched
    new_total = sum(q.max_marks for q in exam.questions)
    if new_total >= exam.total_marks:
        exam.status = ExamStatus.READY.value
        db.commit()

    return question

@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(
    question_id: int,
    q_in: QuestionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Update question text, model answer, keywords, or rubrics."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    exam = question.examination
    if q_in.max_marks is not None:
        other_sum = sum(q.max_marks for q in exam.questions if q.id != question.id)
        if other_sum + q_in.max_marks > exam.total_marks:
            raise HTTPException(
                status_code=400,
                detail=f"Updating question max marks to {q_in.max_marks} exceeds the examination total ({exam.total_marks})."
            )
        question.max_marks = q_in.max_marks

    if q_in.question_number is not None: question.question_number = q_in.question_number
    if q_in.question_text is not None: question.question_text = q_in.question_text
    if q_in.model_answer is not None: question.model_answer = q_in.model_answer
    if q_in.required_keywords is not None: question.required_keywords = q_in.required_keywords
    if q_in.important_concepts is not None: question.important_concepts = q_in.important_concepts
    if q_in.alternative_answers is not None: question.alternative_answers = q_in.alternative_answers
    if q_in.order_index is not None: question.order_index = q_in.order_index

    # Update rubrics if provided
    if q_in.rubrics is not None:
        # Clear existing rubrics
        db.query(MarkingRubric).filter(MarkingRubric.question_id == question.id).delete()
        for idx, r in enumerate(q_in.rubrics):
            rubric = MarkingRubric(
                question_id=question.id,
                criterion_title=r.criterion_title,
                description=r.description,
                allocated_marks=r.allocated_marks,
                order_index=r.order_index or (idx + 1)
            )
            db.add(rubric)

    db.commit()
    db.refresh(question)
    return question

@router.delete("/questions/{question_id}", status_code=status.HTTP_200_OK)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Delete a question and its rubrics from an exam."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    q_num = question.question_number
    db.delete(question)
    db.commit()
    return {"message": f"Question {q_num} successfully deleted."}

@router.post("/examinations/{exam_id}/questions/import", response_model=List[QuestionResponse])
def import_questions(
    exam_id: int,
    questions_in: List[QuestionCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Bulk import questions with rubrics."""
    exam = db.query(Examination).filter(Examination.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    created = []
    for q_in in questions_in:
        q = Question(
            examination_id=exam.id,
            question_number=q_in.question_number,
            question_text=q_in.question_text,
            max_marks=q_in.max_marks,
            model_answer=q_in.model_answer,
            order_index=q_in.order_index or (len(created) + 1)
        )
        q.required_keywords = q_in.required_keywords
        q.important_concepts = q_in.important_concepts
        q.alternative_answers = q_in.alternative_answers
        db.add(q)
        db.commit()
        db.refresh(q)

        for idx, r in enumerate(q_in.rubrics):
            rubric = MarkingRubric(
                question_id=q.id,
                criterion_title=r.criterion_title,
                description=r.description,
                allocated_marks=r.allocated_marks,
                order_index=r.order_index or (idx + 1)
            )
            db.add(rubric)
        db.commit()
        db.refresh(q)
        created.append(q)

    return created
