from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def create_export():
    return {"message": "TODO: create export"}


@router.get("/{export_id}")
async def download_export(export_id: str):
    return {"message": f"TODO: download export {export_id}"}
