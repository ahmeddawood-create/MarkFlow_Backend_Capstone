from fastapi import APIRouter
from app.api.v1.routers import auth, assignments, submissions, evaluations

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(assignments.router)
api_router.include_router(submissions.router)
api_router.include_router(evaluations.router)
