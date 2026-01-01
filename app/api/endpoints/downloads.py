# -*- coding: utf-8 -*-
"""
下载管理API端点
"""
import httpx
import time
from fastapi import APIRouter, HTTPException, Header as HeaderParam
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.download_service import DownloadService
from app.services.credit_service import CreditService
from app.services.auth_service import AuthService
from app.services.metrics_service import MetricsService
import os

router = APIRouter()


class DownloadStartRequest(BaseModel):
    """下载请求"""
    url: str


class DownloadStartResponse(BaseModel):
    """下载响应"""
    job_id: str
    platform: str
    cost_credits: int
    status: str
    message: str
    video_info: Optional[Dict[str, Any]] = None  # 视频元信息（标题、封面、下载链接等）


class DownloadStatusResponse(BaseModel):
    """下载状态响应"""
    job_id: str
    lc_uid: str
    url: str
    platform: str
    cost_credits: int
    status: str
    confirmed: int = 0  # 0=未确认, 1=已确认, -1=已取消
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str


class ConfirmRequest(BaseModel):
    """确认请求"""
    job_id: str


class ConfirmResponse(BaseModel):
    """确认响应"""
    success: bool
    message: str
    credits_deducted: Optional[int] = None
    credits_refunded: Optional[int] = None
    video_info: Optional[Dict[str, Any]] = None  # 确认后返回完整视频信息（含下载链接）


@router.post("/start", response_model=DownloadStartResponse, summary="发起下载任务")
async def start_download(
    request: DownloadStartRequest,
    x_lc_uid: str = HeaderParam(alias="X-LC-UID"),
    x_lc_session: str = HeaderParam(alias="X-LC-Session", default="")
):
    """
    发起视频下载任务（同步获取视频信息）
    
    **流程**：
    1. 验证用户身份
    2. 校验积分余额
    3. 冻结积分
    4. **同步调用第三方API获取视频信息**
    5. 返回视频元信息给App展示
    
    **后续操作**：
    - 用户确认 → 调用 `/api/downloads/confirm` → 积分扣除
    - 用户取消 → 调用 `/api/downloads/cancel` → 积分解冻
    
    **扣分规则**：
    - 抖音: 10分
    - 其他平台: 20分
    """
    start_time = time.time()
    status_code = 200
    error_msg = None
    
    try:
        # 验证身份
        valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
        if not valid:
            status_code = 401
            error_msg = f"身份验证失败: {error}"
            raise HTTPException(status_code=401, detail=error_msg)
        
        # 检查可用余额（总余额 - 已冻结）
        available = CreditService.get_available_balance(x_lc_uid)
        platform = DownloadService.detect_platform(request.url)
        cost = DownloadService.get_cost_for_platform(platform)
        
        if available < cost:
            status_code = 402
            error_msg = f"积分不足。可用余额: {available}, 需要: {cost}"
            raise HTTPException(status_code=402, detail=error_msg)
        
        # 创建任务并预扣积分
        job = DownloadService.create_download_job(x_lc_uid, request.url)
        
        if not job:
            status_code = 500
            error_msg = "创建下载任务失败"
            raise HTTPException(status_code=500, detail=error_msg)
        
        # 同步调用第三方API获取视频信息（只调用1次）
        video_info = None
        try:
            if platform == "douyin":
                video_info = await call_douyin_api(request.url)
                # 保存视频信息到任务
                DownloadService.update_job_status(
                    job_id=job["job_id"],
                    status="pending_confirm",  # 等待用户确认
                    result_data=video_info
                )
            else:
                raise Exception(f"暂不支持平台: {platform}")
        except Exception as e:
            # 解析失败，解冻积分
            DownloadService.update_job_status(
                job_id=job["job_id"],
                status="failed",
                error_message=str(e)
            )
            status_code = 500
            error_msg = f"视频解析失败: {str(e)}"
            raise HTTPException(status_code=500, detail=error_msg)
        
        return DownloadStartResponse(
            job_id=job["job_id"],
            platform=platform,
            cost_credits=cost,
            status="pending_confirm",
            message="视频解析成功，积分已冻结。请展示视频信息供用户确认，确认后调用confirm接口",
            video_info=video_info
        )
    except HTTPException:
        raise
    except Exception as e:
        status_code = 500
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/downloads/start",
            method="POST",
            status_code=status_code,
            latency_ms=latency_ms,
            lc_uid=x_lc_uid,
            error_message=error_msg
        )


@router.get("/status", response_model=DownloadStatusResponse, summary="查询下载状态")
async def get_download_status(
    job_id: str,
    x_lc_uid: str = HeaderParam(alias="X-LC-UID"),
    x_lc_session: str = HeaderParam(alias="X-LC-Session", default="")
):
    """
    查询下载任务状态
    
    **认证**: 通过Header的X-LC-UID和X-LC-Session验证用户身份
    
    **状态说明**：
    - `running`: 下载中
    - `succeeded`: 下载成功（包含result_data）
    - `failed`: 下载失败（积分已返还，包含error_message）
    """
    start_time = time.time()
    status_code = 200
    error_msg = None
    
    try:
        # 验证身份
        valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
        if not valid:
            status_code = 401
            error_msg = f"身份验证失败: {error}"
            raise HTTPException(status_code=401, detail=error_msg)
        
        job = DownloadService.get_job_status(job_id)
        
        if not job:
            status_code = 404
            error_msg = "任务不存在"
            raise HTTPException(status_code=404, detail=error_msg)
        
        # 验证任务所属用户
        if job["lc_uid"] != x_lc_uid:
            status_code = 403
            error_msg = "无权访问此任务"
            raise HTTPException(status_code=403, detail=error_msg)
        
        return DownloadStatusResponse(**job)
    except HTTPException:
        raise
    except Exception as e:
        status_code = 500
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/downloads/status",
            method="GET",
            status_code=status_code,
            latency_ms=latency_ms,
            lc_uid=x_lc_uid,
            error_message=error_msg
        )


@router.post("/confirm", response_model=ConfirmResponse, summary="确认下载成功")
async def confirm_download(
    request: ConfirmRequest,
    x_lc_uid: str = HeaderParam(alias="X-LC-UID"),
    x_lc_session: str = HeaderParam(alias="X-LC-Session", default="")
):
    """
    确认下载成功（客户端调用）
    
    **调用时机**：客户端在文件下载并保存到相册成功后调用
    
    **效果**：将冻结的积分真正扣除
    
    **注意**：
    - 只有状态为 succeeded 的任务才能确认
    - 每个任务只能确认一次
    """
    start_time = time.time()
    status_code = 200
    error_msg = None
    
    try:
        # 验证身份
        valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
        if not valid:
            status_code = 401
            error_msg = f"身份验证失败: {error}"
            raise HTTPException(status_code=401, detail=error_msg)
        
        result = DownloadService.confirm_download(request.job_id, x_lc_uid)
        
        if not result["success"]:
            status_code = 400
            error_msg = result["message"]
            raise HTTPException(status_code=400, detail=error_msg)
        
        return ConfirmResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        status_code = 500
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/downloads/confirm",
            method="POST",
            status_code=status_code,
            latency_ms=latency_ms,
            lc_uid=x_lc_uid,
            error_message=error_msg
        )


@router.post("/cancel", response_model=ConfirmResponse, summary="取消下载")
async def cancel_download(
    request: ConfirmRequest,
    x_lc_uid: str = HeaderParam(alias="X-LC-UID"),
    x_lc_session: str = HeaderParam(alias="X-LC-Session", default="")
):
    """
    取消下载（客户端调用）
    
    **调用时机**：
    - 客户端下载文件失败时
    - 用户主动取消下载时
    
    **效果**：解冻积分，返还到可用余额
    
    **注意**：
    - 已确认的任务无法取消
    - 每个任务只能取消一次
    """
    start_time = time.time()
    status_code = 200
    error_msg = None
    
    try:
        # 验证身份
        valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
        if not valid:
            status_code = 401
            error_msg = f"身份验证失败: {error}"
            raise HTTPException(status_code=401, detail=error_msg)
        
        result = DownloadService.cancel_download(request.job_id, x_lc_uid)
        
        if not result["success"]:
            status_code = 400
            error_msg = result["message"]
            raise HTTPException(status_code=400, detail=error_msg)
        
        return ConfirmResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        status_code = 500
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/downloads/cancel",
            method="POST",
            status_code=status_code,
            latency_ms=latency_ms,
            lc_uid=x_lc_uid,
            error_message=error_msg
        )


async def call_douyin_api(url: str) -> Dict[str, Any]:
    """
    调用抖音解析API
    
    Args:
        url: 抖音视频链接
        
    Returns:
        API响应数据
    """
    # 获取TikHub配置
    api_key = os.getenv("TIKHUB_API_KEY", "")
    if not api_key:
        raise Exception("TIKHUB_API_KEY未配置")
    
    base_url = os.getenv("TIKHUB_API_BASE", "https://api.tikhub.io")
    
    # 先解析aweme_id
    from crawlers.douyin.web.web_crawler import DouyinWebCrawler
    crawler = DouyinWebCrawler()
    aweme_id = await crawler.get_aweme_id(url)
    
    if not aweme_id:
        raise Exception("无法解析视频ID")
    
    # 调用TikHub API
    headers = {
        "Authorization": f"Bearer {api_key}",
        "accept": "application/json",
    }
    
    api_url = f"{base_url.rstrip('/')}/api/v1/douyin/app/v3/fetch_one_video"
    params = {"aweme_id": aweme_id}
    
    # 记录外部API调用
    start_time = time.time()
    status_code = 200
    error_msg = None
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(api_url, headers=headers, params=params)
            status_code = resp.status_code
            
            if resp.status_code >= 400:
                error_msg = f"TikHub API错误: {resp.status_code}, {resp.text}"
    except Exception as e:
        status_code = 500
        error_msg = str(e)
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
        raise
    
    # 记录调用
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
    
    if status_code >= 400:
        raise Exception(error_msg)
    
    return resp.json()

