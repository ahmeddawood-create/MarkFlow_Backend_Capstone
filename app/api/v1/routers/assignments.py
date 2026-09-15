from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.user import User
from app.models.assignment import Assignment
from app.models.rubric import RubricStep
from app.schemas.assignment import AssignmentCreate, AssignmentResponse, AssignmentDetailResponse
from app.schemas.rubric import RubricStepResponse
from app.core.security import get_current_user, require_tutor

router = APIRouter(prefix="/assignments", tags=["Assignments & Rubrics"])


@router.post("/", response_model=AssignmentDetailResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    assignment_in: AssignmentCreate,
    current_tutor: User = Depends(require_tutor),
    session: Session = Depends(get_session)
):
    """
    Tutor-only endpoint: Create a new STEM assignment with a step-by-step rubric.
    Validates rubric steps and computes total marks.
    """
    if not assignment_in.rubric_steps:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="An assignment must have at least one rubric step.",
        )

    # Calculate and verify total marks
    calculated_total = sum(step.max_marks for step in assignment_in.rubric_steps)
    if calculated_total != assignment_in.total_marks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Sum of rubric steps ({calculated_total}) does not match total_marks ({assignment_in.total_marks})."
        )

    assignment = Assignment(
        tutor_id=current_tutor.id,
        title=assignment_in.title,
        description=assignment_in.description or "",
        total_marks=assignment_in.total_marks
    )
    session.add(assignment)
    session.commit()
    session.refresh(assignment)

    # Add rubric steps
    rubric_responses = []
    for step_in in assignment_in.rubric_steps:
        rubric_step = RubricStep(
            assignment_id=assignment.id,
            step_number=step_in.step_number,
            description=step_in.description,
            max_marks=step_in.max_marks,
            required_keywords=step_in.required_keywords or [],
            deduction_rules=step_in.deduction_rules or []
        )
        session.add(rubric_step)
        session.commit()
        session.refresh(rubric_step)
        rubric_responses.append(rubric_step)

    return AssignmentDetailResponse(
        id=assignment.id,
        tutor_id=assignment.tutor_id,
        title=assignment.title,
        description=assignment.description,
        total_marks=assignment.total_marks,
        created_at=assignment.created_at,
        rubric_steps=[RubricStepResponse.model_validate(r) for r in rubric_responses]
    )


@router.get("/", response_model=List[AssignmentResponse])
def list_assignments(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List all available assignments."""
    assignments = session.exec(select(Assignment)).all()
    return assignments


@router.get("/{assignment_id}", response_model=AssignmentDetailResponse)
def get_assignment_detail(
    assignment_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get assignment details including full rubric steps."""
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )

    rubric_steps = session.exec(
        select(RubricStep).where(RubricStep.assignment_id == assignment_id).order_by(RubricStep.step_number)
    ).all()

    return AssignmentDetailResponse(
        id=assignment.id,
        tutor_id=assignment.tutor_id,
        title=assignment.title,
        description=assignment.description,
        total_marks=assignment.total_marks,
        created_at=assignment.created_at,
        rubric_steps=[RubricStepResponse.model_validate(r) for r in rubric_steps]
    )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: int,
    session: Session = Depends(get_session),
    current_tutor: User = Depends(require_tutor)
):
    """Tutor-only: Delete an assignment and cascade delete related rubrics & submissions."""
    assignment = session.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    if assignment.tutor_id != current_tutor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete other tutors' assignments")

    session.delete(assignment)
    session.commit()
    return None
