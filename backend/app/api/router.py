from fastapi import APIRouter

from app.features.analysis.api import router as analyze_router
from app.features.qa.api import router as qa_router


api_router = APIRouter()

# Mount feature routers
api_router.include_router(analyze_router)
api_router.include_router(qa_router)


