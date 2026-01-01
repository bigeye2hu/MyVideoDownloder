# -*- coding: utf-8 -*-
"""
积分管理API端点
"""
import time
from fastapi import APIRouter, HTTPException, Header as HeaderParam
from pydantic import BaseModel
from typing import Optional
from app.services.credit_service import CreditService
from app.services.auth_service import AuthService
from app.services.metrics_service import MetricsService
from app.db.database import get_or_create_user

router = APIRouter()


class BalanceResponse(BaseModel):
    """余额查询响应"""
    lc_uid: str
    credits_balance: int      # 总余额
    credits_frozen: int = 0   # 冻结中的积分
    credits_available: int    # 可用余额（总余额 - 冻结）


class LedgerItem(BaseModel):
    """流水记录项"""
    id: int
    lc_uid: str
    delta: int
    reason: str
    ref_id: Optional[str]
    created_at: str


class LedgerResponse(BaseModel):
    """流水查询响应"""
    lc_uid: str
    items: list[LedgerItem]


class AddIAPRequest(BaseModel):
    """IAP充值请求"""
    amount: int
    transaction_id: str
    product_id: str
    reason: str = "IAP购买"


class AddIAPResponse(BaseModel):
    """IAP充值响应"""
    lc_uid: str
    credits_balance: int
    credits_frozen: int = 0


@router.get("/balance", response_model=BalanceResponse, summary="查询积分余额")
async def get_balance(
    x_lc_uid: str = HeaderParam(alias="X-LC-UID"),
    x_lc_session: str = HeaderParam(alias="X-LC-Session", default="")
):
    """
    查询当前登录用户的积分余额
    
    - **认证**: 通过Header的X-LC-UID和X-LC-Session验证用户身份
    - **新用户**: 首次查询会自动创建账户并赠送100积分
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
        
        user = get_or_create_user(x_lc_uid)
        balance = user["credits_balance"]
        frozen = user.get("credits_frozen", 0) or 0
        available = balance - frozen
        return BalanceResponse(
            lc_uid=x_lc_uid, 
            credits_balance=balance,
            credits_frozen=frozen,
            credits_available=available
        )
    except HTTPException:
        raise
    except Exception as e:
        status_code = 500
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=f"查询余额失败: {str(e)}")
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/credits/balance",
            method="GET",
            status_code=status_code,
            latency_ms=latency_ms,
            lc_uid=x_lc_uid,
            error_message=error_msg
        )


@router.get("/ledger", response_model=LedgerResponse, summary="查询积分流水")
async def get_ledger(
    x_lc_uid: str = HeaderParam(alias="X-LC-UID"),
    x_lc_session: str = HeaderParam(alias="X-LC-Session", default=""),
    limit: int = 50
):
    """
    查询用户积分流水记录
    
    - **认证**: 通过Header的X-LC-UID和X-LC-Session验证用户身份
    - **limit**: 返回记录数，默认50条
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
        
        items = CreditService.get_ledger(x_lc_uid, limit)
        return LedgerResponse(
            lc_uid=x_lc_uid,
            items=[LedgerItem(**item) for item in items]
        )
    except HTTPException:
        raise
    except Exception as e:
        status_code = 500
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=f"查询流水失败: {str(e)}")
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/credits/ledger",
            method="GET",
            status_code=status_code,
            latency_ms=latency_ms,
            lc_uid=x_lc_uid,
            error_message=error_msg
        )


@router.post("/add-iap", response_model=AddIAPResponse, summary="IAP充值积分")
async def add_iap_credits(
    request: AddIAPRequest,
    x_lc_uid: str = HeaderParam(alias="X-LC-UID"),
    x_lc_session: str = HeaderParam(alias="X-LC-Session", default="")
):
    """
    IAP购买后添加积分
    
    - **认证**: 通过Header的X-LC-UID和X-LC-Session验证用户身份
    - **防重复**: 通过transaction_id防止重复充值
    - **amount**: 充值积分数量
    - **transaction_id**: Apple IAP交易ID
    - **product_id**: 商品ID（如com.mygolfswingapp.credits.300）
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
        
        # 确保用户存在
        get_or_create_user(x_lc_uid)
        
        # 执行充值
        result = CreditService.add_credits_iap(
            lc_uid=x_lc_uid,
            amount=request.amount,
            transaction_id=request.transaction_id,
            product_id=request.product_id,
            reason=request.reason
        )
        
        if not result["success"]:
            status_code = 400
            error_msg = result["error"]
            raise HTTPException(status_code=400, detail=error_msg)
        
        return AddIAPResponse(
            lc_uid=x_lc_uid,
            credits_balance=result["new_balance"],
            credits_frozen=result["frozen"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        status_code = 500
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=f"充值失败: {str(e)}")
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/credits/add-iap",
            method="POST",
            status_code=status_code,
            latency_ms=latency_ms,
            lc_uid=x_lc_uid,
            error_message=error_msg
        )

