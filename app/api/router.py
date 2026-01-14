from fastapi import APIRouter
from app.api.endpoints import (
    tiktok_web,
    tiktok_app,
    douyin_web,
    douyin_app,
    bilibili_web,
    hybrid_parsing, ios_shortcut, download,
    credits,
    downloads,
    admin,
    feedback,
)

router = APIRouter()

# TikTok routers
router.include_router(tiktok_web.router, prefix="/tiktok/web", tags=["TikTok-Web-API"])
router.include_router(tiktok_app.router, prefix="/tiktok/app", tags=["TikTok-App-API"])

# Douyin routers
router.include_router(douyin_web.router, prefix="/douyin/web", tags=["Douyin-Web-API"])
router.include_router(douyin_app.router, prefix="/douyin/app", tags=["Douyin-App-API"])

# Bilibili routers
router.include_router(bilibili_web.router, prefix="/bilibili/web", tags=["Bilibili-Web-API"])

# Hybrid routers
router.include_router(hybrid_parsing.router, prefix="/hybrid", tags=["Hybrid-API"])

# iOS_Shortcut routers
router.include_router(ios_shortcut.router, prefix="/ios", tags=["iOS-Shortcut"])

# Download routers
router.include_router(download.router, tags=["Download"])

# Credits & Downloads (V1 商业化积分系统)
router.include_router(credits.router, prefix="/credits", tags=["Credits-API"])
router.include_router(downloads.router, prefix="/downloads", tags=["Downloads-API"])

# Admin (数据库管理)
router.include_router(admin.router, prefix="/admin", tags=["Admin-API"])

# Feedback (用户反馈)
router.include_router(feedback.router, tags=["Feedback-API"])
