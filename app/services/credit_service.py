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
    
    @staticmethod
    def freeze_credits(lc_uid: str, amount: int, ref_id: Optional[str] = None) -> bool:
        """
        冻结积分（预占，不真正扣除）
        
        Args:
            lc_uid: LeanCloud用户ID
            amount: 冻结金额（正数）
            ref_id: 关联ID（如job_id）
            
        Returns:
            是否成功
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 检查可用余额（余额 - 已冻结）
                cursor.execute(
                    "SELECT credits_balance, credits_frozen FROM users WHERE lc_uid = ?",
                    (lc_uid,)
                )
                row = cursor.fetchone()
                
                if not row:
                    logger.error(f"用户不存在: {lc_uid}")
                    return False
                
                current_balance = row["credits_balance"]
                current_frozen = row["credits_frozen"] or 0
                available = current_balance - current_frozen
                
                if available < amount:
                    logger.warning(f"可用积分不足: {lc_uid}, 余额: {current_balance}, 已冻结: {current_frozen}, 可用: {available}, 需要: {amount}")
                    return False
                
                # 增加冻结金额
                now = datetime.utcnow().isoformat()
                new_frozen = current_frozen + amount
                
                cursor.execute("""
                UPDATE users 
                SET credits_frozen = ?, updated_at = ?
                WHERE lc_uid = ?
                """, (new_frozen, now, lc_uid))
                
                conn.commit()
                
                logger.info(f"积分冻结成功: {lc_uid}, 金额: {amount}, ref_id: {ref_id}, 新冻结总额: {new_frozen}")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"积分冻结失败: {lc_uid}, 错误: {e}")
                return False
    
    @staticmethod
    def confirm_deduct(lc_uid: str, amount: int, reason: str, ref_id: Optional[str] = None) -> bool:
        """
        确认扣除（将冻结的积分真正扣除）
        
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
                now = datetime.utcnow().isoformat()
                
                # 减少余额和冻结金额
                cursor.execute("""
                UPDATE users 
                SET credits_balance = credits_balance - ?, 
                    credits_frozen = credits_frozen - ?,
                    updated_at = ?
                WHERE lc_uid = ?
                """, (amount, amount, now, lc_uid))
                
                # 记录流水（负数）
                cursor.execute("""
                INSERT INTO credit_ledger (lc_uid, delta, reason, ref_id, created_at)
                VALUES (?, ?, ?, ?, ?)
                """, (lc_uid, -amount, reason, ref_id, now))
                
                conn.commit()
                
                logger.info(f"确认扣除成功: {lc_uid}, 金额: {amount}, 原因: {reason}")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"确认扣除失败: {lc_uid}, 错误: {e}")
                return False
    
    @staticmethod
    def unfreeze_credits(lc_uid: str, amount: int, ref_id: Optional[str] = None) -> bool:
        """
        解冻积分（取消预占，积分返还可用）
        
        Args:
            lc_uid: LeanCloud用户ID
            amount: 解冻金额（正数）
            ref_id: 关联ID（如job_id）
            
        Returns:
            是否成功
        """
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            try:
                now = datetime.utcnow().isoformat()
                
                # 减少冻结金额
                cursor.execute("""
                UPDATE users 
                SET credits_frozen = MAX(0, credits_frozen - ?),
                    updated_at = ?
                WHERE lc_uid = ?
                """, (amount, now, lc_uid))
                
                conn.commit()
                
                logger.info(f"积分解冻成功: {lc_uid}, 金额: {amount}, ref_id: {ref_id}")
                return True
                
            except Exception as e:
                conn.rollback()
                logger.error(f"积分解冻失败: {lc_uid}, 错误: {e}")
                return False
    
    @staticmethod
    def get_available_balance(lc_uid: str) -> int:
        """
        获取可用余额（总余额 - 冻结金额）
        
        Args:
            lc_uid: LeanCloud用户ID
            
        Returns:
            可用积分
        """
        user = get_or_create_user(lc_uid)
        frozen = user.get("credits_frozen", 0) or 0
        return user["credits_balance"] - frozen

