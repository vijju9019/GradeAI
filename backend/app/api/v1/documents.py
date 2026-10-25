import os
import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_teacher
from app.core.config import settings, UPLOAD_DIR
from app.models.user import User
from app.models.submission import StudentSubmission, SubmissionStatus
from app.models.document import UploadedDocument, ExtractedPage
from app.models.question import Question
from app.models.evaluation import ExtractedAnswer
from app.services.document_extractor import document_extractor
from app.services.segmenter import answer_segmenter
from app.schemas.submission import (
    UploadedDocumentResponse,
    ExtractedPageResponse,
    PageCorrectionRequest,
    AnswerMappingUpdateRequest
)

router = APIRouter()

@router.post("/submissions/{submission_id}/upload", response_model=UploadedDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    submission_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Secure document upload endpoint:
    - Validates MIME type and extension
    - Generates safe unique filename (UUID)
    - Performs text extraction (digital PDF text, plain text, or OCR with quality diagnostics)
    - Persists document and extracted pages
    """
    submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Student submission not found")

    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed formats: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )

    # Secure storage filename
    stored_name = f"{uuid.uuid4().hex}{ext}"
    target_path = UPLOAD_DIR / stored_name

    # Save file contents safely
    try:
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_BYTES // (1024*1024)}MB."
            )
        with open(target_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store file: {str(e)}")

    # Run document extraction
    try:
        extracted_pages_data = document_extractor.extract_document(target_path, file.content_type or "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document extraction failed: {str(e)}")

    # Create UploadedDocument record
    doc_record = UploadedDocument(
        submission_id=submission.id,
        original_filename=file.filename or stored_name,
        stored_filename=stored_name,
        file_path=str(target_path),
        file_size=len(content),
        mime_type=file.content_type or "application/octet-stream",
        page_count=len(extracted_pages_data)
    )
    db.add(doc_record)
    db.commit()
    db.refresh(doc_record)

    # Create ExtractedPage records
    for page in extracted_pages_data:
        p_rec = ExtractedPage(
            document_id=doc_record.id,
            page_number=page["page_number"],
            raw_text=page["text"],
            corrected_text=page["text"],
            extraction_method=page["method"],
            is_poor_quality=page["is_poor_quality"],
            quality_warning=page["warning"]
        )
        db.add(p_rec)

    submission.status = SubmissionStatus.EXTRACTED.value
    db.commit()
    db.refresh(doc_record)
    return doc_record

@router.get("/documents/{doc_id}/file")
def get_document_file(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Retrieve original uploaded document file for preview/side-by-side inspection."""
    doc = db.query(UploadedDocument).filter(UploadedDocument.id == doc_id).first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Document file not found on disk")

    return FileResponse(
        path=doc.file_path,
        media_type=doc.mime_type,
        filename=doc.original_filename
    )

@router.put("/pages/{page_id}/correct", response_model=ExtractedPageResponse)
def correct_page_text(
    page_id: int,
    req: PageCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Allow teacher to manually correct OCR mistakes or poorly extracted page text."""
    page = db.query(ExtractedPage).filter(ExtractedPage.id == page_id).first()
    if not page:
        raise HTTPException(status_code=404, detail="Extracted page not found")

    page.corrected_text = req.corrected_text
    page.is_poor_quality = False  # Teacher corrected it
    db.commit()
    db.refresh(page)
    return page

@router.post("/submissions/{submission_id}/segment")
def run_answer_segmentation(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """
    Segment the complete document text into question-mapped student answers.
    Combines text across all pages in chronological order.
    """
    submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Student submission not found")

    exam_questions = db.query(Question).filter(
        Question.examination_id == submission.examination_id
    ).order_by(Question.order_index).all()

    if not exam_questions:
        raise HTTPException(status_code=400, detail="Cannot segment answers: Examination has no questions defined.")

    # Combine all pages' corrected text
    all_pages = []
    for doc in submission.documents:
        for p in doc.extracted_pages:
            all_pages.append(p.corrected_text or p.raw_text)

    full_document_text = "\n\n".join(all_pages)

    # Run intelligent segmentation
    seg_result = answer_segmenter.segment_answers(full_document_text, exam_questions)

    # Clear old extracted answers if any
    db.query(ExtractedAnswer).filter(ExtractedAnswer.submission_id == submission.id).delete()

    for item in seg_result["mapped_answers"]:
        ans_record = ExtractedAnswer(
            submission_id=submission.id,
            question_id=item["question_id"],
            raw_answer_text=item["answer_text"],
            corrected_answer_text=item["answer_text"],
            segmentation_confidence=item["confidence"],
            is_manually_mapped=False,
            is_missing=item["is_missing"]
        )
        db.add(ans_record)

    submission.status = SubmissionStatus.SEGMENTED.value
    db.commit()

    return {
        "submission_id": submission.id,
        "mapped_count": len(seg_result["mapped_answers"]),
        "unmatched_text": seg_result["unmatched_text"],
        "warnings": seg_result["warnings"]
    }

@router.get("/submissions/{submission_id}/answers")
def get_submission_answers(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Get all segmented student answers for an exam submission."""
    submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Student submission not found")

    answers = db.query(ExtractedAnswer).filter(ExtractedAnswer.submission_id == submission.id).all()
    output = []
    for a in answers:
        q = a.question
        output.append({
            "id": a.id,
            "question_id": a.question_id,
            "question_number": q.question_number if q else "",
            "question_text": q.question_text if q else "",
            "max_marks": q.max_marks if q else 0.0,
            "raw_answer_text": a.raw_answer_text,
            "corrected_answer_text": a.corrected_answer_text,
            "segmentation_confidence": a.segmentation_confidence,
            "is_missing": a.is_missing,
            "has_evaluation": a.evaluation_result is not None
        })
    return output

@router.put("/submissions/{submission_id}/answers")
def update_submission_answers(
    submission_id: int,
    update_in: AnswerMappingUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Allow teachers to edit student answers or re-map question answers."""
    submission = db.query(StudentSubmission).filter(StudentSubmission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Student submission not found")

    for item in update_in.answers:
        existing = db.query(ExtractedAnswer).filter(
            ExtractedAnswer.submission_id == submission_id,
            ExtractedAnswer.question_id == item.question_id
        ).first()

        if existing:
            existing.corrected_answer_text = item.answer_text
            existing.is_manually_mapped = True
            existing.is_missing = item.is_missing or (len(item.answer_text.strip()) == 0)
        else:
            new_ans = ExtractedAnswer(
                submission_id=submission_id,
                question_id=item.question_id,
                raw_answer_text=item.answer_text,
                corrected_answer_text=item.answer_text,
                segmentation_confidence=1.0,
                is_manually_mapped=True,
                is_missing=item.is_missing or (len(item.answer_text.strip()) == 0)
            )
            db.add(new_ans)

    db.commit()
    return {"message": "Answers successfully updated."}
