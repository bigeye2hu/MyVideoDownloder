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
        创建下载任务并冻结积分（延迟扣分模式）
        
        积分流程：
        1. 创建任务时：冻结积分（预占，不真正扣除）
        2. 解析成功后：等待客户端确认
        3. 客户端确认下载成功：真正扣除积分
        4. 客户端取消或超时：解冻积分（返还）
        
        Args:
            lc_uid: LeanCloud用户ID
            url: 视频链接
            
        Returns:
            任务信息或None（余额不足）
        """
        job_id = str(uuid.uuid4())
        platform = DownloadService.detect_platform(url)
        cost = DownloadService.get_cost_for_platform(platform)
        
        # 冻结积分（预占，不真正扣除）
        success = CreditService.freeze_credits(
            lc_uid=lc_uid,
            amount=cost,
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
                (job_id, lc_uid, url, platform, cost_credits, status, confirmed, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (job_id, lc_uid, url, platform, cost, "running", 0, now, now))
                
                conn.commit()
                
                logger.info(f"下载任务创建成功: {job_id}, 用户: {lc_uid}, 平台: {platform}, 冻结积分: {cost}")
                
                return {
                    "job_id": job_id,
                    "lc_uid": lc_uid,
                    "url": url,
                    "platform": platform,
                    "cost_credits": cost,
                    "status": "running",
                    "confirmed": 0,
                    "created_at": now
                }
                
            except Exception as e:
                conn.rollback()
                # 回滚积分冻结
                CreditService.unfreeze_credits(
                    lc_uid=lc_uid,
                    amount=cost,
                    ref_id=job_id
                )
                logger.error(f"下载任务创建失败: {e}")
                return None
    
    @staticmethod
    def update_job_status(job_id: str, status: str, result_data: Optional[Dict] = None, 
                         error_message: Optional[str] = None):
        """
        更新任务状态（延迟扣分模式）
        
        注意：
        - 解析失败(failed)时：解冻积分（返还）
        - 解析成功(succeeded)时：不扣积分，等待客户端确认
        
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
                SELECT lc_uid, cost_credits, status, confirmed FROM download_jobs 
                WHERE job_id = ?
                """, (job_id,))
                
                row = cursor.fetchone()
                if not row:
                    logger.error(f"任务不存在: {job_id}")
                    return
                
                lc_uid = row["lc_uid"]
                cost_credits = row["cost_credits"]
                old_status = row["status"]
                confirmed = row["confirmed"]
                
                # 如果解析失败，解冻积分
                if status == "failed" and old_status == "running" and confirmed == 0:
                    CreditService.unfreeze_credits(
                        lc_uid=lc_uid,
                        amount=cost_credits,
                        ref_id=job_id
                    )
                    logger.info(f"解析失败，积分已解冻: {job_id}")
                
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
    
    @staticmethod
    def confirm_download(job_id: str, lc_uid: str) -> Dict[str, Any]:
        """
        确认下载成功（客户端调用）
        
        客户端在文件下载并保存成功后调用此方法，真正扣除积分
        
        Args:
            job_id: 任务ID
            lc_uid: 用户ID（用于验证权限）
            
        Returns:
            {"success": bool, "message": str}
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            try:
                # 获取任务信息
                cursor.execute("""
                SELECT lc_uid, cost_credits, status, confirmed FROM download_jobs 
                WHERE job_id = ?
                """, (job_id,))
                
                row = cursor.fetchone()
                if not row:
                    return {"success": False, "message": "任务不存在"}
                
                if row["lc_uid"] != lc_uid:
                    return {"success": False, "message": "无权操作此任务"}
                
                if row["confirmed"] != 0:
                    return {"success": False, "message": "任务已确认或已取消"}
                
                if row["status"] != "succeeded":
                    return {"success": False, "message": "任务未完成，无法确认"}
                
                cost_credits = row["cost_credits"]
                
                # 真正扣除积分（从冻结转为扣除）
                success = CreditService.confirm_deduct(
                    lc_uid=lc_uid,
                    amount=cost_credits,
                    reason="download_confirmed",
                    ref_id=job_id
                )
                
                if not success:
                    return {"success": False, "message": "积分扣除失败"}
                
                # 更新任务确认状态
                cursor.execute("""
                UPDATE download_jobs 
                SET confirmed = 1, updated_at = ?
                WHERE job_id = ?
                """, (now, job_id))
                
                conn.commit()
                
                logger.info(f"下载确认成功，积分已扣除: {job_id}, 用户: {lc_uid}, 积分: {cost_credits}")
                
                return {"success": True, "message": "确认成功，积分已扣除", "credits_deducted": cost_credits}
                
            except Exception as e:
                conn.rollback()
                logger.error(f"下载确认失败: {job_id}, {e}")
                return {"success": False, "message": f"确认失败: {str(e)}"}
    
    @staticmethod
    def cancel_download(job_id: str, lc_uid: str) -> Dict[str, Any]:
        """
        取消下载（客户端调用）
        
        客户端在下载失败或用户取消时调用，解冻积分
        
        Args:
            job_id: 任务ID
            lc_uid: 用户ID（用于验证权限）
            
        Returns:
            {"success": bool, "message": str}
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            now = datetime.utcnow().isoformat()
            
            try:
                # 获取任务信息
                cursor.execute("""
                SELECT lc_uid, cost_credits, status, confirmed FROM download_jobs 
                WHERE job_id = ?
                """, (job_id,))
                
                row = cursor.fetchone()
                if not row:
                    return {"success": False, "message": "任务不存在"}
                
                if row["lc_uid"] != lc_uid:
                    return {"success": False, "message": "无权操作此任务"}
                
                if row["confirmed"] != 0:
                    return {"success": False, "message": "任务已确认或已取消"}
                
                cost_credits = row["cost_credits"]
                
                # 解冻积分
                CreditService.unfreeze_credits(
                    lc_uid=lc_uid,
                    amount=cost_credits,
                    ref_id=job_id
                )
                
                # 更新任务确认状态为取消
                cursor.execute("""
                UPDATE download_jobs 
                SET confirmed = -1, updated_at = ?
                WHERE job_id = ?
                """, (now, job_id))
                
                conn.commit()
                
                logger.info(f"下载取消，积分已解冻: {job_id}, 用户: {lc_uid}, 积分: {cost_credits}")
                
                return {"success": True, "message": "取消成功，积分已返还", "credits_refunded": cost_credits}
                
            except Exception as e:
                conn.rollback()
                logger.error(f"下载取消失败: {job_id}, {e}")
                return {"success": False, "message": f"取消失败: {str(e)}"}

