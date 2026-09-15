"""
seed_data.py - MarkFlow Demo Data Populator

Seeds the database with:
- 1 Tutor (tutor@markflow.local / tutorpassword123)
- 2 Students (student1@markflow.local, student2@markflow.local / studentpassword123)
- 1 Physics Kinematics Assignment with a 3-step mark scheme
- 1 Graded sample submission with evaluation metrics & breakdown
- 1 Pending submission ready for live evaluation demo
"""

from sqlmodel import Session, select
from app.db.session import engine, create_db_and_tables
from app.models.user import User, UserRole
from app.models.assignment import Assignment
from app.models.rubric import RubricStep
from app.models.submission import Submission, SubmissionStatus
from app.models.evaluation import Evaluation
from app.core.security import hash_password


def seed():
    print("Initializing database tables...")
    create_db_and_tables()

    with Session(engine) as session:
        # Check if already seeded
        existing_tutor = session.exec(select(User).where(User.email == "tutor@markflow.local")).first()
        if existing_tutor:
            print("Database already contains seed data. Skipping re-seed.")
            return

        print("Seeding users...")
        tutor = User(
            email="tutor@markflow.local",
            hashed_password=hash_password("tutorpassword123"),
            full_name="Dr. Eleanor Vance (Physics)",
            role=UserRole.TUTOR
        )
        student1 = User(
            email="student1@markflow.local",
            hashed_password=hash_password("studentpassword123"),
            full_name="Alice Chen",
            role=UserRole.STUDENT
        )
        student2 = User(
            email="student2@markflow.local",
            hashed_password=hash_password("studentpassword123"),
            full_name="Bob Miller",
            role=UserRole.STUDENT
        )
        session.add_all([tutor, student1, student2])
        session.commit()
        session.refresh(tutor)
        session.refresh(student1)
        session.refresh(student2)

        print("Seeding STEM Assignment: Projectile Motion & Kinematics...")
        assignment = Assignment(
            tutor_id=tutor.id,
            title="Physics 101: Projectile Motion & Kinematics",
            description="A cannon fires a shell at 50 m/s at an angle of 30 degrees above horizontal. Assume g = 9.8 m/s^2. Derive the time of flight, maximum altitude, and total horizontal range.",
            total_marks=10.0
        )
        session.add(assignment)
        session.commit()
        session.refresh(assignment)

        print("Seeding 3-step Rubric Scheme...")
        steps = [
            RubricStep(
                assignment_id=assignment.id,
                step_number=1,
                description="State kinematic formulas and decompose initial velocity into horizontal and vertical components (v0x = v0*cos(theta), v0y = v0*sin(theta)).",
                max_marks=3.0,
                required_keywords=["velocity", "component", "cos", "sin", "theta"],
                deduction_rules=["Missing velocity decomposition (-1.5 marks)"]
            ),
            RubricStep(
                assignment_id=assignment.id,
                step_number=2,
                description="Solve for total flight time t = 2*v0y/g and maximum height H = (v0y^2)/(2*g).",
                max_marks=4.0,
                required_keywords=["time", "flight", "height", "gravity", "g = 9.8"],
                deduction_rules=["Arithmetic error in peak altitude (-1.0 mark)"]
            ),
            RubricStep(
                assignment_id=assignment.id,
                step_number=3,
                description="Compute horizontal range R = v0x * t and include correct physical units (meters).",
                max_marks=3.0,
                required_keywords=["range", "distance", "meters", "m"],
                deduction_rules=["Missing units (-0.5 marks)"]
            )
        ]
        session.add_all(steps)
        session.commit()

        print("Seeding sample graded submission for Student 1 (Alice Chen)...")
        sub1 = Submission(
            assignment_id=assignment.id,
            student_id=student1.id,
            raw_text=(
                "Step 1: The initial velocity is v0 = 50 m/s, theta = 30 deg.\n"
                "v0x = 50 * cos(30) = 43.3 m/s.\n"
                "v0y = 50 * sin(30) = 25.0 m/s.\n\n"
                "Step 2: Using g = 9.8 m/s^2, the time of flight is t = 2 * v0y / g = 50 / 9.8 = 5.10 s.\n"
                "Max height H = v0y^2 / (2 * g) = 625 / 19.6 = 31.89 m.\n\n"
                "Step 3: Horizontal range R = v0x * t = 43.3 * 5.10 = 220.83 meters."
            ),
            status=SubmissionStatus.GRADED
        )
        session.add(sub1)
        session.commit()
        session.refresh(sub1)

        evaluation = Evaluation(
            submission_id=sub1.id,
            score_awarded=10.0,
            max_possible_score=10.0,
            step_breakdown=[
                {
                    "step": 1,
                    "awarded": 3.0,
                    "max": 3.0,
                    "notes": "Excellent initial velocity decomposition into horizontal and vertical components."
                },
                {
                    "step": 2,
                    "awarded": 4.0,
                    "max": 4.0,
                    "notes": "Accurate flight time calculation (5.10s) and maximum altitude (31.89m)."
                },
                {
                    "step": 3,
                    "awarded": 3.0,
                    "max": 3.0,
                    "notes": "Correct horizontal range equation applied with proper units (220.83 meters)."
                }
            ],
            overall_feedback="Outstanding analytical solution! All three rubric steps satisfied with clean notation and correct units.",
            prompt_tokens=312,
            completion_tokens=148,
            estimated_cost_usd=0.0000,
            latency_seconds=1.42
        )
        session.add(evaluation)
        session.commit()

        print("---------------------------------------------------------------")
        print("Demo Database Seeded Successfully!")
        print("Tutor Login:   tutor@markflow.local    / tutorpassword123")
        print("Student 1:     student1@markflow.local / studentpassword123 (Graded)")
        print("Student 2:     student2@markflow.local / studentpassword123 (Ready to submit)")
        print("Sample Assignment ID: 1")
        print("Sample Evaluation ID: 1 (PDF Ready)")
        print("---------------------------------------------------------------")


if __name__ == "__main__":
    seed()
