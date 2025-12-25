# -*- coding: utf-8 -*-
"""
数据库管理API端点 - 用于测试和调试
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.db.database import get_db_connection, DB_PATH
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


# ==================== 管理页面 ====================

@router.get("/", response_class=HTMLResponse, summary="管理页面")
async def admin_page():
    """数据库管理页面"""
    html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>数据库管理 - MyVideoDownloader</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e4e4e4;
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { 
            text-align: center; 
            margin-bottom: 30px; 
            color: #00d9ff;
            font-size: 2em;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .stat-card h3 { color: #888; font-size: 0.9em; margin-bottom: 10px; }
        .stat-card .value { font-size: 2em; color: #00d9ff; font-weight: bold; }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .tab {
            padding: 12px 24px;
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            cursor: pointer;
            color: #aaa;
            transition: all 0.3s;
        }
        .tab:hover { background: rgba(255,255,255,0.1); }
        .tab.active { background: #00d9ff; color: #1a1a2e; font-weight: bold; }
        
        .panel { display: none; }
        .panel.active { display: block; }
        
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 { color: #00d9ff; margin-bottom: 15px; font-size: 1.2em; }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.9em;
        }
        th, td {
            padding: 12px 8px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        th { color: #00d9ff; font-weight: 600; }
        tr:hover { background: rgba(255,255,255,0.03); }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85em;
            transition: all 0.3s;
        }
        .btn-primary { background: #00d9ff; color: #1a1a2e; }
        .btn-danger { background: #ff4757; color: white; }
        .btn-success { background: #2ed573; color: #1a1a2e; }
        .btn:hover { opacity: 0.8; transform: translateY(-1px); }
        
        input, select {
            padding: 10px;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 6px;
            background: rgba(255,255,255,0.05);
            color: #e4e4e4;
            margin-right: 10px;
        }
        input:focus { outline: none; border-color: #00d9ff; }
        
        .form-row { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; align-items: center; }
        
        .status-running { color: #ffa502; }
        .status-succeeded { color: #2ed573; }
        .status-failed { color: #ff4757; }
        
        .url-cell { max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
        
        .refresh-btn { float: right; margin-bottom: 10px; }
        
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0; right: 0; bottom: 0;
            background: rgba(0,0,0,0.8);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }
        .modal.show { display: flex; }
        .modal-content {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .modal-content h3 { margin-bottom: 20px; color: #00d9ff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 数据库管理面板</h1>
        
        <!-- 统计卡片 -->
        <div class="stats-grid" id="statsGrid">
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
                <div class="value" id="statSucceeded">-</div>
            </div>
            <div class="stat-card">
                <h3>失败下载</h3>
                <div class="value" id="statFailed">-</div>
            </div>
        </div>
        
        <!-- 标签页 -->
        <div class="tabs">
            <div class="tab active" data-tab="users">👤 用户管理</div>
            <div class="tab" data-tab="downloads">📥 下载任务</div>
            <div class="tab" data-tab="ledger">📝 积分流水</div>
        </div>
        
        <!-- 用户管理面板 -->
        <div class="panel active" id="panel-users">
            <div class="card">
                <button class="btn btn-primary refresh-btn" onclick="loadUsers()">🔄 刷新</button>
                <h2>用户列表</h2>
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
        <div class="panel" id="panel-downloads">
            <div class="card">
                <button class="btn btn-primary refresh-btn" onclick="loadDownloads()">🔄 刷新</button>
                <h2>下载任务列表</h2>
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
        <div class="panel" id="panel-ledger">
            <div class="card">
                <button class="btn btn-primary refresh-btn" onclick="loadLedger()">🔄 刷新</button>
                <h2>积分流水记录</h2>
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
    </div>
    
    <!-- 修改积分弹窗 -->
    <div class="modal" id="editModal">
        <div class="modal-content">
            <h3>✏️ 修改用户积分</h3>
            <input type="hidden" id="editUid">
            <div class="form-row">
                <label>当前余额: <span id="currentBalance">-</span></label>
            </div>
            <div class="form-row">
                <input type="number" id="newBalance" placeholder="新积分值" style="width: 200px;">
            </div>
            <div class="form-row">
                <input type="text" id="editReason" placeholder="修改原因" value="admin_adjust" style="width: 200px;">
            </div>
            <div class="form-row">
                <button class="btn btn-success" onclick="saveCredits()">保存</button>
                <button class="btn" onclick="closeModal()">取消</button>
            </div>
        </div>
    </div>
    
    <script>
        const API_BASE = '/api/admin';
        
        // 标签页切换
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
            });
        });
        
        // 加载统计
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
        
        // 加载用户
        async function loadUsers() {
            try {
                const res = await fetch(API_BASE + '/users');
                const users = await res.json();
                const tbody = document.getElementById('usersTable');
                tbody.innerHTML = users.map(u => `
                    <tr>
                        <td style="font-family: monospace; font-size: 0.8em;">${u.lc_uid}</td>
                        <td><strong>${u.credits_balance}</strong></td>
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
        
        // 加载下载任务
        async function loadDownloads() {
            try {
                const res = await fetch(API_BASE + '/downloads');
                const jobs = await res.json();
                const tbody = document.getElementById('downloadsTable');
                tbody.innerHTML = jobs.map(j => `
                    <tr>
                        <td style="font-family: monospace; font-size: 0.75em;">${j.job_id.substring(0,8)}...</td>
                        <td style="font-family: monospace; font-size: 0.75em;">${j.lc_uid.substring(0,10)}...</td>
                        <td class="url-cell" title="${j.url}">${j.url}</td>
                        <td>${j.platform}</td>
                        <td>${j.cost_credits}</td>
                        <td class="status-${j.status}">${j.status}</td>
                        <td>${formatTime(j.created_at)}</td>
                        <td>
                            <button class="btn btn-danger" onclick="deleteDownload('${j.job_id}')">删除</button>
                        </td>
                    </tr>
                `).join('');
            } catch (e) { console.error(e); }
        }
        
        // 加载流水
        async function loadLedger() {
            try {
                const filter = document.getElementById('ledgerFilter').value;
                let url = API_BASE + '/ledger';
                if (filter) url += '?lc_uid=' + encodeURIComponent(filter);
                const res = await fetch(url);
                const items = await res.json();
                const tbody = document.getElementById('ledgerTable');
                tbody.innerHTML = items.map(l => `
                    <tr>
                        <td>${l.id}</td>
                        <td style="font-family: monospace; font-size: 0.75em;">${l.lc_uid.substring(0,10)}...</td>
                        <td style="color: ${l.delta >= 0 ? '#2ed573' : '#ff4757'}; font-weight: bold;">
                            ${l.delta >= 0 ? '+' : ''}${l.delta}
                        </td>
                        <td>${l.reason}</td>
                        <td style="font-family: monospace; font-size: 0.75em;">${l.ref_id || '-'}</td>
                        <td>${formatTime(l.created_at)}</td>
                    </tr>
                `).join('');
            } catch (e) { console.error(e); }
        }
        
        // 编辑用户
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
        
        function formatTime(isoStr) {
            if (!isoStr) return '-';
            const d = new Date(isoStr);
            return d.toLocaleString('zh-CN', { 
                month: '2-digit', day: '2-digit', 
                hour: '2-digit', minute: '2-digit' 
            });
        }
        
        // 初始化
        loadStats();
        loadUsers();
        loadDownloads();
        loadLedger();
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

