from fastapi import APIRouter, Query, HTTPException
import os
import time
import httpx
from crawlers.douyin.web.web_crawler import DouyinWebCrawler as _DouyinWebCrawler
from app.services.metrics_service import MetricsService


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
    
    # 记录外部API调用
    start_time = time.time()
    status_code = 200
    error_msg = None

    try:
        async with httpx.AsyncClient(timeout=20) as cli:
            resp = await cli.get(url, headers=headers, params=params)
        status_code = resp.status_code
    except httpx.RequestError as exc:
        status_code = 502
        error_msg = str(exc)
        # 记录失败调用
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/v1/douyin/app/v3/fetch_one_video",
            method="GET",
            status_code=status_code,
            latency_ms=latency_ms,
            is_external=True,
            external_api="TikHub",
            error_message=error_msg
        )
        raise HTTPException(status_code=502, detail=f"TikHub upstream error: {exc}")
    
    # 记录成功/失败调用
    latency_ms = int((time.time() - start_time) * 1000)
    MetricsService.record_api_call(
        endpoint="/api/v1/douyin/app/v3/fetch_one_video",
        method="GET",
        status_code=status_code,
        latency_ms=latency_ms,
        is_external=True,
        external_api="TikHub",
        error_message=resp.text if status_code >= 400 else None
    )

    if resp.status_code >= 400:
        # 透传上游错误，便于前端准确提示
        raise HTTPException(status_code=resp.status_code, detail=resp.text)

    return resp.json()


@router.get("/v3/fetch_one_video_by_url", summary="传入抖音链接，自动解析并代理TikHub")
async def fetch_one_video_by_url(url: str = Query(..., description="抖音视频链接，如 https://www.douyin.com/video/XXXXXXXXXXXX")):
    start_time = time.time()
    status_code = 200
    error_msg = None
    
    try:
        try:
            aweme_id = await _crawler.get_aweme_id(url)
        except Exception as exc:
            status_code = 400
            error_msg = f"Parse aweme_id failed: {exc}"
            raise HTTPException(status_code=400, detail=error_msg)

        if not aweme_id:
            status_code = 400
            error_msg = "aweme_id not found from url"
            raise HTTPException(status_code=400, detail=error_msg)

        # 复用上面的代理逻辑
        return await fetch_one_video(aweme_id=aweme_id)
    except HTTPException:
        raise
    except Exception as e:
        status_code = 500
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/douyin/app/v3/fetch_one_video_by_url",
            method="GET",
            status_code=status_code,
            latency_ms=latency_ms,
            error_message=error_msg
        )


