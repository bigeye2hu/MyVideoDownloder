from fastapi import APIRouter, Query, HTTPException
import os
import httpx
from crawlers.douyin.web.web_crawler import DouyinWebCrawler as _DouyinWebCrawler


router = APIRouter()
_crawler = _DouyinWebCrawler()


def _get_tikhub_base() -> str:
    base = os.getenv("TIKHUB_API_BASE", "https://api.tikhub.io")
    return base.rstrip("/")


def _get_tikhub_key() -> str:
    return os.getenv("TIKHUB_API_KEY", "")


@router.get("/v3/fetch_one_video", summary="Proxy TikHub fetch_one_video")
async def fetch_one_video(aweme_id: str = Query(..., description="抖音作品ID")):
    api_key = _get_tikhub_key()
    if not api_key:
        raise HTTPException(status_code=500, detail="Server misconfigured: TIKHUB_API_KEY missing")

    base = _get_tikhub_base()
    url = f"{base}/api/v1/douyin/app/v3/fetch_one_video"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "accept": "application/json",
    }

    params = {"aweme_id": aweme_id}

    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            resp = await cli.get(url, headers=headers, params=params)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"TikHub upstream error: {exc}")

    if resp.status_code >= 400:
        # 透传上游错误，便于前端准确提示
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


@router.get("/v3/fetch_one_video_by_url", summary="传入抖音链接，自动解析并代理TikHub")
async def fetch_one_video_by_url(url: str = Query(..., description="抖音视频链接，如 https://www.douyin.com/video/XXXXXXXXXXXX")):
    try:
        aweme_id = await _crawler.get_aweme_id(url)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Parse aweme_id failed: {exc}")

    if not aweme_id:
        raise HTTPException(status_code=400, detail="aweme_id not found from url")

    # 复用上面的代理逻辑
    return await fetch_one_video(aweme_id=aweme_id)


