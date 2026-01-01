# -*- coding: utf-8 -*-
"""
API调用监控服务 - 记录和统计API调用情况
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from app.db.database import get_db_connection

logger = logging.getLogger(__name__)


class MetricsService:
    """API调用监控服务"""
    
    # 数据保留天数
    RETENTION_DAYS = 7
    
    @staticmethod
    def record_api_call(
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: int,
        is_external: bool = False,
        external_api: Optional[str] = None,
        lc_uid: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        记录一次API调用
        
        Args:
            endpoint: 接口路径
            method: HTTP方法
            status_code: 响应状态码
            latency_ms: 响应时间(毫秒)
            is_external: 是否是外部第三方API调用
            external_api: 外部API名称(如 TikHub)
            lc_uid: 调用者用户ID
            error_message: 错误信息(如有)
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                now = datetime.utcnow().isoformat()
                
                cursor.execute("""
                    INSERT INTO api_metrics 
                    (endpoint, method, status_code, latency_ms, is_external, 
                     external_api, lc_uid, error_message, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    endpoint, method, status_code, latency_ms, 
                    1 if is_external else 0, external_api, lc_uid, 
                    error_message, now
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"记录API调用失败: {e}")
    
    @staticmethod
    def get_stats(hours: int = 24) -> Dict[str, Any]:
        """
        获取API调用统计
        
        Args:
            hours: 统计最近多少小时的数据
            
        Returns:
            统计数据字典
        """
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # 总调用次数
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as success,
                       SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors,
                       AVG(latency_ms) as avg_latency
                FROM api_metrics 
                WHERE created_at > ?
            """, (cutoff,))
            row = cursor.fetchone()
            overall = {
                "total": row["total"] or 0,
                "success": row["success"] or 0,
                "errors": row["errors"] or 0,
                "avg_latency_ms": round(row["avg_latency"] or 0, 2)
            }
            
            # 外部API调用统计
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN status_code >= 200 AND status_code < 300 THEN 1 ELSE 0 END) as success,
                       SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors,
                       AVG(latency_ms) as avg_latency
                FROM api_metrics 
                WHERE is_external = 1 AND created_at > ?
            """, (cutoff,))
            row = cursor.fetchone()
            external = {
                "total": row["total"] or 0,
                "success": row["success"] or 0,
                "errors": row["errors"] or 0,
                "avg_latency_ms": round(row["avg_latency"] or 0, 2)
            }
            
            # 按端点分组统计
            cursor.execute("""
                SELECT endpoint, method, 
                       COUNT(*) as count,
                       SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors,
                       AVG(latency_ms) as avg_latency
                FROM api_metrics 
                WHERE created_at > ?
                GROUP BY endpoint, method
                ORDER BY count DESC
                LIMIT 20
            """, (cutoff,))
            by_endpoint = [dict(row) for row in cursor.fetchall()]
            
            # 按外部API分组
            cursor.execute("""
                SELECT external_api, 
                       COUNT(*) as count,
                       SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors,
                       AVG(latency_ms) as avg_latency
                FROM api_metrics 
                WHERE is_external = 1 AND created_at > ?
                GROUP BY external_api
                ORDER BY count DESC
            """, (cutoff,))
            by_external = [dict(row) for row in cursor.fetchall()]
            
            return {
                "hours": hours,
                "overall": overall,
                "external": external,
                "by_endpoint": by_endpoint,
                "by_external_api": by_external
            }
    
    @staticmethod
    def get_recent_calls(
        limit: int = 100,
        is_external: Optional[bool] = None,
        endpoint_filter: Optional[str] = None,
        errors_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取最近的API调用记录
        
        Args:
            limit: 返回数量限制
            is_external: 是否只看外部API
            endpoint_filter: 端点过滤
            errors_only: 是否只看错误
            
        Returns:
            调用记录列表
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM api_metrics WHERE 1=1"
            params = []
            
            if is_external is not None:
                query += " AND is_external = ?"
                params.append(1 if is_external else 0)
            
            if endpoint_filter:
                query += " AND endpoint LIKE ?"
                params.append(f"%{endpoint_filter}%")
            
            if errors_only:
                query += " AND status_code >= 400"
            
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def get_hourly_stats(hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取每小时统计数据(用于图表)
        
        Args:
            hours: 统计最近多少小时
            
        Returns:
            每小时统计列表
        """
        cutoff = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # SQLite中按小时分组
            cursor.execute("""
                SELECT 
                    strftime('%Y-%m-%d %H:00', created_at) as hour,
                    COUNT(*) as total,
                    SUM(CASE WHEN is_external = 1 THEN 1 ELSE 0 END) as external,
                    SUM(CASE WHEN status_code >= 400 THEN 1 ELSE 0 END) as errors,
                    AVG(latency_ms) as avg_latency
                FROM api_metrics 
                WHERE created_at > ?
                GROUP BY strftime('%Y-%m-%d %H', created_at)
                ORDER BY hour ASC
            """, (cutoff,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    @staticmethod
    def cleanup_old_data() -> int:
        """
        清理过期数据(保留RETENTION_DAYS天)
        
        Returns:
            删除的记录数
        """
        cutoff = (datetime.utcnow() - timedelta(days=MetricsService.RETENTION_DAYS)).isoformat()
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM api_metrics WHERE created_at < ?", (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            
            if deleted > 0:
                logger.info(f"清理了 {deleted} 条过期的API监控记录")
            
            return deleted


class MetricsTimer:
    """API调用计时器上下文管理器"""
    
    def __init__(
        self,
        endpoint: str,
        method: str = "GET",
        is_external: bool = False,
        external_api: Optional[str] = None,
        lc_uid: Optional[str] = None
    ):
        self.endpoint = endpoint
        self.method = method
        self.is_external = is_external
        self.external_api = external_api
        self.lc_uid = lc_uid
        self.start_time = None
        self.status_code = 200
        self.error_message = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        latency_ms = int((time.time() - self.start_time) * 1000)
        
        if exc_type is not None:
            self.status_code = 500
            self.error_message = str(exc_val)
        
        MetricsService.record_api_call(
            endpoint=self.endpoint,
            method=self.method,
            status_code=self.status_code,
            latency_ms=latency_ms,
            is_external=self.is_external,
            external_api=self.external_api,
            lc_uid=self.lc_uid,
            error_message=self.error_message
        )
        
        return False  # 不吞掉异常
    
    def set_status(self, status_code: int, error: Optional[str] = None):
        """设置响应状态码"""
        self.status_code = status_code
        self.error_message = error


