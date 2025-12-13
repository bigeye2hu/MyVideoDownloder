from fastapi import APIRouter
from app.api.endpoints import (
    douyin_app,
)

router = APIRouter()

# Only keep the TikHub proxied Douyin-App endpoint
router.include_router(douyin_app.router, prefix="/douyin/app", tags=["Douyin-App-API(Proxy TikHub)"])
