from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_teacher
from app.models.user import User
from app.services.report_generator import report_generator
from app.schemas.reports import StudentReportResponse

router = APIRouter()

@router.get("/submissions/{submission_id}/report", response_model=StudentReportResponse)
def get_student_scorecard(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Retrieve full student scorecard breakdown and metadata."""
    report_data = report_generator.get_student_report_data(db, submission_id)
    return report_data

@router.get("/submissions/{submission_id}/report/pdf")
def download_student_pdf_report(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Generate and download formal academic PDF scorecard."""
    report_data = report_generator.get_student_report_data(db, submission_id)
    pdf_bytes = report_generator.generate_pdf_report(report_data)

    filename = f"Scorecard_{report_data['student_id']}_{report_data['exam_title'][:15].replace(' ', '_')}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename}\""
        }
    )

@router.get("/examinations/{exam_id}/report/csv")
def download_exam_csv_report(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Download CSV export of examination results."""
    csv_str = report_generator.generate_csv_report(db, exam_id)
    return Response(
        content=csv_str,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=\"examination_{exam_id}_marks.csv\""
        }
    )

@router.get("/examinations/{exam_id}/report/excel")
def download_exam_excel_report(
    exam_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_teacher)
):
    """Download styled Excel (.xlsx) spreadsheet of examination results."""
    excel_bytes = report_generator.generate_excel_report(db, exam_id)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=\"examination_{exam_id}_marks.xlsx\""
        }
    )
