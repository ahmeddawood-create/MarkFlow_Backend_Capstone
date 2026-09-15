from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.user import User, UserRole
from app.models.assignment import Assignment
from app.models.submission import Submission, SubmissionStatus
from app.models.evaluation import Evaluation
from app.schemas.submission import SubmissionCreate, SubmissionResponse, SubmissionDetailResponse
from app.schemas.evaluation import EvaluationResponse
from app.core.security import get_current_user, require_student, require_tutor
from app.services.llm_evaluator import run_evaluation_job

router = APIRouter(prefix="/submissions", tags=["Submissions & Evaluation Gateway"])


@router.post(
    "/{assignment_id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_202_ACCEPTED
)
def submit_assignment(
    assignment_id: int,
    submission_in: SubmissionCreate,
    background_tasks: BackgroundTasks,
    current_student: User = Depends(require_student),
    session: Session = Depends(get_session)
):
    """
    Student endpoint: Submit solution to a STEM assignment.
    Offloads LLM rubric grading to background task and immediately returns 202 Accepted.
    """
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    if not submission_in.raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Submission text cannot be empty"
        )

    # Create submission record with initial EVALUATING state
    submission = Submission(
        assignment_id=assignment.id,
        student_id=current_student.id,
        raw_text=submission_in.raw_text,
        status=SubmissionStatus.EVALUATING
    )
    session.add(submission)
    session.commit()
    session.refresh(submission)

    # Offload slow AI evaluation to background job
    background_tasks.add_task(run_evaluation_job, submission.id)

    return submission


@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
def get_submission_detail(
    submission_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Retrieve submission status, student answer, and evaluation details (if graded).
    Accessible by the submitting student or any tutor.
    """
    submission = session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    # Access control: students can only see their own submissions
    if current_user.role == UserRole.STUDENT and submission.student_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You can only view your own submissions"
        )

    evaluation = session.exec(
        select(Evaluation).where(Evaluation.submission_id == submission.id)
    ).first()

    eval_response = None
    if evaluation:
        eval_response = EvaluationResponse.model_validate(evaluation)

    return SubmissionDetailResponse(
        id=submission.id,
        assignment_id=submission.assignment_id,
        student_id=submission.student_id,
        status=submission.status,
        submitted_at=submission.submitted_at,
        raw_text=submission.raw_text,
        evaluation=eval_response
    )


@router.get("/", response_model=List[SubmissionResponse])
def list_submissions(
    assignment_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    List submissions. Students see only their own; Tutors see all (optionally filtered by assignment).
    """
    query = select(Submission)
    if current_user.role == UserRole.STUDENT:
        query = query.where(Submission.student_id == current_user.id)
    elif assignment_id is not None:
        query = query.where(Submission.assignment_id == assignment_id)

    submissions = session.exec(query.order_by(Submission.submitted_at.desc())).all()
    return submissions


@router.post("/{submission_id}/regrade", status_code=status.HTTP_202_ACCEPTED)
def trigger_regrade(
    submission_id: int,
    background_tasks: BackgroundTasks,
    current_tutor: User = Depends(require_tutor),
    session: Session = Depends(get_session)
):
    """
    Tutor-only: Trigger re-evaluation of a submission in the background.
    """
    submission = session.get(Submission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Delete existing evaluation if present
    existing_eval = session.exec(
        select(Evaluation).where(Evaluation.submission_id == submission.id)
    ).first()
    if existing_eval:
        session.delete(existing_eval)
        session.commit()

    submission.status = SubmissionStatus.EVALUATING
    session.add(submission)
    session.commit()

    background_tasks.add_task(run_evaluation_job, submission.id)
    return {"message": "Regrading queued successfully", "submission_id": submission.id}
