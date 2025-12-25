# -*- coding: utf-8 -*-
"""
下载服务 - 处理下载任务创建、状态跟踪、积分扣除等
"""
import uuid
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from app.db.database import get_db_connection
from app.services.credit_service import CreditService

logger = logging.getLogger(__name__)


class DownloadService:
    """下载服务类"""
    
    # 平台扣分配置
    PLATFORM_COSTS = {
        "douyin": 10,
        "tiktok": 20,
        "bilibili": 20,
        "other": 20
    }
    
    @staticmethod
    def detect_platform(url: str) -> str:
        """
        检测视频平台
        
        Args:
            url: 视频链接
            
        Returns:
            平台名称
        """
        url_lower = url.lower()
        
        if "douyin.com" in url_lower or "iesdouyin.com" in url_lower:
            return "douyin"
        elif "tiktok.com" in url_lower:
            return "tiktok"
        elif "bilibili.com" in url_lower:
            return "bilibili"
        else:
            return "other"
    
    @staticmethod
    def get_cost_for_platform(platform: str) -> int:
        """
        获取平台下载所需积分
        
        Args:
            platform: 平台名称
            
        Returns:
            所需积分
        """
        return DownloadService.PLATFORM_COSTS.get(platform, 20)
    
    @staticmethod
    def create_download_job(lc_uid: str, url: str) -> Optional[Dict[str, Any]]:
        """
        创建下载任务并预扣积分
        
        Args:
            lc_uid: LeanCloud用户ID
            url: 视频链接
            
        Returns:
            任务信息或None（余额不足）
        """
        job_id = str(uuid.uuid4())
        platform = DownloadService.detect_platform(url)
        cost = DownloadService.get_cost_for_platform(platform)
        
        # 预扣积分
        success = CreditService.deduct_credits(
            lc_uid=lc_uid,
            amount=cost,
            reason=f"download_{platform}",
            ref_id=job_id
        )
        
        if not success:
            logger.warning(f"积分不足，无法创建下载任务: {lc_uid}, {url}")
            return None
        
        # 创建任务记录
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            try:
                cursor.execute("""
                INSERT INTO download_jobs 
                (job_id, lc_uid, url, platform, cost_credits, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (job_id, lc_uid, url, platform, cost, "running", now, now))
                
                conn.commit()
                
                logger.info(f"下载任务创建成功: {job_id}, 用户: {lc_uid}, 平台: {platform}, 扣分: {cost}")
                
                return {
                    "job_id": job_id,
                    "lc_uid": lc_uid,
                    "url": url,
                    "platform": platform,
                    "cost_credits": cost,
                    "status": "running",
                    "created_at": now
                }
                
            except Exception as e:
                conn.rollback()
                # 回滚积分扣除
                CreditService.refund_credits(
                    lc_uid=lc_uid,
                    amount=cost,
                    reason=f"download_create_failed",
                    ref_id=job_id
                )
                logger.error(f"下载任务创建失败: {e}")
                return None
    
    @staticmethod
    def update_job_status(job_id: str, status: str, result_data: Optional[Dict] = None, 
                         error_message: Optional[str] = None):
        """
        更新任务状态
        
        Args:
            job_id: 任务ID
            status: 新状态 (running/succeeded/failed)
            result_data: 结果数据（成功时）
            error_message: 错误信息（失败时）
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            try:
                # 获取任务信息
                cursor.execute("""
                SELECT lc_uid, cost_credits, status FROM download_jobs 
                WHERE job_id = ?
                """, (job_id,))
                
                row = cursor.fetchone()
                if not row:
                    logger.error(f"任务不存在: {job_id}")
                    return
                
                lc_uid = row["lc_uid"]
                cost_credits = row["cost_credits"]
                old_status = row["status"]
                
                # 如果任务失败，需要返还积分
                if status == "failed" and old_status == "running":
                    CreditService.refund_credits(
                        lc_uid=lc_uid,
                        amount=cost_credits,
                        reason="download_failed",
                        ref_id=job_id
                    )
                    logger.info(f"下载失败，积分已返还: {job_id}")
                
                # 更新任务状态
                result_json = json.dumps(result_data, ensure_ascii=False) if result_data else None
                
                cursor.execute("""
                UPDATE download_jobs 
                SET status = ?, result_data = ?, error_message = ?, updated_at = ?
                WHERE job_id = ?
                """, (status, result_json, error_message, now, job_id))
                
                conn.commit()
                
                logger.info(f"任务状态更新: {job_id}, {old_status} -> {status}")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"任务状态更新失败: {job_id}, {e}")
    
    @staticmethod
    def get_job_status(job_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务状态
        
        Args:
            job_id: 任务ID
            
        Returns:
            任务信息或None
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM download_jobs WHERE job_id = ?
            """, (job_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            job = dict(row)
            
            # 解析结果数据
            if job["result_data"]:
                try:
                    job["result_data"] = json.loads(job["result_data"])
                except:
                    pass
            
            return job

