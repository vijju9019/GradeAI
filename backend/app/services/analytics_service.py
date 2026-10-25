import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.examination import Examination, ExamStatus
from app.models.submission import StudentSubmission, SubmissionStatus
from app.models.document import UploadedDocument, ExtractedPage
from app.models.evaluation import ExtractedAnswer, EvaluationResult, ApprovedMark
from app.models.question import Question
from app.models.audit import AuditLog

logger = logging.getLogger(__name__)

class AnalyticsService:
    def get_dashboard_stats(self, db: Session) -> Dict[str, Any]:
        """Compute real database-backed metrics for the dashboard."""
        total_exams = db.query(func.count(Examination.id)).scalar() or 0
        total_students = db.query(func.count(StudentSubmission.id)).scalar() or 0
        total_documents = db.query(func.count(UploadedDocument.id)).scalar() or 0

        # Submissions that need review
        pending_reviews = db.query(func.count(StudentSubmission.id)).filter(
            StudentSubmission.status.in_([SubmissionStatus.EVALUATED.value, SubmissionStatus.SEGMENTED.value]),
            StudentSubmission.is_finalized == False
        ).scalar() or 0

        finalized_count = db.query(func.count(StudentSubmission.id)).filter(
            StudentSubmission.is_finalized == True
        ).scalar() or 0

        # Average approved percentage among evaluated or finalized submissions
        avg_percentage = db.query(func.avg(StudentSubmission.percentage)).filter(
            StudentSubmission.status.in_([SubmissionStatus.REVIEWED.value, SubmissionStatus.FINALIZED.value])
        ).scalar() or 0.0

        # OCR success rate: proportion of extracted pages that aren't poor quality / failed
        total_pages = db.query(func.count(ExtractedPage.id)).scalar() or 0
        poor_pages = db.query(func.count(ExtractedPage.id)).filter(ExtractedPage.is_poor_quality == True).scalar() or 0
        ocr_success_rate = round(((total_pages - poor_pages) / total_pages * 100), 1) if total_pages > 0 else 100.0

        # Teacher override rate: proportion of approved marks where teacher changed the AI mark
        total_approved = db.query(func.count(ApprovedMark.id)).scalar() or 0
        overridden_count = db.query(func.count(ApprovedMark.id)).filter(ApprovedMark.is_overridden == True).scalar() or 0
        teacher_override_rate = round((overridden_count / total_approved * 100), 1) if total_approved > 0 else 0.0

        return {
            "total_examinations": total_exams,
            "total_students_evaluated": total_students,
            "total_documents_processed": total_documents,
            "pending_teacher_reviews": pending_reviews,
            "finalized_submissions": finalized_count,
            "average_approved_percentage": round(float(avg_percentage), 1),
            "ocr_success_rate": ocr_success_rate,
            "teacher_override_rate": teacher_override_rate
        }

    def get_marks_distribution(self, db: Session, exam_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Calculate score brackets from approved/finalized submissions."""
        query = db.query(StudentSubmission.percentage)
        if exam_id:
            query = query.filter(StudentSubmission.examination_id == exam_id)
        
        percentages = [row[0] for row in query.all()]
        
        brackets = {
            "0-20%": 0,
            "21-40%": 0,
            "41-60%": 0,
            "61-80%": 0,
            "81-100%": 0
        }

        for pct in percentages:
            if pct <= 20: brackets["0-20%"] += 1
            elif pct <= 40: brackets["21-40%"] += 1
            elif pct <= 60: brackets["41-60%"] += 1
            elif pct <= 80: brackets["61-80%"] += 1
            else: brackets["81-100%"] += 1

        return [{"range_label": k, "count": v} for k, v in brackets.items()]

    def get_question_difficulty_breakdown(self, db: Session, exam_id: int) -> List[Dict[str, Any]]:
        """Calculate average marks and difficulty rating for each question in an examination."""
        questions = db.query(Question).filter(Question.examination_id == exam_id).order_by(Question.order_index).all()
        results = []

        for q in questions:
            # Average teacher marks if available, else suggested marks
            approved_marks = db.query(ApprovedMark.teacher_marks).filter(ApprovedMark.question_id == q.id).all()
            if approved_marks:
                avg_mark = sum(m[0] for m in approved_marks) / len(approved_marks)
            else:
                eval_marks = db.query(EvaluationResult.suggested_marks).filter(EvaluationResult.question_id == q.id).all()
                avg_mark = (sum(m[0] for m in eval_marks) / len(eval_marks)) if eval_marks else 0.0

            max_m = float(q.max_marks)
            pct = round((avg_mark / max_m * 100), 1) if max_m > 0 else 0.0

            if pct >= 75: difficulty = "Easy"
            elif pct >= 45: difficulty = "Moderate"
            else: difficulty = "Challenging"

            results.append({
                "question_number": q.question_number,
                "max_marks": max_m,
                "average_marks": round(avg_mark, 2),
                "average_percentage": pct,
                "difficulty": difficulty
            })

        return results

    def get_subject_performance(self, db: Session) -> List[Dict[str, Any]]:
        """Aggregate performance by subject."""
        exams = db.query(Examination).all()
        subject_stats: Dict[str, Dict[str, Any]] = {}

        for ex in exams:
            sub_name = ex.subject
            if sub_name not in subject_stats:
                subject_stats[sub_name] = {"exam_count": 0, "student_count": 0, "total_pct": 0.0, "evaluated_students": 0}
            
            subject_stats[sub_name]["exam_count"] += 1
            for sub in ex.submissions:
                subject_stats[sub_name]["student_count"] += 1
                if sub.is_finalized or sub.total_approved_marks > 0:
                    subject_stats[sub_name]["total_pct"] += sub.percentage
                    subject_stats[sub_name]["evaluated_students"] += 1

        output = []
        for subj, data in subject_stats.items():
            avg_score = round(data["total_pct"] / data["evaluated_students"], 1) if data["evaluated_students"] > 0 else 0.0
            output.append({
                "subject": subj,
                "exam_count": data["exam_count"],
                "student_count": data["student_count"],
                "average_score": avg_score
            })

        return output

    def get_recent_activity(self, db: Session, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch latest audit entries."""
        logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
        activities = []
        for l in logs:
            action_desc = l.action.replace("_", " ").capitalize()
            activities.append({
                "id": l.id,
                "action": l.action,
                "description": f"{action_desc} on {l.entity_type} {l.entity_id or ''}".strip(),
                "timestamp": l.timestamp.strftime("%Y-%m-%d %H:%M"),
                "user_name": l.user.full_name if l.user else "System"
            })
        return activities


analytics_service = AnalyticsService()
