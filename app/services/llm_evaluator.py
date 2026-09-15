import json
import time
import re
from typing import Dict, Any, List, Optional
import httpx

from sqlmodel import Session, select
from app.core.config import settings
from app.db.session import engine
from app.models.submission import Submission, SubmissionStatus
from app.models.assignment import Assignment
from app.models.rubric import RubricStep
from app.models.evaluation import Evaluation


def _generate_deterministic_fallback_evaluation(
    raw_text: str,
    rubric_steps: List[RubricStep]
) -> Dict[str, Any]:
    """
    Deterministic rule-based marking engine.
    Used when GEMINI_API_KEY is not supplied or during test / offline environments.
    Checks keyword presence and enforces rubric max marks.
    """
    lower_text = raw_text.lower()
    step_results = []
    total_awarded = 0.0

    for step in rubric_steps:
        # Check matching required keywords
        matched_keywords = [kw for kw in step.required_keywords if kw.lower() in lower_text]
        keyword_ratio = (
            len(matched_keywords) / len(step.required_keywords)
            if step.required_keywords
            else 1.0
        )

        awarded = round(step.max_marks * keyword_ratio, 1)
        # Cap awarded score
        awarded = min(awarded, step.max_marks)
        total_awarded += awarded

        if awarded == step.max_marks:
            notes = f"Full marks awarded. All criteria for Step {step.step_number} satisfied."
        elif awarded > 0:
            missing = [kw for kw in step.required_keywords if kw.lower() not in lower_text]
            notes = f"Partial credit. Missing key formulation/keywords: {', '.join(missing)}."
        else:
            notes = f"No credit. Criteria for Step {step.step_number} not demonstrated in submission."

        step_results.append({
            "step": step.step_number,
            "awarded": awarded,
            "max": step.max_marks,
            "notes": notes
        })

    feedback = (
        f"Automated deterministic marking complete. Evaluated {len(rubric_steps)} rubric steps. "
        f"Score: {total_awarded:.1f} out of {sum(s.max_marks for s in rubric_steps):.1f}."
    )

    return {
        "steps": step_results,
        "total_awarded": total_awarded,
        "overall_feedback": feedback,
        "prompt_tokens": len(raw_text.split()) * 2,
        "completion_tokens": 120,
        "estimated_cost_usd": 0.0,
    }


def _call_gemini_api(
    raw_text: str,
    rubric_steps: List[RubricStep],
    assignment_title: str
) -> Dict[str, Any]:
    """Call Google Gemini Flash API with structured JSON response."""
    rubric_descriptions = []
    for s in rubric_steps:
        rubric_descriptions.append({
            "step_number": s.step_number,
            "description": s.description,
            "max_marks": s.max_marks,
            "required_keywords": s.required_keywords,
            "deduction_rules": s.deduction_rules
        })

    system_prompt = (
        "You are an expert STEM tutor and automated grader. Evaluate the student's submission "
        "strictly according to the provided rubric steps.\n"
        "Return a VALID JSON object matching this schema exactly:\n"
        "{\n"
        '  "steps": [\n'
        '    {"step": 1, "awarded": 3.0, "max": 3.0, "notes": "Explanation..."}\n'
        "  ],\n"
        '  "total_awarded": 3.0,\n'
        '  "overall_feedback": "Constructive summary..."\n'
        "}\n"
        "Rules:\n"
        "1. Do not award more than the max marks for any step.\n"
        "2. Award partial credit where appropriate based on keywords and formulas.\n"
        "3. Output ONLY the JSON object, with no markdown code fences or other text."
    )

    user_content = (
        f"Assignment: {assignment_title}\n\n"
        f"Rubric Steps:\n{json.dumps(rubric_descriptions, indent=2)}\n\n"
        f"Student Submission:\n{raw_text}"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n{user_content}"}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }

    with httpx.Client(timeout=30.0) as client:
        response = client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

    raw_json_str = data["candidates"][0]["content"]["parts"][0]["text"]
    parsed = json.loads(raw_json_str)

    usage = data.get("usageMetadata", {})
    prompt_tokens = usage.get("promptTokenCount", 0)
    completion_tokens = usage.get("candidatesTokenCount", 0)

    # Free tier cost = $0.00
    return {
        "steps": parsed.get("steps", []),
        "total_awarded": float(parsed.get("total_awarded", 0.0)),
        "overall_feedback": parsed.get("overall_feedback", "Automated grading complete."),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "estimated_cost_usd": 0.0,
    }


def evaluate_submission(raw_text: str, rubric_steps: List[RubricStep], assignment_title: str) -> Dict[str, Any]:
    """
    Evaluates a submission against rubric steps.
    Uses Gemini API if key is present; otherwise gracefully falls back to deterministic evaluator.
    """
    start_time = time.time()
    
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        try:
            result = _call_gemini_api(raw_text, rubric_steps, assignment_title)
        except Exception:
            # Fallback on rate limit, quota or network errors
            result = _generate_deterministic_fallback_evaluation(raw_text, rubric_steps)
    else:
        result = _generate_deterministic_fallback_evaluation(raw_text, rubric_steps)

    latency = round(time.time() - start_time, 3)
    result["latency_seconds"] = latency
    return result


def run_evaluation_job(submission_id: int) -> None:
    """
    FastAPI BackgroundTask worker:
    Executes off the HTTP request thread, updates submission status,
    and creates the Evaluation record.
    """
    with Session(engine) as session:
        submission = session.get(Submission, submission_id)
        if not submission:
            return

        submission.status = SubmissionStatus.EVALUATING
        session.add(submission)
        session.commit()
        session.refresh(submission)

        try:
            assignment = session.get(Assignment, submission.assignment_id)
            if not assignment:
                raise ValueError("Assignment not found for submission")

            rubric_query = (
                select(RubricStep)
                .where(RubricStep.assignment_id == assignment.id)
                .order_by(RubricStep.step_number)
            )
            rubric_steps = list(session.exec(rubric_query).all())

            eval_result = evaluate_submission(
                raw_text=submission.raw_text,
                rubric_steps=rubric_steps,
                assignment_title=assignment.title
            )

            # Save or update Evaluation record idempotently
            existing_eval = session.exec(
                select(Evaluation).where(Evaluation.submission_id == submission.id)
            ).first()

            if existing_eval:
                evaluation = existing_eval
                evaluation.score_awarded = eval_result["total_awarded"]
                evaluation.max_possible_score = assignment.total_marks
                evaluation.step_breakdown = eval_result["steps"]
                evaluation.overall_feedback = eval_result["overall_feedback"]
                evaluation.prompt_tokens = eval_result["prompt_tokens"]
                evaluation.completion_tokens = eval_result["completion_tokens"]
                evaluation.estimated_cost_usd = eval_result["estimated_cost_usd"]
                evaluation.latency_seconds = eval_result["latency_seconds"]
            else:
                evaluation = Evaluation(
                    submission_id=submission.id,
                    score_awarded=eval_result["total_awarded"],
                    max_possible_score=assignment.total_marks,
                    step_breakdown=eval_result["steps"],
                    overall_feedback=eval_result["overall_feedback"],
                    prompt_tokens=eval_result["prompt_tokens"],
                    completion_tokens=eval_result["completion_tokens"],
                    estimated_cost_usd=eval_result["estimated_cost_usd"],
                    latency_seconds=eval_result["latency_seconds"]
                )
                session.add(evaluation)

            submission.status = SubmissionStatus.GRADED
            session.add(submission)
            session.commit()

        except Exception as e:
            session.rollback()
            submission.status = SubmissionStatus.FAILED
            session.add(submission)
            session.commit()
