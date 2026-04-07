from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_leads():
    return {"message": "TODO: list leads"}


@router.get("/{lead_id}")
async def get_lead(lead_id: str):
    return {"message": f"TODO: get lead {lead_id}"}
