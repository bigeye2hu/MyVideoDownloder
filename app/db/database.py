# -*- coding: utf-8 -*-
"""
数据库初始化和连接管理
"""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# 数据库文件路径 - 挂载到宿主机
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'credits.db')

# 确保数据目录存在
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_database():
    """初始化数据库，创建所有必需的表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. 用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            lc_uid TEXT PRIMARY KEY,
            credits_balance INTEGER NOT NULL DEFAULT 0,
            credits_frozen INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)
        
        # 添加credits_frozen列（如果不存在）
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN credits_frozen INTEGER NOT NULL DEFAULT 0")
        except:
            pass  # 列已存在
        
        # 2. 积分流水表（强烈要求）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS credit_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lc_uid TEXT NOT NULL,
            delta INTEGER NOT NULL,
            reason TEXT NOT NULL,
            ref_id TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (lc_uid) REFERENCES users(lc_uid)
        )
        """)
        
        # 为流水表创建索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_credit_ledger_lc_uid 
        ON credit_ledger(lc_uid)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_credit_ledger_created_at 
        ON credit_ledger(created_at)
        """)
        
        # 3. IAP交易表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS iap_transactions (
            transaction_id TEXT PRIMARY KEY,
            lc_uid TEXT NOT NULL,
            product_id TEXT NOT NULL,
            credits INTEGER NOT NULL,
            signed_transaction TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (lc_uid) REFERENCES users(lc_uid)
        )
        """)
        
        # 4. 下载任务表
        # status: running(解析中) / succeeded(解析成功) / failed(解析失败)
        # confirmed: 0(未确认) / 1(已确认下载成功) / -1(已取消/超时)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS download_jobs (
            job_id TEXT PRIMARY KEY,
            lc_uid TEXT NOT NULL,
            url TEXT NOT NULL,
            platform TEXT NOT NULL,
            cost_credits INTEGER NOT NULL,
            status TEXT NOT NULL,
            confirmed INTEGER NOT NULL DEFAULT 0,
            result_data TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (lc_uid) REFERENCES users(lc_uid)
        )
        """)
        
        # 添加confirmed列（如果不存在）
        try:
            cursor.execute("ALTER TABLE download_jobs ADD COLUMN confirmed INTEGER NOT NULL DEFAULT 0")
        except:
            pass  # 列已存在
        
        # 为下载任务表创建索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_download_jobs_lc_uid 
        ON download_jobs(lc_uid)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_download_jobs_status 
        ON download_jobs(status)
        """)
        
        # 5. API调用监控表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS api_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            endpoint TEXT NOT NULL,
            method TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            latency_ms INTEGER NOT NULL,
            is_external INTEGER NOT NULL DEFAULT 0,
            external_api TEXT,
            lc_uid TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL
        )
        """)
        
        # 为API监控表创建索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_metrics_endpoint 
        ON api_metrics(endpoint)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_metrics_created_at 
        ON api_metrics(created_at)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_api_metrics_is_external 
        ON api_metrics(is_external)
        """)
        
        # 6. 用户反馈表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedbacks (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            content TEXT NOT NULL,
            contact TEXT,
            device_info TEXT,
            lc_uid TEXT,
            timestamp TEXT NOT NULL,
            received_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            FOREIGN KEY (lc_uid) REFERENCES users(lc_uid)
        )
        """)
        
        # 为反馈表创建索引
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedbacks_lc_uid 
        ON feedbacks(lc_uid)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedbacks_created_at 
        ON feedbacks(received_at)
        """)
        
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_feedbacks_status 
        ON feedbacks(status)
        """)
        
        conn.commit()
        logger.info(f"数据库初始化成功: {DB_PATH}")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"数据库初始化失败: {e}")
        raise
    finally:
        conn.close()


@contextmanager
def get_db_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 允许通过列名访问
    try:
        yield conn
    finally:
        conn.close()


def get_or_create_user(lc_uid: str, initial_credits: int = 100) -> dict:
    """
    获取或创建用户，新用户赠送初始积分
    
    Args:
        lc_uid: LeanCloud用户ID
        initial_credits: 新用户初始积分，默认100
    
    Returns:
        用户信息字典
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 检查用户是否存在
        cursor.execute("SELECT * FROM users WHERE lc_uid = ?", (lc_uid,))
        user = cursor.fetchone()
        
        if user:
            return dict(user)
        
        # 创建新用户
        now = datetime.utcnow().isoformat()
        cursor.execute("""
        INSERT INTO users (lc_uid, credits_balance, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """, (lc_uid, initial_credits, now, now))
        
        # 记录积分流水
        cursor.execute("""
        INSERT INTO credit_ledger (lc_uid, delta, reason, ref_id, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (lc_uid, initial_credits, "signup", None, now))
        
        conn.commit()
        
        logger.info(f"新用户创建成功: {lc_uid}, 赠送积分: {initial_credits}")
        
        return {
            "lc_uid": lc_uid,
            "credits_balance": initial_credits,
            "created_at": now,
            "updated_at": now
        }


# 在模块加载时初始化数据库
init_database()

