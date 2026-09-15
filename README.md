# MarkFlow: Student Assessment & Automated Marking Gateway

> **Automated STEM grading pipeline with deterministic rubric enforcement, token cost tracking, and downloadable PDF report cards.**

---

## 1. Problem & 10x Claim

* **The Problem:** Private STEM tutors, teaching assistants, and university instructors spend 10–15 hours weekly manually marking multi-step student solutions against standard mark schemes and writing repetitive explanatory notes for common mistakes.
* **The 10x Claim:** **Drops open-ended STEM assignment grading from ~15 minutes (900 seconds) per student to an 8-second automated review pipeline** with deterministic rubric enforcement and zero tutor burnout.
* **Explicit Non-Goal:** Real-time collaborative text editing, handwriting OCR scanning, or live video proctoring.

---

## 2. The 6 Program Concepts

MarkFlow implements **6 of the primary concepts** (exceeding the required 5 without any swaps):

| # | Concept | Where It Lives in Code | Description |
|---|---|---|---|
| 1 | **API Endpoints** | [`app/api/v1/routers/`](file:///c:/flyrank%20internship/Backend_Capstone/app/api/v1/routers/) | RESTful FastAPI routes with strict Pydantic v2 schemas and HTTP status codes (`201`, `202`, `400`, `401`, `403`, `422`). |
| 2 | **Database** | [`app/models/`](file:///c:/flyrank%20internship/Backend_Capstone/app/models/), [`app/db/session.py`](file:///c:/flyrank%20internship/Backend_Capstone/app/db/session.py) | Relational persistence with SQLModel (SQLAlchemy) & SQLite, handling foreign keys, cascades, and JSON columns. |
| 3 | **Authentication** | [`app/core/security.py`](file:///c:/flyrank%20internship/Backend_Capstone/app/core/security.py), [`app/api/v1/routers/auth.py`](file:///c:/flyrank%20internship/Backend_Capstone/app/api/v1/routers/auth.py) | Role-Based Access Control (RBAC) with JWT Bearer tokens (`require_tutor`, `require_student`) and bcrypt password hashing. |
| 4 | **Background Jobs** | [`app/services/llm_evaluator.py`](file:///c:/flyrank%20internship/Backend_Capstone/app/services/llm_evaluator.py), [`app/api/v1/routers/submissions.py`](file:///c:/flyrank%20internship/Backend_Capstone/app/api/v1/routers/submissions.py) | FastAPI `BackgroundTasks` offloading slow LLM evaluation from the HTTP thread (`SUBMITTED` $\to$ `EVALUATING` $\to$ `GRADED`). |
| 5 | **LLM Integration** | [`app/services/llm_evaluator.py`](file:///c:/flyrank%20internship/Backend_Capstone/app/services/llm_evaluator.py) | Google Gemini 1.5 Flash structured JSON rubric evaluator with fallback, logging tokens, latency, and $0 cost tracking. |
| 6 | **Reporting (PDF)** | [`app/services/pdf_generator.py`](file:///c:/flyrank%20internship/Backend_Capstone/app/services/pdf_generator.py) | Pure-Python ReportLab service rendering clean 1-page student grade reports with step-by-step score cards. |

---

## 3. $0 Technology Stack

* **Framework:** FastAPI
* **ORM & Database:** SQLModel (SQLAlchemy) + SQLite
* **Authentication:** PyJWT + bcrypt
* **AI Evaluation Engine:** Google Gemini Free Tier (`gemini-1.5-flash`) with deterministic rule-based fallback
* **PDF Engine:** ReportLab (pure Python, 0 OS-level DLL dependencies)
* **Testing:** pytest + httpx TestClient

---

## 4. Setup & Running in Under 2 Minutes

### Step 1: Clone and set up virtual environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Configure environment
```bash
cp .env.example .env
# (Optional) Add your free GEMINI_API_KEY from https://aistudio.google.com/
# If left empty, MarkFlow runs its built-in deterministic rule evaluator!
```

### Step 4: Seed demo data
```bash
python seed_data.py
```
*Prepopulates:*
- **Tutor:** `tutor@markflow.local` / `tutorpassword123`
- **Student 1 (Graded):** `student1@markflow.local` / `studentpassword123`
- **Student 2 (Ready to submit):** `student2@markflow.local` / `studentpassword123`
- **Sample Assignment:** Physics Kinematics with a 3-step mark scheme

### Step 5: Start the server
```bash
uvicorn app.main:app --reload
```
Interactive docs are live at **http://127.0.0.1:8000/docs**.

---

## 5. The 5-Minute Interactive Demo Walkthrough (Swagger UI)

1. **Open Swagger:** Navigate to `http://127.0.0.1:8000/docs`.
2. **Step 1 — Authenticate as Tutor:**
   - Click the green **Authorize** button at the top right.
   - Enter `username`: `tutor@markflow.local` and `password`: `tutorpassword123`.
   - Click **Authorize** $\to$ **Close**.
3. **Step 2 — Inspect Assignment & Rubric:**
   - Expand `GET /api/v1/assignments/1` $\to$ **Try it out** $\to$ **Execute**.
   - See the 10-mark Physics problem with 3 granular rubric steps.
4. **Step 3 — Switch to Student:**
   - Click **Authorize** $\to$ **Logout** $\to$ log in with `username`: `student2@markflow.local` and `password`: `studentpassword123`.
5. **Step 4 — Submit STEM Solution:**
   - Expand `POST /api/v1/submissions/1/submit` $\to$ **Try it out**.
   - Input:
     ```json
     {
       "raw_text": "Step 1: v0x = 50*cos(30) = 43.3 m/s, v0y = 50*sin(30) = 25 m/s.\nStep 2: Total flight time t = 2*v0y/g = 50/9.8 = 5.1s, max height H = 31.9m.\nStep 3: Range R = v0x * t = 43.3 * 5.1 = 220.8 meters."
     }
     ```
   - Click **Execute** $\to$ Receive **`202 Accepted`** with `status: EVALUATING`. The background worker immediately begins grading!
6. **Step 5 — Check Evaluated Grade:**
   - Expand `GET /api/v1/submissions/{submission_id}` $\to$ see `status: GRADED` with step-by-step score breakdown, latency (~1.5s), and feedback.
7. **Step 6 — Download Official PDF Grade Sheet:**
   - Expand `GET /api/v1/evaluations/{evaluation_id}/report.pdf` $\to$ Click **Download file**.
   - Open the generated PDF to see the beautifully styled assessment grade card!

---

## 6. Running the Test Suite

Run all automated unit and integration tests with:
```bash
pytest
```
All tests verify RBAC permissions, rubric math integrity, background task grading, and ReportLab PDF magic byte output.
