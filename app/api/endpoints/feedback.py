# -*- coding: utf-8 -*-
"""
用户反馈API端点
"""
import time
import json
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.db.database import get_db_connection
from app.services.metrics_service import MetricsService

router = APIRouter()


class DeviceInfo(BaseModel):
    """设备信息"""
    app_version: Optional[str] = None
    ios_version: Optional[str] = None
    device_model: Optional[str] = None


class FeedbackRequest(BaseModel):
    """反馈请求"""
    type: str = Field(default="其他", description="反馈类型：功能建议 | 问题反馈 | 其他")
    content: str = Field(..., min_length=1, max_length=500, description="反馈内容，最长500字")
    contact: Optional[str] = Field(default=None, description="联系方式（选填）")
    device_info: Optional[DeviceInfo] = Field(default=None, description="设备信息（选填）")
    user_id: Optional[str] = Field(default=None, description="用户ID（选填）")
    timestamp: Optional[str] = Field(default=None, description="时间戳（选填）")


class FeedbackResponse(BaseModel):
    """反馈响应"""
    success: bool
    message: str
    feedback_id: Optional[str] = None


@router.post("/feedback", response_model=FeedbackResponse, summary="提交用户反馈")
async def submit_feedback(request: FeedbackRequest):
    """
    提交用户反馈
    
    - **type**: 反馈类型（功能建议 | 问题反馈 | 其他）
    - **content**: 反馈内容（必填，最长500字）
    - **contact**: 联系方式（选填）
    - **device_info**: 设备信息（选填）
    - **user_id**: 用户ID（选填）
    - **timestamp**: 时间戳（选填）
    """
    start_time = time.time()
    status_code = 200
    error_msg = None
    
    try:
        # 验证反馈类型
        valid_types = ["功能建议", "问题反馈", "其他"]
        if request.type not in valid_types:
            status_code = 400
            error_msg = f"反馈类型无效，必须是：{', '.join(valid_types)}"
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 生成反馈ID
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # 处理时间戳
        if request.timestamp:
            try:
                datetime.fromisoformat(request.timestamp.replace('Z', '+00:00'))
            except:
                request.timestamp = datetime.utcnow().isoformat()
        else:
            request.timestamp = datetime.utcnow().isoformat()
        
        received_at = datetime.utcnow().isoformat()
        
        # 处理设备信息
        device_info_str = None
        if request.device_info:
            device_info_str = json.dumps(request.device_info.dict(), ensure_ascii=False)
        
        # 保存到数据库
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO feedbacks (
                    id, type, content, contact, device_info, 
                    lc_uid, timestamp, received_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback_id,
                request.type,
                request.content,
                request.contact,
                device_info_str,
                request.user_id,
                request.timestamp,
                received_at,
                'pending'  # pending: 待处理, processed: 已处理, archived: 已归档
            ))
            conn.commit()
        
        return FeedbackResponse(
            success=True,
            message="反馈提交成功",
            feedback_id=feedback_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        status_code = 500
        error_msg = str(e)
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")
    finally:
        latency_ms = int((time.time() - start_time) * 1000)
        MetricsService.record_api_call(
            endpoint="/api/feedback",
            method="POST",
            status_code=status_code,
            latency_ms=latency_ms,
            lc_uid=request.user_id,
            error_message=error_msg
        )

