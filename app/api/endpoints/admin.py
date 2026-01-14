# -*- coding: utf-8 -*-
"""
统一管理后台API端点 - 数据库管理 + API监控
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.db.database import get_db_connection, DB_PATH
from app.services.metrics_service import MetricsService
from datetime import datetime
import json
import os

router = APIRouter()


class UserInfo(BaseModel):
    """用户信息"""
    lc_uid: str
    credits_balance: int
    created_at: str
    updated_at: str


class UpdateCreditsRequest(BaseModel):
    """修改积分请求"""
    lc_uid: str
    new_balance: int
    reason: str = "admin_adjust"


class DownloadJobInfo(BaseModel):
    """下载任务信息"""
    job_id: str
    lc_uid: str
    url: str
    platform: str
    cost_credits: int
    status: str
    error_message: Optional[str]
    created_at: str
    updated_at: str


class LedgerInfo(BaseModel):
    """积分流水信息"""
    id: int
    lc_uid: str
    delta: int
    reason: str
    ref_id: Optional[str]
    created_at: str


# ==================== 用户管理 ====================

@router.get("/users", response_model=List[UserInfo], summary="获取所有用户")
async def get_all_users():
    """获取所有用户及其积分"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/users/{lc_uid}", response_model=UserInfo, summary="获取单个用户")
async def get_user(lc_uid: str):
    """获取单个用户信息"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE lc_uid = ?", (lc_uid,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        return dict(row)


@router.post("/users/update-credits", summary="修改用户积分")
async def update_user_credits(request: UpdateCreditsRequest):
    """直接修改用户积分（管理员操作）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 获取当前余额
        cursor.execute("SELECT credits_balance FROM users WHERE lc_uid = ?", (request.lc_uid,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        old_balance = row["credits_balance"]
        delta = request.new_balance - old_balance
        now = datetime.utcnow().isoformat()
        
        # 更新余额
        cursor.execute("""
            UPDATE users SET credits_balance = ?, updated_at = ?
            WHERE lc_uid = ?
        """, (request.new_balance, now, request.lc_uid))
        
        # 记录流水
        cursor.execute("""
            INSERT INTO credit_ledger (lc_uid, delta, reason, ref_id, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (request.lc_uid, delta, request.reason, None, now))
        
        conn.commit()
        
        return {
            "success": True,
            "lc_uid": request.lc_uid,
            "old_balance": old_balance,
            "new_balance": request.new_balance,
            "delta": delta
        }


@router.delete("/users/{lc_uid}", summary="删除用户")
async def delete_user(lc_uid: str):
    """删除用户及其相关数据"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 删除流水记录
        cursor.execute("DELETE FROM credit_ledger WHERE lc_uid = ?", (lc_uid,))
        # 删除下载任务
        cursor.execute("DELETE FROM download_jobs WHERE lc_uid = ?", (lc_uid,))
        # 删除用户
        cursor.execute("DELETE FROM users WHERE lc_uid = ?", (lc_uid,))
        
        conn.commit()
        
        return {"success": True, "message": f"用户 {lc_uid} 已删除"}


# ==================== 下载任务管理 ====================

@router.get("/downloads", response_model=List[Dict[str, Any]], summary="获取所有下载任务")
async def get_all_downloads(limit: int = Query(default=100, le=500)):
    """获取所有下载任务"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT job_id, lc_uid, url, platform, cost_credits, status, 
                   error_message, created_at, updated_at 
            FROM download_jobs 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/downloads/{job_id}", summary="获取下载任务详情")
async def get_download_detail(job_id: str):
    """获取下载任务详情（含result_data）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM download_jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        job = dict(row)
        if job.get("result_data"):
            try:
                job["result_data"] = json.loads(job["result_data"])
            except:
                pass
        return job


@router.delete("/downloads/{job_id}", summary="删除下载任务")
async def delete_download(job_id: str):
    """删除下载任务"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM download_jobs WHERE job_id = ?", (job_id,))
        conn.commit()
        return {"success": True, "message": f"任务 {job_id} 已删除"}


# ==================== 积分流水 ====================

@router.get("/ledger", response_model=List[LedgerInfo], summary="获取积分流水")
async def get_ledger(
    lc_uid: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """获取积分流水记录"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if lc_uid:
            cursor.execute("""
                SELECT * FROM credit_ledger 
                WHERE lc_uid = ?
                ORDER BY created_at DESC 
                LIMIT ?
            """, (lc_uid, limit))
        else:
            cursor.execute("""
                SELECT * FROM credit_ledger 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ==================== 统计信息 ====================

@router.get("/stats", summary="获取统计信息")
async def get_stats():
    """获取数据库统计信息"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 用户统计
        cursor.execute("SELECT COUNT(*) as count, SUM(credits_balance) as total_credits FROM users")
        user_stats = dict(cursor.fetchone())
        
        # 下载统计
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM download_jobs 
            GROUP BY status
        """)
        download_stats = {row["status"]: row["count"] for row in cursor.fetchall()}
        
        # 流水统计
        cursor.execute("SELECT COUNT(*) as count FROM credit_ledger")
        ledger_count = cursor.fetchone()["count"]
        
        return {
            "db_path": DB_PATH,
            "users": {
                "count": user_stats["count"] or 0,
                "total_credits": user_stats["total_credits"] or 0
            },
            "downloads": download_stats,
            "ledger_count": ledger_count
        }


# ==================== API监控 ====================

# 核心API端点列表
CORE_ENDPOINTS = [
    {"endpoint": "/api/credits/balance", "method": "GET", "description": "查询积分余额", "type": "internal"},
    {"endpoint": "/api/credits/ledger", "method": "GET", "description": "查询积分流水", "type": "internal"},
    {"endpoint": "/api/credits/add-iap", "method": "POST", "description": "IAP充值积分", "type": "internal"},
    {"endpoint": "/api/downloads/start", "method": "POST", "description": "发起下载任务", "type": "internal"},
    {"endpoint": "/api/downloads/status", "method": "GET", "description": "查询下载状态", "type": "internal"},
    {"endpoint": "/api/downloads/confirm", "method": "POST", "description": "确认下载成功", "type": "internal"},
    {"endpoint": "/api/downloads/cancel", "method": "POST", "description": "取消下载", "type": "internal"},
    {"endpoint": "/api/douyin/app/v3/fetch_one_video_by_url", "method": "GET", "description": "获取抖音视频信息", "type": "internal"},
]

EXTERNAL_APIS = [
    {"name": "TikHub", "endpoint": "/api/v1/douyin/app/v3/fetch_one_video", "description": "抖音视频解析（付费，每次调用扣费）"},
]


@router.get("/metrics/endpoints", summary="获取核心端点列表")
async def get_core_endpoints():
    """获取核心API端点和外部API列表"""
    return {
        "core_endpoints": CORE_ENDPOINTS,
        "external_apis": EXTERNAL_APIS
    }


@router.get("/metrics/stats", summary="获取API调用统计")
async def get_metrics_stats(hours: int = Query(default=24, le=168)):
    """获取API调用统计"""
    return MetricsService.get_stats(hours)


@router.get("/metrics/calls", summary="获取最近API调用记录")
async def get_metrics_calls(
    limit: int = Query(default=100, le=500),
    external_only: bool = Query(default=False),
    errors_only: bool = Query(default=False),
    endpoint: Optional[str] = None
):
    """获取最近的API调用记录"""
    return MetricsService.get_recent_calls(
        limit=limit,
        is_external=True if external_only else None,
        endpoint_filter=endpoint,
        errors_only=errors_only
    )


@router.get("/metrics/hourly", summary="获取每小时统计")
async def get_metrics_hourly(hours: int = Query(default=24, le=168)):
    """获取每小时统计数据"""
    return MetricsService.get_hourly_stats(hours)


@router.post("/metrics/cleanup", summary="清理过期数据")
async def cleanup_metrics():
    """清理7天前的监控数据"""
    deleted = MetricsService.cleanup_old_data()
    return {"success": True, "deleted_count": deleted}


# ==================== 用户反馈管理 ====================

@router.get("/feedbacks", summary="获取用户反馈列表")
async def get_feedbacks(
    limit: int = Query(default=100, le=500),
    type_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None
):
    """获取用户反馈列表"""
    import json
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM feedbacks WHERE 1=1"
        params = []
        
        if type_filter:
            query += " AND type = ?"
            params.append(type_filter)
        
        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)
        
        if search:
            query += " AND content LIKE ?"
            params.append(f"%{search}%")
        
        query += " ORDER BY received_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        feedbacks = []
        for row in rows:
            fb = dict(row)
            # 解析设备信息JSON
            if fb.get("device_info"):
                try:
                    fb["device_info"] = json.loads(fb["device_info"])
                except:
                    pass
            feedbacks.append(fb)
        
        return feedbacks


@router.get("/feedbacks/{feedback_id}", summary="获取反馈详情")
async def get_feedback_detail(feedback_id: str):
    """获取反馈详情"""
    import json
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM feedbacks WHERE id = ?", (feedback_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="反馈不存在")
        
        fb = dict(row)
        if fb.get("device_info"):
            try:
                fb["device_info"] = json.loads(fb["device_info"])
            except:
                pass
        return fb


@router.post("/feedbacks/{feedback_id}/status", summary="更新反馈状态")
async def update_feedback_status(
    feedback_id: str,
    status: str = Query(..., description="新状态：pending | processed | archived")
):
    """更新反馈状态"""
    valid_statuses = ["pending", "processed", "archived"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"状态无效，必须是：{', '.join(valid_statuses)}")
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE feedbacks SET status = ? WHERE id = ?", (status, feedback_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="反馈不存在")
        conn.commit()
    
    return {"success": True, "message": f"反馈状态已更新为 {status}"}


@router.delete("/feedbacks/{feedback_id}", summary="删除反馈")
async def delete_feedback(feedback_id: str):
    """删除反馈"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM feedbacks WHERE id = ?", (feedback_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="反馈不存在")
        conn.commit()
    
    return {"success": True, "message": f"反馈 {feedback_id} 已删除"}


# ==================== 管理页面 ====================

@router.get("/", response_class=HTMLResponse, summary="管理页面")
async def admin_page():
    """统一管理后台页面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>管理后台 - MyVideoDownloader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%);
            color: #e4e4e4;
            min-height: 100vh;
        }
        
        /* 顶部导航 */
        .top-nav {
            background: rgba(0,0,0,0.4);
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding: 0 30px;
            display: flex;
            align-items: center;
            height: 60px;
            backdrop-filter: blur(10px);
            position: sticky;
            top: 0;
            z-index: 100;
        }
        .logo {
            font-size: 1.4em;
            font-weight: 700;
            color: #00d9ff;
            margin-right: 40px;
        }
        .main-tabs {
            display: flex;
            gap: 5px;
        }
        .main-tab {
            padding: 18px 24px;
            cursor: pointer;
            color: #888;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
            font-weight: 500;
        }
        .main-tab:hover { color: #ccc; }
        .main-tab.active { 
            color: #00d9ff; 
            border-bottom-color: #00d9ff;
        }
        
        .container { max-width: 1500px; margin: 0 auto; padding: 30px; }
        
        /* 统计卡片 */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.08);
            transition: all 0.3s;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            border-color: rgba(0,217,255,0.3);
        }
        .stat-card h3 { color: #666; font-size: 0.85em; margin-bottom: 12px; text-transform: uppercase; letter-spacing: 1px; }
        .stat-card .value { font-size: 2.2em; color: #00d9ff; font-weight: 700; }
        .stat-card .value.warning { color: #ffa502; }
        .stat-card .value.danger { color: #ff4757; }
        .stat-card .value.success { color: #2ed573; }
        
        /* 子标签页 */
        .sub-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }
        .sub-tab {
            padding: 10px 20px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 25px;
            cursor: pointer;
            color: #aaa;
            transition: all 0.3s;
            font-size: 0.9em;
        }
        .sub-tab:hover { background: rgba(255,255,255,0.1); color: #fff; }
        .sub-tab.active { background: #00d9ff; color: #0f0f1a; font-weight: 600; }
        
        .main-panel { display: none; }
        .main-panel.active { display: block; }
        .sub-panel { display: none; }
        .sub-panel.active { display: block; }
        
        /* 卡片 */
        .card {
            background: rgba(255,255,255,0.04);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.06);
        }
        .card h2 { 
            color: #00d9ff; 
            margin-bottom: 20px; 
            font-size: 1.1em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* 表格 */
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88em;
        }
        th, td {
            padding: 14px 10px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }
        th { 
            color: #00d9ff; 
            font-weight: 600; 
            text-transform: uppercase;
            font-size: 0.8em;
            letter-spacing: 0.5px;
        }
        tr:hover { background: rgba(255,255,255,0.02); }
        
        /* 按钮 */
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.3s;
            font-weight: 500;
        }
        .btn-primary { background: linear-gradient(135deg, #00d9ff, #0099cc); color: #0f0f1a; }
        .btn-danger { background: linear-gradient(135deg, #ff4757, #cc3344); color: white; }
        .btn-success { background: linear-gradient(135deg, #2ed573, #22aa55); color: #0f0f1a; }
        .btn-secondary { background: rgba(255,255,255,0.1); color: #aaa; }
        .btn:hover { transform: translateY(-2px); box-shadow: 0 5px 20px rgba(0,0,0,0.3); }
        
        input, select {
            padding: 12px 16px;
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 10px;
            background: rgba(255,255,255,0.05);
            color: #e4e4e4;
            margin-right: 10px;
            transition: all 0.3s;
        }
        input:focus { outline: none; border-color: #00d9ff; background: rgba(0,217,255,0.05); }
        
        .form-row { display: flex; gap: 12px; margin-bottom: 15px; flex-wrap: wrap; align-items: center; }
        
        /* 状态标签 */
        .status { padding: 4px 10px; border-radius: 12px; font-size: 0.8em; font-weight: 500; }
        .status-running { background: rgba(255,165,2,0.2); color: #ffa502; }
        .status-succeeded { background: rgba(46,213,115,0.2); color: #2ed573; }
        .status-failed { background: rgba(255,71,87,0.2); color: #ff4757; }
        
        .url-cell { max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        .mono { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 0.85em; }
        
        .refresh-btn { float: right; }
        
        /* 弹窗 */
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.85);
            z-index: 1000;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(5px);
        }
        .modal.show { display: flex; }
        .modal-content {
            background: linear-gradient(145deg, #1a1a2e, #0f0f1a);
            border-radius: 20px;
            padding: 35px;
            max-width: 450px;
            width: 90%;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .modal-content h3 { margin-bottom: 25px; color: #00d9ff; font-size: 1.3em; }
        
        /* 图表区域 */
        .chart-container {
            background: rgba(0,0,0,0.2);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            min-height: 200px;
        }
        .chart-bar {
            display: flex;
            align-items: flex-end;
            gap: 4px;
            height: 150px;
            padding: 10px 0;
        }
        .bar {
            flex: 1;
            background: linear-gradient(to top, #00d9ff, #0066cc);
            border-radius: 4px 4px 0 0;
            min-width: 8px;
            transition: all 0.3s;
            position: relative;
        }
        .bar:hover {
            background: linear-gradient(to top, #00ffff, #0099ff);
        }
        .bar .tooltip {
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.9);
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.75em;
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .bar:hover .tooltip { opacity: 1; }
        
        .legend {
            display: flex;
            gap: 20px;
            margin-top: 15px;
            justify-content: center;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 0.85em;
            color: #888;
        }
        .legend-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        
        /* 空状态 */
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        .empty-state .icon { font-size: 3em; margin-bottom: 15px; }
    </style>
</head>
<body>
    <!-- 顶部导航 -->
    <nav class="top-nav">
        <div class="logo">📊 MyVideo Admin</div>
        <div class="main-tabs">
            <div class="main-tab active" data-panel="database">🗃️ 数据库</div>
            <div class="main-tab" data-panel="monitor">📈 API监控</div>
        </div>
    </nav>
    
    <div class="container">
        <!-- ==================== 数据库面板 ==================== -->
        <div class="main-panel active" id="panel-database">
            <!-- 统计卡片 -->
            <div class="stats-grid" id="dbStatsGrid">
                <div class="stat-card">
                    <h3>用户总数</h3>
                    <div class="value" id="statUsers">-</div>
                </div>
                <div class="stat-card">
                    <h3>总积分</h3>
                    <div class="value" id="statCredits">-</div>
                </div>
                <div class="stat-card">
                    <h3>成功下载</h3>
                    <div class="value success" id="statSucceeded">-</div>
                </div>
                <div class="stat-card">
                    <h3>失败下载</h3>
                    <div class="value danger" id="statFailed">-</div>
                </div>
            </div>
            
            <!-- 子标签页 -->
            <div class="sub-tabs">
                <div class="sub-tab active" data-subtab="users">👤 用户</div>
                <div class="sub-tab" data-subtab="downloads">📥 下载任务</div>
                <div class="sub-tab" data-subtab="ledger">📝 积分流水</div>
                <div class="sub-tab" data-subtab="feedbacks">💬 用户反馈</div>
            </div>
            
            <!-- 用户面板 -->
            <div class="sub-panel active" id="subtab-users">
                <div class="card">
                    <button class="btn btn-primary refresh-btn" onclick="loadUsers()">🔄 刷新</button>
                    <h2>👤 用户列表</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>用户ID (lc_uid)</th>
                                <th>积分余额</th>
                                <th>创建时间</th>
                                <th>更新时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="usersTable"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 下载任务面板 -->
            <div class="sub-panel" id="subtab-downloads">
                <div class="card">
                    <button class="btn btn-primary refresh-btn" onclick="loadDownloads()">🔄 刷新</button>
                    <h2>📥 下载任务</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>任务ID</th>
                                <th>用户ID</th>
                                <th>URL</th>
                                <th>平台</th>
                                <th>积分</th>
                                <th>状态</th>
                                <th>时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="downloadsTable"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 积分流水面板 -->
            <div class="sub-panel" id="subtab-ledger">
                <div class="card">
                    <button class="btn btn-primary refresh-btn" onclick="loadLedger()">🔄 刷新</button>
                    <h2>📝 积分流水</h2>
                    <div class="form-row">
                        <input type="text" id="ledgerFilter" placeholder="按用户ID筛选...">
                        <button class="btn btn-primary" onclick="loadLedger()">筛选</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>用户ID</th>
                                <th>变动</th>
                                <th>原因</th>
                                <th>关联ID</th>
                                <th>时间</th>
                            </tr>
                        </thead>
                        <tbody id="ledgerTable"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 用户反馈面板 -->
            <div class="sub-panel" id="subtab-feedbacks">
                <div class="card">
                    <button class="btn btn-primary refresh-btn" onclick="loadFeedbacks()">🔄 刷新</button>
                    <h2>💬 用户反馈</h2>
                    <div class="form-row">
                        <select id="feedbackTypeFilter" onchange="loadFeedbacks()">
                            <option value="">全部类型</option>
                            <option value="功能建议">功能建议</option>
                            <option value="问题反馈">问题反馈</option>
                            <option value="其他">其他</option>
                        </select>
                        <select id="feedbackStatusFilter" onchange="loadFeedbacks()">
                            <option value="">全部状态</option>
                            <option value="pending">待处理</option>
                            <option value="processed">已处理</option>
                            <option value="archived">已归档</option>
                        </select>
                        <input type="text" id="feedbackFilter" placeholder="搜索反馈内容...">
                        <button class="btn btn-primary" onclick="loadFeedbacks()">筛选</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>反馈ID</th>
                                <th>类型</th>
                                <th>内容</th>
                                <th>联系方式</th>
                                <th>用户ID</th>
                                <th>设备信息</th>
                                <th>状态</th>
                                <th>提交时间</th>
                                <th>操作</th>
                            </tr>
                        </thead>
                        <tbody id="feedbacksTable"></tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- ==================== 监控面板 ==================== -->
        <div class="main-panel" id="panel-monitor">
            <!-- 监控统计卡片 -->
            <div class="stats-grid" id="monitorStatsGrid">
                <div class="stat-card">
                    <h3>总调用(24h)</h3>
                    <div class="value" id="mStatTotal">-</div>
                </div>
                <div class="stat-card">
                    <h3>成功率</h3>
                    <div class="value success" id="mStatSuccess">-</div>
                </div>
                <div class="stat-card">
                    <h3>外部API调用</h3>
                    <div class="value warning" id="mStatExternal">-</div>
                </div>
                <div class="stat-card">
                    <h3>平均延迟</h3>
                    <div class="value" id="mStatLatency">-</div>
                </div>
                <div class="stat-card">
                    <h3>错误数</h3>
                    <div class="value danger" id="mStatErrors">-</div>
                </div>
            </div>
            
            <!-- 子标签页 -->
            <div class="sub-tabs">
                <div class="sub-tab active" data-subtab="m-overview">📊 概览</div>
                <div class="sub-tab" data-subtab="m-external">🌐 外部API</div>
                <div class="sub-tab" data-subtab="m-logs">📋 调用日志</div>
            </div>
            
            <!-- 概览面板 -->
            <div class="sub-panel active" id="subtab-m-overview">
                <!-- 核心端点列表 -->
                <div class="card">
                    <button class="btn btn-primary refresh-btn" onclick="loadMetrics()">🔄 刷新数据</button>
                    <h2>🎯 核心API端点</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>端点</th>
                                <th>方法</th>
                                <th>描述</th>
                                <th>24h调用</th>
                                <th>错误</th>
                                <th>平均延迟</th>
                            </tr>
                        </thead>
                        <tbody id="coreEndpointTable"></tbody>
                    </table>
                </div>
                
                <!-- 外部API列表 -->
                <div class="card">
                    <h2>🌐 外部第三方API（付费）</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>API名称</th>
                                <th>端点</th>
                                <th>描述</th>
                                <th>24h调用</th>
                                <th>错误</th>
                                <th>成功率</th>
                                <th>平均延迟</th>
                            </tr>
                        </thead>
                        <tbody id="externalApiTable"></tbody>
                    </table>
                </div>
                
                <div class="card">
                    <h2>📈 24小时调用趋势</h2>
                    <div class="chart-container">
                        <div class="chart-bar" id="hourlyChart"></div>
                    </div>
                    <div class="legend">
                        <div class="legend-item"><div class="legend-dot" style="background:#00d9ff"></div> 总调用</div>
                        <div class="legend-item"><div class="legend-dot" style="background:#ffa502"></div> 外部API</div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>🔥 热门端点统计</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>端点</th>
                                <th>方法</th>
                                <th>调用次数</th>
                                <th>错误数</th>
                                <th>平均延迟</th>
                            </tr>
                        </thead>
                        <tbody id="endpointTable"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 外部API面板 -->
            <div class="sub-panel" id="subtab-m-external">
                <div class="card">
                    <button class="btn btn-primary refresh-btn" onclick="loadMetrics()">🔄 刷新</button>
                    <h2>🌐 外部第三方API调用统计</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>API名称</th>
                                <th>调用次数</th>
                                <th>错误数</th>
                                <th>成功率</th>
                                <th>平均延迟</th>
                            </tr>
                        </thead>
                        <tbody id="externalTable"></tbody>
                    </table>
                </div>
                
                <div class="card">
                    <h2>📋 最近外部API调用</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>时间</th>
                                <th>API</th>
                                <th>端点</th>
                                <th>状态码</th>
                                <th>延迟</th>
                                <th>错误</th>
                            </tr>
                        </thead>
                        <tbody id="externalLogsTable"></tbody>
                    </table>
                </div>
            </div>
            
            <!-- 调用日志面板 -->
            <div class="sub-panel" id="subtab-m-logs">
                <div class="card">
                    <button class="btn btn-primary refresh-btn" onclick="loadApiLogs()">🔄 刷新</button>
                    <button class="btn btn-danger refresh-btn" style="margin-right:10px" onclick="cleanupOldData()">🧹 清理7天前数据</button>
                    <h2>📋 API调用日志</h2>
                    <div class="form-row">
                        <input type="text" id="logFilter" placeholder="按端点筛选...">
                        <label><input type="checkbox" id="errorsOnly"> 仅错误</label>
                        <button class="btn btn-primary" onclick="loadApiLogs()">筛选</button>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>时间</th>
                                <th>方法</th>
                                <th>端点</th>
                                <th>状态码</th>
                                <th>延迟</th>
                                <th>外部</th>
                                <th>用户</th>
                                <th>错误</th>
                            </tr>
                        </thead>
                        <tbody id="logsTable"></tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
    
    <!-- 修改积分弹窗 -->
    <div class="modal" id="editModal">
        <div class="modal-content">
            <h3>✏️ 修改用户积分</h3>
            <input type="hidden" id="editUid">
            <div class="form-row">
                <label>当前余额: <span id="currentBalance" style="color:#00d9ff;font-weight:bold">-</span></label>
            </div>
            <div class="form-row">
                <input type="number" id="newBalance" placeholder="新积分值" style="width: 100%;">
            </div>
            <div class="form-row">
                <input type="text" id="editReason" placeholder="修改原因" value="admin_adjust" style="width: 100%;">
            </div>
            <div class="form-row" style="margin-top:20px">
                <button class="btn btn-success" onclick="saveCredits()">保存</button>
                <button class="btn btn-secondary" onclick="closeModal()">取消</button>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = '/api/admin';
        
        // ==================== 主标签页切换 ====================
        document.querySelectorAll('.main-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.main-tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.main-panel').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById('panel-' + tab.dataset.panel).classList.add('active');
                
                // 切换到监控时加载数据
                if (tab.dataset.panel === 'monitor') {
                    loadMetrics();
                }
            });
        });
        
        // 子标签页切换
        document.querySelectorAll('.sub-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                const parent = tab.closest('.main-panel');
                parent.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
                parent.querySelectorAll('.sub-panel').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById('subtab-' + tab.dataset.subtab).classList.add('active');
                
                // 切换到反馈标签页时加载数据
                if (tab.dataset.subtab === 'feedbacks') {
                    loadFeedbacks();
                }
            });
        });
        
        // ==================== 数据库功能 ====================
        async function loadStats() {
            try {
                const res = await fetch(API_BASE + '/stats');
                const data = await res.json();
                document.getElementById('statUsers').textContent = data.users.count;
                document.getElementById('statCredits').textContent = data.users.total_credits;
                document.getElementById('statSucceeded').textContent = data.downloads.succeeded || 0;
                document.getElementById('statFailed').textContent = data.downloads.failed || 0;
            } catch (e) { console.error(e); }
        }
        
        async function loadUsers() {
            try {
                const res = await fetch(API_BASE + '/users');
                const users = await res.json();
                const tbody = document.getElementById('usersTable');
                if (users.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="5" class="empty-state">暂无用户数据</td></tr>';
                    return;
                }
                tbody.innerHTML = users.map(u => `
                    <tr>
                        <td class="mono">${u.lc_uid}</td>
                        <td><strong style="color:#00d9ff">${u.credits_balance}</strong></td>
                        <td>${formatTime(u.created_at)}</td>
                        <td>${formatTime(u.updated_at)}</td>
                        <td>
                            <button class="btn btn-primary" onclick="editUser('${u.lc_uid}', ${u.credits_balance})">编辑</button>
                            <button class="btn btn-danger" onclick="deleteUser('${u.lc_uid}')">删除</button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) { console.error(e); }
        }
        
        async function loadDownloads() {
            try {
                const res = await fetch(API_BASE + '/downloads');
                const jobs = await res.json();
                const tbody = document.getElementById('downloadsTable');
                if (jobs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">暂无下载任务</td></tr>';
                    return;
                }
                tbody.innerHTML = jobs.map(j => `
                    <tr>
                        <td class="mono">${j.job_id.substring(0,8)}...</td>
                        <td class="mono">${j.lc_uid.substring(0,10)}...</td>
                        <td class="url-cell" title="${j.url}">${j.url}</td>
                        <td>${j.platform}</td>
                        <td>${j.cost_credits}</td>
                        <td><span class="status status-${j.status}">${j.status}</span></td>
                        <td>${formatTime(j.created_at)}</td>
                        <td>
                            <button class="btn btn-danger" onclick="deleteDownload('${j.job_id}')">删除</button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) { console.error(e); }
        }
        
        async function loadLedger() {
            try {
                const filter = document.getElementById('ledgerFilter').value;
                let url = API_BASE + '/ledger';
                if (filter) url += '?lc_uid=' + encodeURIComponent(filter);
                const res = await fetch(url);
                const items = await res.json();
                const tbody = document.getElementById('ledgerTable');
                if (items.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">暂无流水记录</td></tr>';
                    return;
                }
                tbody.innerHTML = items.map(l => `
                    <tr>
                        <td>${l.id}</td>
                        <td class="mono">${l.lc_uid.substring(0,10)}...</td>
                        <td style="color: ${l.delta >= 0 ? '#2ed573' : '#ff4757'}; font-weight: bold;">
                            ${l.delta >= 0 ? '+' : ''}${l.delta}
                        </td>
                        <td>${l.reason}</td>
                        <td class="mono">${l.ref_id ? l.ref_id.substring(0,8)+'...' : '-'}</td>
                        <td>${formatTime(l.created_at)}</td>
                    </tr>
                `).join('');
            } catch (e) { console.error(e); }
        }
        
        async function loadFeedbacks() {
            try {
                const typeFilter = document.getElementById('feedbackTypeFilter').value;
                const statusFilter = document.getElementById('feedbackStatusFilter').value;
                const searchFilter = document.getElementById('feedbackFilter').value;
                
                let url = API_BASE + '/feedbacks?limit=200';
                if (typeFilter) url += '&type_filter=' + encodeURIComponent(typeFilter);
                if (statusFilter) url += '&status_filter=' + encodeURIComponent(statusFilter);
                if (searchFilter) url += '&search=' + encodeURIComponent(searchFilter);
                
                const res = await fetch(url);
                const items = await res.json();
                const tbody = document.getElementById('feedbacksTable');
                
                if (items.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" class="empty-state">暂无反馈记录</td></tr>';
                    return;
                }
                
                tbody.innerHTML = items.map(fb => {
                    const deviceInfo = fb.device_info ? (typeof fb.device_info === 'string' ? JSON.parse(fb.device_info) : fb.device_info) : {};
                    const deviceStr = deviceInfo.app_version || deviceInfo.device_model ? 
                        `${deviceInfo.app_version || '-'} / ${deviceInfo.ios_version || '-'} / ${deviceInfo.device_model || '-'}` : '-';
                    const statusClass = fb.status === 'pending' ? 'status-warning' : fb.status === 'processed' ? 'status-success' : 'status-dim';
                    const statusText = fb.status === 'pending' ? '待处理' : fb.status === 'processed' ? '已处理' : '已归档';
                    
                    return `
                        <tr>
                            <td class="mono" title="${fb.id}">${fb.id}</td>
                            <td>${fb.type}</td>
                            <td class="content-cell" title="${fb.content}">${fb.content.length > 50 ? fb.content.substring(0, 50) + '...' : fb.content}</td>
                            <td>${fb.contact || '-'}</td>
                            <td class="mono" title="${fb.lc_uid || '未登录'}">${fb.lc_uid || '<span style="color:#888;">未登录</span>'}</td>
                            <td class="mono" style="font-size: 0.85em;">${deviceStr}</td>
                            <td><span class="status ${statusClass}">${statusText}</span></td>
                            <td>${formatTime(fb.received_at)}</td>
                            <td>
                                <button class="btn btn-sm" onclick="viewFeedback('${fb.id}')">查看</button>
                                ${fb.status === 'pending' ? `<button class="btn btn-sm btn-success" onclick="updateFeedbackStatus('${fb.id}', 'processed')">标记已处理</button>` : ''}
                                <button class="btn btn-sm btn-danger" onclick="deleteFeedback('${fb.id}')">删除</button>
                            </td>
                        </tr>
                    `;
                }).join('');
            } catch (e) { 
                console.error('加载反馈失败:', e);
                document.getElementById('feedbacksTable').innerHTML = '<tr><td colspan="9" class="empty-state">加载失败: ' + e.message + '</td></tr>';
            }
        }
        
        async function viewFeedback(feedbackId) {
            try {
                const res = await fetch(API_BASE + '/feedbacks/' + feedbackId);
                const fb = await res.json();
                const deviceInfo = fb.device_info ? (typeof fb.device_info === 'string' ? JSON.parse(fb.device_info) : fb.device_info) : {};
                
                const deviceInfoStr = Object.keys(deviceInfo).length > 0 ? 
                    `应用版本: ${deviceInfo.app_version || '未知'}\niOS版本: ${deviceInfo.ios_version || '未知'}\n设备型号: ${deviceInfo.device_model || '未知'}` : '无';
                
                alert(`反馈详情\n\n反馈ID: ${fb.id}\n类型: ${fb.type}\n状态: ${fb.status === 'pending' ? '待处理' : fb.status === 'processed' ? '已处理' : '已归档'}\n\n反馈内容:\n${fb.content}\n\n联系方式: ${fb.contact || '无'}\n用户ID: ${fb.lc_uid || '未登录（游客）'}\n\n设备信息:\n${deviceInfoStr}\n\n提交时间: ${fb.timestamp || '未知'}\n接收时间: ${fb.received_at || '未知'}`);
            } catch (e) {
                alert('查看反馈失败: ' + e.message);
            }
        }
        
        async function updateFeedbackStatus(feedbackId, status) {
            if (!confirm('确定要更新反馈状态吗？')) return;
            try {
                const res = await fetch(API_BASE + '/feedbacks/' + feedbackId + '/status?status=' + status, {
                    method: 'POST'
                });
                const result = await res.json();
                if (result.success) {
                    alert('状态更新成功');
                    loadFeedbacks();
                } else {
                    alert('状态更新失败: ' + result.message);
                }
            } catch (e) {
                alert('更新状态失败: ' + e.message);
            }
        }
        
        async function deleteFeedback(feedbackId) {
            if (!confirm('确定要删除这条反馈吗？此操作不可恢复！')) return;
            try {
                const res = await fetch(API_BASE + '/feedbacks/' + feedbackId, {
                    method: 'DELETE'
                });
                const result = await res.json();
                if (result.success) {
                    alert('删除成功');
                    loadFeedbacks();
                } else {
                    alert('删除失败: ' + result.message);
                }
            } catch (e) {
                alert('删除失败: ' + e.message);
            }
        }
        
        function editUser(uid, balance) {
            document.getElementById('editUid').value = uid;
            document.getElementById('currentBalance').textContent = balance;
            document.getElementById('newBalance').value = balance;
            document.getElementById('editModal').classList.add('show');
        }
        
        function closeModal() {
            document.getElementById('editModal').classList.remove('show');
        }
        
        async function saveCredits() {
            const uid = document.getElementById('editUid').value;
            const newBalance = parseInt(document.getElementById('newBalance').value);
            const reason = document.getElementById('editReason').value;
            
            try {
                const res = await fetch(API_BASE + '/users/update-credits', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ lc_uid: uid, new_balance: newBalance, reason: reason })
                });
                const data = await res.json();
                if (data.success) {
                    alert(`积分已修改: ${data.old_balance} → ${data.new_balance}`);
                    closeModal();
                    loadUsers();
                    loadStats();
                }
            } catch (e) { alert('操作失败: ' + e); }
        }
        
        async function deleteUser(uid) {
            if (!confirm('确定要删除用户 ' + uid + ' 及其所有数据吗？')) return;
            try {
                const res = await fetch(API_BASE + '/users/' + uid, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) {
                    loadUsers();
                    loadStats();
                }
            } catch (e) { alert('删除失败: ' + e); }
        }
        
        async function deleteDownload(jobId) {
            if (!confirm('确定要删除此下载任务吗？')) return;
            try {
                const res = await fetch(API_BASE + '/downloads/' + jobId, { method: 'DELETE' });
                const data = await res.json();
                if (data.success) loadDownloads();
            } catch (e) { alert('删除失败: ' + e); }
        }
        
        // ==================== 监控功能 ====================
        async function loadMetrics() {
            try {
                // 加载统计
                const statsRes = await fetch(API_BASE + '/metrics/stats?hours=24');
                const stats = await statsRes.json();
                
                // 加载端点配置
                const endpointsRes = await fetch(API_BASE + '/metrics/endpoints');
                const endpoints = await endpointsRes.json();
                
                document.getElementById('mStatTotal').textContent = stats.overall.total;
                const successRate = stats.overall.total > 0 
                    ? Math.round((stats.overall.success / stats.overall.total) * 100) + '%'
                    : '-';
                document.getElementById('mStatSuccess').textContent = successRate;
                document.getElementById('mStatExternal').textContent = stats.external.total;
                document.getElementById('mStatLatency').textContent = stats.overall.avg_latency_ms + 'ms';
                document.getElementById('mStatErrors').textContent = stats.overall.errors;
                
                // 核心端点表格（将配置与统计数据合并）
                const coreEndpointTbody = document.getElementById('coreEndpointTable');
                const endpointStatsMap = {};
                stats.by_endpoint.forEach(e => {
                    endpointStatsMap[e.endpoint] = e;
                });
                
                coreEndpointTbody.innerHTML = endpoints.core_endpoints.map(ep => {
                    const stat = endpointStatsMap[ep.endpoint] || { count: 0, errors: 0, avg_latency: 0 };
                    return `
                        <tr>
                            <td class="mono" style="font-size:0.8em">${ep.endpoint}</td>
                            <td>${ep.method}</td>
                            <td>${ep.description}</td>
                            <td>${stat.count || 0}</td>
                            <td style="color:${stat.errors > 0 ? '#ff4757' : '#2ed573'}">${stat.errors || 0}</td>
                            <td>${stat.count > 0 ? Math.round(stat.avg_latency) + 'ms' : '-'}</td>
                        </tr>
                    `;
                }).join('');
                
                // 外部API端点表格（合并配置与统计）
                const externalApiTbody = document.getElementById('externalApiTable');
                const externalStatsMap = {};
                stats.by_external_api.forEach(e => {
                    externalStatsMap[e.external_api] = e;
                });
                
                externalApiTbody.innerHTML = endpoints.external_apis.map(api => {
                    const stat = externalStatsMap[api.name] || { count: 0, errors: 0, avg_latency: 0 };
                    const rate = stat.count > 0 ? Math.round(((stat.count - stat.errors) / stat.count) * 100) : 0;
                    return `
                        <tr>
                            <td><strong style="color:#ffa502">${api.name}</strong></td>
                            <td class="mono" style="font-size:0.75em">${api.endpoint}</td>
                            <td>${api.description}</td>
                            <td>${stat.count || 0}</td>
                            <td style="color:${stat.errors > 0 ? '#ff4757' : '#2ed573'}">${stat.errors || 0}</td>
                            <td style="color:${stat.count === 0 ? '#888' : (rate < 90 ? '#ff4757' : '#2ed573')}">${stat.count > 0 ? rate + '%' : '-'}</td>
                            <td>${stat.count > 0 ? Math.round(stat.avg_latency) + 'ms' : '-'}</td>
                        </tr>
                    `;
                }).join('');
                
                // 热门端点统计表格
                const epTbody = document.getElementById('endpointTable');
                if (stats.by_endpoint.length === 0) {
                    epTbody.innerHTML = '<tr><td colspan="5" class="empty-state">暂无数据</td></tr>';
                } else {
                    epTbody.innerHTML = stats.by_endpoint.map(e => `
                        <tr>
                            <td class="mono" style="font-size:0.8em">${e.endpoint}</td>
                            <td>${e.method}</td>
                            <td>${e.count}</td>
                            <td style="color:${e.errors > 0 ? '#ff4757' : '#2ed573'}">${e.errors}</td>
                            <td>${Math.round(e.avg_latency)}ms</td>
                        </tr>
                    `).join('');
                }
                
                // 外部API表格（在外部API面板）
                const extTbody = document.getElementById('externalTable');
                if (stats.by_external_api.length === 0) {
                    extTbody.innerHTML = '<tr><td colspan="5" class="empty-state">暂无外部API调用</td></tr>';
                } else {
                    extTbody.innerHTML = stats.by_external_api.map(e => {
                        const rate = e.count > 0 ? Math.round(((e.count - e.errors) / e.count) * 100) : 0;
                        return `
                        <tr>
                            <td><strong>${e.external_api}</strong></td>
                            <td>${e.count}</td>
                            <td style="color:${e.errors > 0 ? '#ff4757' : '#2ed573'}">${e.errors}</td>
                            <td style="color:${rate < 90 ? '#ff4757' : '#2ed573'}">${rate}%</td>
                            <td>${Math.round(e.avg_latency)}ms</td>
                        </tr>
                    `}).join('');
                }
                
                // 加载小时趋势
                loadHourlyChart();
                
                // 加载外部日志
                loadExternalLogs();
                
            } catch (e) { console.error(e); }
        }
        
        async function loadHourlyChart() {
            try {
                const res = await fetch(API_BASE + '/metrics/hourly?hours=24');
                const data = await res.json();
                
                const chartDiv = document.getElementById('hourlyChart');
                if (data.length === 0) {
                    chartDiv.innerHTML = '<div class="empty-state">暂无数据</div>';
                    return;
                }
                
                const maxVal = Math.max(...data.map(d => d.total), 1);
                
                chartDiv.innerHTML = data.map(d => {
                    const height = Math.max((d.total / maxVal) * 100, 5);
                    const hour = d.hour.split(' ')[1] || d.hour;
                    return `
                        <div class="bar" style="height:${height}%">
                            <div class="tooltip">${hour}<br>总:${d.total} 外部:${d.external} 错误:${d.errors}</div>
                        </div>
                    `;
                }).join('');
            } catch (e) { console.error(e); }
        }
        
        async function loadExternalLogs() {
            try {
                const res = await fetch(API_BASE + '/metrics/calls?limit=50&external_only=true');
                const logs = await res.json();
                const tbody = document.getElementById('externalLogsTable');
                
                if (logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="empty-state">暂无外部API调用记录</td></tr>';
                    return;
                }
                
                tbody.innerHTML = logs.map(l => `
                    <tr>
                        <td>${formatTime(l.created_at)}</td>
                        <td><strong>${l.external_api || '-'}</strong></td>
                        <td class="mono" style="max-width:200px;overflow:hidden;text-overflow:ellipsis">${l.endpoint}</td>
                        <td style="color:${l.status_code >= 400 ? '#ff4757' : '#2ed573'}">${l.status_code}</td>
                        <td>${l.latency_ms}ms</td>
                        <td style="color:#ff4757;max-width:150px;overflow:hidden;text-overflow:ellipsis" title="${l.error_message||''}">${l.error_message ? l.error_message.substring(0,30)+'...' : '-'}</td>
                    </tr>
                `).join('');
            } catch (e) { console.error(e); }
        }
        
        async function loadApiLogs() {
            try {
                const filter = document.getElementById('logFilter').value;
                const errorsOnly = document.getElementById('errorsOnly').checked;
                let url = API_BASE + '/metrics/calls?limit=100';
                if (filter) url += '&endpoint=' + encodeURIComponent(filter);
                if (errorsOnly) url += '&errors_only=true';
                
                const res = await fetch(url);
                const logs = await res.json();
                const tbody = document.getElementById('logsTable');
                
                if (logs.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="8" class="empty-state">暂无调用记录</td></tr>';
                    return;
                }
                
                tbody.innerHTML = logs.map(l => `
                    <tr>
                        <td>${formatTime(l.created_at)}</td>
                        <td>${l.method}</td>
                        <td class="mono" style="max-width:200px;overflow:hidden;text-overflow:ellipsis" title="${l.endpoint}">${l.endpoint}</td>
                        <td style="color:${l.status_code >= 400 ? '#ff4757' : '#2ed573'}">${l.status_code}</td>
                        <td>${l.latency_ms}ms</td>
                        <td>${l.is_external ? '✅' : '-'}</td>
                        <td class="mono">${l.lc_uid ? l.lc_uid.substring(0,8)+'...' : '-'}</td>
                        <td style="color:#ff4757;max-width:100px;overflow:hidden;text-overflow:ellipsis" title="${l.error_message||''}">${l.error_message ? '⚠️' : '-'}</td>
                    </tr>
                `).join('');
            } catch (e) { console.error(e); }
        }
        
        async function cleanupOldData() {
            if (!confirm('确定要清理7天前的监控数据吗？')) return;
            try {
                const res = await fetch(API_BASE + '/metrics/cleanup', { method: 'POST' });
                const data = await res.json();
                alert(`已清理 ${data.deleted_count} 条记录`);
                loadMetrics();
            } catch (e) { alert('清理失败: ' + e); }
        }
        
        // ==================== 工具函数 ====================
        function formatTime(isoStr) {
            if (!isoStr) return '-';
            const d = new Date(isoStr);
            return d.toLocaleString('zh-CN', { 
                month: '2-digit', day: '2-digit', 
                hour: '2-digit', minute: '2-digit',
                second: '2-digit'
            });
        }
        
        // ==================== 初始化 ====================
        loadStats();
        loadUsers();
        loadDownloads();
        loadLedger();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)
