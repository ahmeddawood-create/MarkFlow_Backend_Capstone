from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.user import User, UserRole
from app.models.submission import Submission
from app.models.assignment import Assignment
from app.models.evaluation import Evaluation
from app.schemas.evaluation import EvaluationResponse
from app.core.security import get_current_user
from app.services.pdf_generator import generate_evaluation_pdf

router = APIRouter(prefix="/evaluations", tags=["Evaluations & PDF Reporting"])


@router.get("/{evaluation_id}", response_model=EvaluationResponse)
def get_evaluation(
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Retrieve evaluation details by ID."""
    evaluation = session.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evaluation not found"
        )

    # Check permission
    submission = session.get(Submission, evaluation.submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated submission not found")

    if current_user.role == UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view evaluations belonging to other students"
        )

    return evaluation


@router.get("/{evaluation_id}/report.pdf")
def download_evaluation_pdf(
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Download a formatted, single-page student grade sheet PDF report.
    Returns application/pdf.
    """
    evaluation = session.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluation not found")

    submission = session.get(Submission, evaluation.submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Enforce student access control
    if current_user.role == UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot download grade reports for other students"
        )

    assignment = session.get(Assignment, submission.assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    student = session.get(User, submission.student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    pdf_buffer = generate_evaluation_pdf(
        evaluation=evaluation,
        submission=submission,
        assignment=assignment,
        student=student
    )

    filename = f"grade_report_sub_{submission.id}_eval_{evaluation.id}.pdf"
    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
