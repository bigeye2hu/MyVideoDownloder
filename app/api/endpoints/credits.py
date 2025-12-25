# -*- coding: utf-8 -*-
"""
积分管理API端点
"""
from fastapi import APIRouter, HTTPException, Header as HeaderParam
from pydantic import BaseModel
from typing import Optional
from app.services.credit_service import CreditService
from app.services.auth_service import AuthService
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
    # 验证身份
    valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
    if not valid:
        raise HTTPException(status_code=401, detail=f"身份验证失败: {error}")
    
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询余额失败: {str(e)}")


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
    # 验证身份
    valid, error = await AuthService.verify_session(x_lc_uid, x_lc_session)
    if not valid:
        raise HTTPException(status_code=401, detail=f"身份验证失败: {error}")
    
    try:
        items = CreditService.get_ledger(x_lc_uid, limit)
        return LedgerResponse(
            lc_uid=x_lc_uid,
            items=[LedgerItem(**item) for item in items]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询流水失败: {str(e)}")

