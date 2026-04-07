from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_campaigns():
    return {"message": "TODO: list campaigns"}


@router.post("/")
async def create_campaign():
    return {"message": "TODO: create campaign"}


@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str):
    return {"message": f"TODO: get campaign {campaign_id}"}
