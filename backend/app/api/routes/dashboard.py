from fastapi import APIRouter

router = APIRouter()


@router.get("/summary")
def dashboard_summary_placeholder() -> dict[str, str]:
    return {"message": "Dashboard business logic is not implemented yet."}
