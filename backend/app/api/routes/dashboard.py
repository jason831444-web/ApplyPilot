from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(current_user: CurrentUser, db: DbSession) -> DashboardSummary:
    return DashboardService(db).get_summary(current_user)
