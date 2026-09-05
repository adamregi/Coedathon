from fastapi import APIRouter
from app.api.v1.analysis import router as analysis_router
from app.api.v1.applications import router as applications_router
from app.api.v1.auth import router as auth_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.health import router as health_router
from app.api.v1.jobs import router as jobs_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.skills import router as skills_router
from app.api.v1.students import router as students_router

api_v1_router = APIRouter()

# Mount health directly at root or under /api/v1 as well
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(students_router)
api_v1_router.include_router(skills_router)
api_v1_router.include_router(jobs_router)
api_v1_router.include_router(analysis_router)
api_v1_router.include_router(recommendations_router)
api_v1_router.include_router(applications_router)
api_v1_router.include_router(dashboard_router)
