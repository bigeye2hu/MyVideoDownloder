# -*- coding: utf-8 -*-
"""
积分服务 - 处理积分查询、扣除、返还等业务逻辑
"""
import logging
from datetime import datetime
from typing import Optional
from app.db.database import get_db_connection, get_or_create_user

logger = logging.getLogger(__name__)


class CreditService:
    """积分服务类"""
    
    @staticmethod
    def get_balance(lc_uid: str) -> int:
        """
        获取用户积分余额
        
        Args:
            lc_uid: LeanCloud用户ID
            
        Returns:
            积分余额
        """
        user = get_or_create_user(lc_uid)
        return user["credits_balance"]
    
    @staticmethod
    def deduct_credits(lc_uid: str, amount: int, reason: str, ref_id: Optional[str] = None) -> bool:
        """
        扣除积分（事务性操作）
        
        Args:
            lc_uid: LeanCloud用户ID
            amount: 扣除金额（正数）
            reason: 扣除原因
            ref_id: 关联ID（如job_id）
            
        Returns:
            是否成功
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 检查余额
                cursor.execute(
                    "SELECT credits_balance FROM users WHERE lc_uid = ?",
                    (lc_uid,)
                )
                row = cursor.fetchone()
                
                if not row:
                    logger.error(f"用户不存在: {lc_uid}")
                    return False
                
                current_balance = row["credits_balance"]
                
                if current_balance < amount:
                    logger.warning(f"积分不足: {lc_uid}, 余额: {current_balance}, 需要: {amount}")
                    return False
                
                # 扣除积分
                now = datetime.utcnow().isoformat()
                new_balance = current_balance - amount
                
                cursor.execute("""
                UPDATE users 
                SET credits_balance = ?, updated_at = ?
                WHERE lc_uid = ?
                """, (new_balance, now, lc_uid))
                
                # 记录流水（负数）
                cursor.execute("""
                INSERT INTO credit_ledger (lc_uid, delta, reason, ref_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """, (lc_uid, -amount, reason, ref_id, now))
                
                conn.commit()
                
                logger.info(f"积分扣除成功: {lc_uid}, 金额: {amount}, 原因: {reason}, 新余额: {new_balance}")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"积分扣除失败: {lc_uid}, 错误: {e}")
                return False
    
    @staticmethod
    def refund_credits(lc_uid: str, amount: int, reason: str, ref_id: Optional[str] = None) -> bool:
        """
        返还积分（下载失败时调用）
        
        Args:
            lc_uid: LeanCloud用户ID
            amount: 返还金额（正数）
            reason: 返还原因
            ref_id: 关联ID（如job_id）
            
        Returns:
            是否成功
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            try:
                now = datetime.utcnow().isoformat()
                
                # 增加积分
                cursor.execute("""
                UPDATE users 
                SET credits_balance = credits_balance + ?, updated_at = ?
                WHERE lc_uid = ?
                """, (amount, now, lc_uid))
                
                # 记录流水（正数）
                cursor.execute("""
                INSERT INTO credit_ledger (lc_uid, delta, reason, ref_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """, (lc_uid, amount, reason, ref_id, now))
                
                conn.commit()
                
                logger.info(f"积分返还成功: {lc_uid}, 金额: {amount}, 原因: {reason}")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"积分返还失败: {lc_uid}, 错误: {e}")
                return False
    
    @staticmethod
    def get_ledger(lc_uid: str, limit: int = 50) -> list:
        """
        获取用户积分流水记录
        
        Args:
            lc_uid: LeanCloud用户ID
            limit: 返回记录数限制
            
        Returns:
            流水记录列表
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
            SELECT * FROM credit_ledger
            WHERE lc_uid = ?
            ORDER BY created_at DESC
            LIMIT ?
            """, (lc_uid, limit))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

