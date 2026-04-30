from fastapi import APIRouter

router = APIRouter()


@router.post("")
def create_application_placeholder() -> dict[str, str]:
    return {"message": "Application creation business logic is not implemented yet."}


@router.get("")
def list_applications_placeholder() -> dict[str, str]:
    return {"message": "Application business logic is not implemented yet."}


@router.get("/{application_id}")
def read_application_placeholder(application_id: int) -> dict[str, str | int]:
    return {
        "application_id": application_id,
        "message": "Application detail business logic is not implemented yet.",
    }


@router.patch("/{application_id}")
def update_application_placeholder(application_id: int) -> dict[str, str | int]:
    return {
        "application_id": application_id,
        "message": "Application update business logic is not implemented yet.",
    }


@router.delete("/{application_id}")
def delete_application_placeholder(application_id: int) -> dict[str, str | int]:
    return {
        "application_id": application_id,
        "message": "Application delete business logic is not implemented yet.",
    }
