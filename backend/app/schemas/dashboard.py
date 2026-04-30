from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_jobs: int = 0
    total_applications: int = 0
    message: str = "Dashboard aggregation is not implemented yet."
