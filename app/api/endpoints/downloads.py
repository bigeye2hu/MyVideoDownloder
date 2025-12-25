# -*- coding: utf-8 -*-
"""
下载管理API端点
"""
import asyncio
import httpx
from fastapi import APIRouter, HTTPException, Header as HeaderParam
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.services.download_service import DownloadService
from app.services.credit_service import CreditService
from app.services.auth_service import AuthService
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


@router.post("/start", response_model=DownloadStartResponse, summary="发起下载任务")
async def start_download(
    request: DownloadStartRequest,
    x_lc_uid: str = HeaderParam(alias="X-LC-UID"),
    x_lc_session: str = HeaderParam(alias="X-LC-Session", default="")
):
    """
    发起视频下载任务
    
    服务器会自动完成：
    1. 验证用户身份
    2. 判断平台类型
    3. 计算所需积分
    4. 校验余额是否足够
    5. 预扣（冻结）积分
    6. 异步执行下载任务
    
    **扣分规则**：
    - 抖音: 10分
    - 其他平台: 20分
    
    **注意**：下载成功才最终扣分，失败会自动返还
    """
    # 验证身份
    valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
    if not valid:
        raise HTTPException(status_code=401, detail=f"身份验证失败: {error}")
    
    # 检查可用余额（总余额 - 已冻结）
    available = CreditService.get_available_balance(x_lc_uid)
    platform = DownloadService.detect_platform(request.url)
    cost = DownloadService.get_cost_for_platform(platform)
    
    if available < cost:
        raise HTTPException(
            status_code=402,
            detail=f"积分不足。可用余额: {available}, 需要: {cost}"
        )
    
    # 创建任务并预扣积分
    job = DownloadService.create_download_job(x_lc_uid, request.url)
    
    if not job:
        raise HTTPException(status_code=500, detail="创建下载任务失败")
    
    # 异步执行下载（不阻塞响应）
    asyncio.create_task(execute_download(job["job_id"], request.url, platform))
    
    return DownloadStartResponse(
        job_id=job["job_id"],
        platform=platform,
        cost_credits=cost,
        status="running",
        message="下载任务已创建，积分已冻结。解析成功后请调用confirm接口确认"
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
    # 验证身份
    valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
    if not valid:
        raise HTTPException(status_code=401, detail=f"身份验证失败: {error}")
    
    job = DownloadService.get_job_status(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 验证任务所属用户
    if job["lc_uid"] != x_lc_uid:
        raise HTTPException(status_code=403, detail="无权访问此任务")
    
    return DownloadStatusResponse(**job)


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
    # 验证身份
    valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
    if not valid:
        raise HTTPException(status_code=401, detail=f"身份验证失败: {error}")
    
    result = DownloadService.confirm_download(request.job_id, x_lc_uid)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return ConfirmResponse(**result)


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
    # 验证身份
    valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
    if not valid:
        raise HTTPException(status_code=401, detail=f"身份验证失败: {error}")
    
    result = DownloadService.cancel_download(request.job_id, x_lc_uid)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return ConfirmResponse(**result)


async def execute_download(job_id: str, url: str, platform: str):
    """
    执行实际的下载任务（后台异步）
    
    Args:
        job_id: 任务ID
        url: 视频链接
        platform: 平台类型
    """
    try:
        if platform == "douyin":
            # 调用现有的douyin_app接口
            result = await call_douyin_api(url)
            
            # 更新任务状态为成功
            DownloadService.update_job_status(
                job_id=job_id,
                status="succeeded",
                result_data=result
            )
        else:
            # 其他平台暂不支持
            raise Exception(f"暂不支持平台: {platform}")
            
    except Exception as e:
        # 下载失败，更新状态并返还积分
        DownloadService.update_job_status(
            job_id=job_id,
            status="failed",
            error_message=str(e)
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
    
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(api_url, headers=headers, params=params)
        
        if resp.status_code >= 400:
            raise Exception(f"TikHub API错误: {resp.status_code}, {resp.text}")
        
        return resp.json()

