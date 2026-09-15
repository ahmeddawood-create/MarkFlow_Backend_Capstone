import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

from app.main import app
from app.db.session import get_session
from app.models.user import User, UserRole
from app.core.security import hash_password


@pytest.fixture(name="session")
def session_fixture():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    import app.db.session
    import app.services.llm_evaluator
    old_db_engine = app.db.session.engine
    old_svc_engine = app.services.llm_evaluator.engine
    app.db.session.engine = test_engine
    app.services.llm_evaluator.engine = test_engine

    with Session(test_engine) as session:
        yield session

    app.db.session.engine = old_db_engine
    app.services.llm_evaluator.engine = old_svc_engine



@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def tutor_token(client: TestClient, session: Session) -> str:
    user = User(
        email="tutor_test@markflow.local",
        hashed_password=hash_password("password123"),
        full_name="Prof Tutor",
        role=UserRole.TUTOR
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    resp = client.post("/api/v1/auth/login", data={"username": user.email, "password": "password123"})
    return resp.json()["access_token"]


@pytest.fixture
def student_token(client: TestClient, session: Session) -> str:
    user = User(
        email="student_test@markflow.local",
        hashed_password=hash_password("password123"),
        full_name="Sam Student",
        role=UserRole.STUDENT
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    resp = client.post("/api/v1/auth/login", data={"username": user.email, "password": "password123"})
    return resp.json()["access_token"]
