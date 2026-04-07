from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


def create_app() -> FastAPI:
    application = FastAPI(
        title="VenderWEB API",
        description="Lead generation platform for SMB web services",
        version="0.1.0",
        debug=settings.app_debug,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from app.api.routers import auth, campaigns, dashboard, exports, leads, verticals

    application.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    application.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])
    application.include_router(leads.router, prefix="/api/leads", tags=["leads"])
    application.include_router(exports.router, prefix="/api/exports", tags=["exports"])
    application.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
    application.include_router(verticals.router, prefix="/api/catalog", tags=["catalog"])

    @application.get("/health")
    async def health():
        return {"status": "ok"}

    return application


app = create_app()
