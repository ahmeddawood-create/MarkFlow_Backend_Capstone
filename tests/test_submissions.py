from app.services.llm_evaluator import run_evaluation_job
from app.models.submission import Submission, SubmissionStatus
from app.models.evaluation import Evaluation
from sqlmodel import select


def test_submit_assignment_and_evaluate(client, session, tutor_token, student_token):
    # 1. Tutor creates assignment with rubric
    tutor_headers = {"Authorization": f"Bearer {tutor_token}"}
    create_assignment_payload = {
        "title": "Quantum Mechanics: Infinite Potential Well",
        "description": "Find ground state wave function and energy eigenvalues.",
        "total_marks": 6.0,
        "rubric_steps": [
            {
                "step_number": 1,
                "description": "Write 1D time-independent Schrodinger equation.",
                "max_marks": 3.0,
                "required_keywords": ["schrodinger", "psi", "hbar"],
                "deduction_rules": []
            },
            {
                "step_number": 2,
                "description": "Derive energy eigenvalues E_n = (n^2 * pi^2 * hbar^2) / (2 * m * L^2).",
                "max_marks": 3.0,
                "required_keywords": ["eigenvalue", "energy", "pi", "hbar"],
                "deduction_rules": []
            }
        ]
    }
    assign_resp = client.post("/api/v1/assignments/", json=create_assignment_payload, headers=tutor_headers)
    assert assign_resp.status_code == 201
    assignment_id = assign_resp.json()["id"]

    # 2. Student submits solution
    student_headers = {"Authorization": f"Bearer {student_token}"}
    submission_payload = {
        "raw_text": (
            "Step 1: The time-independent Schrodinger equation is -hbar^2/(2m) * d^2 psi / dx^2 = E psi.\n"
            "Step 2: Applying boundary conditions psi(0)=psi(L)=0 yields energy eigenvalue E_n = n^2 pi^2 hbar^2 / (2 m L^2)."
        )
    }
    sub_resp = client.post(
        f"/api/v1/submissions/{assignment_id}/submit",
        json=submission_payload,
        headers=student_headers
    )
    assert sub_resp.status_code == 202
    sub_data = sub_resp.json()
    submission_id = sub_data["id"]
    assert sub_data["status"] == "EVALUATING"

    # 3. Simulate background grading task
    run_evaluation_job(submission_id)

    # 4. Check submission status and evaluation
    detail_resp = client.get(f"/api/v1/submissions/{submission_id}", headers=student_headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["status"] == "GRADED"
    assert detail_data["evaluation"] is not None
    assert detail_data["evaluation"]["score_awarded"] > 0
    assert len(detail_data["evaluation"]["step_breakdown"]) == 2

    # 5. Download evaluation PDF
    eval_id = detail_data["evaluation"]["id"]
    pdf_resp = client.get(f"/api/v1/evaluations/{eval_id}/report.pdf", headers=student_headers)
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    # PDF magic bytes
    assert pdf_resp.content.startswith(b"%PDF-")
