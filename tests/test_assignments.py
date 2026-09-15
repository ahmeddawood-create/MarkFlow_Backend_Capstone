def test_create_assignment_as_tutor(client, tutor_token):
    headers = {"Authorization": f"Bearer {tutor_token}"}
    payload = {
        "title": "Calculus 101: Integration by Parts",
        "description": "Evaluate the integral of x * e^x dx.",
        "total_marks": 5.0,
        "rubric_steps": [
            {
                "step_number": 1,
                "description": "Identify u and dv correctly (u = x, dv = e^x dx).",
                "max_marks": 2.0,
                "required_keywords": ["u = x", "dv = e^x"],
                "deduction_rules": []
            },
            {
                "step_number": 2,
                "description": "Apply integration by parts formula: uv - integral(v du).",
                "max_marks": 3.0,
                "required_keywords": ["uv", "integral", "e^x"],
                "deduction_rules": []
            }
        ]
    }

    response = client.post("/api/v1/assignments/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Calculus 101: Integration by Parts"
    assert len(data["rubric_steps"]) == 2
    assert data["total_marks"] == 5.0


def test_create_assignment_as_student_forbidden(client, student_token):
    headers = {"Authorization": f"Bearer {student_token}"}
    payload = {
        "title": "Unauthorized Assignment",
        "total_marks": 5.0,
        "rubric_steps": [
            {"step_number": 1, "description": "Step 1", "max_marks": 5.0}
        ]
    }

    response = client.post("/api/v1/assignments/", json=payload, headers=headers)
    assert response.status_code == 403
    assert "Only tutors can perform this operation" in response.json()["detail"]


def test_create_assignment_rubric_sum_mismatch(client, tutor_token):
    headers = {"Authorization": f"Bearer {tutor_token}"}
    payload = {
        "title": "Mismatched Marks Assignment",
        "total_marks": 10.0,
        "rubric_steps": [
            {"step_number": 1, "description": "Step 1", "max_marks": 4.0}
        ]
    }

    response = client.post("/api/v1/assignments/", json=payload, headers=headers)
    assert response.status_code == 400
    assert "does not match total_marks" in response.json()["detail"]


def test_get_assignment_detail(client, tutor_token, student_token):
    headers = {"Authorization": f"Bearer {tutor_token}"}
    payload = {
        "title": "Physics Lab",
        "total_marks": 2.0,
        "rubric_steps": [
            {"step_number": 1, "description": "Safety Check", "max_marks": 2.0}
        ]
    }
    create_resp = client.post("/api/v1/assignments/", json=payload, headers=headers)
    assignment_id = create_resp.json()["id"]

    # Student can read assignment details
    student_headers = {"Authorization": f"Bearer {student_token}"}
    resp = client.get(f"/api/v1/assignments/{assignment_id}", headers=student_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Physics Lab"
    assert len(data["rubric_steps"]) == 1
