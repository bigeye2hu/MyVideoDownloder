# 积分系统API文档 - App端对接指南

## 概述

本文档说明App如何与Server端积分系统交互，完成视频下载的完整流程。

### 核心原则

1. **App只和Server通信** - 不直接调用第三方API（如TikHub）
2. **Server统一处理第三方调用** - 第三方API切换时App无感知
3. **延迟扣分机制** - 积分冻结 → 下载成功后真正扣除 → 失败则解冻返还

---

## 认证方式

所有API请求需要在Header中携带LeanCloud认证信息：

```
X-LC-UID: <用户的LeanCloud objectId>
X-LC-Session: <用户的LeanCloud sessionToken>
```

---

## 完整下载流程

```
┌──────────────────────────────────────────────────────────────────────┐
│                           下载视频完整流程                            │
└──────────────────────────────────────────────────────────────────────┘

     App                                Server                    TikHub
      │                                   │                          │
      │ 1. POST /api/downloads/start      │                          │
      │   { url }                         │                          │
      │ ─────────────────────────────────>│                          │
      │                                   │ 2. 冻结积分               │
      │                                   │ 3. 调用TikHub             │
      │                                   │ ─────────────────────────>│
      │                                   │<─────────────────────────│
      │                                   │                          │
      │ 4. 返回视频信息                    │                          │
      │   { job_id, video_info }          │                          │
      │<──────────────────────────────────│                          │
      │                                   │                          │
      │ 5. 展示确认弹窗                    │                          │
      │    (标题、封面、消耗积分)          │                          │
      │                                   │                          │
      │ ─────── 用户确认 ─────>           │                          │
      │                                   │                          │
      │ 6. POST /api/downloads/confirm    │                          │
      │   { job_id }                      │                          │
      │ ─────────────────────────────────>│                          │
      │                                   │ 7. 真正扣除积分           │
      │                                   │                          │
      │ 8. 返回下载链接                    │                          │
      │   { video_info.download_url }     │                          │
      │<──────────────────────────────────│                          │
      │                                   │                          │
      │ 9. 使用download_url下载视频        │                          │
      │                                   │                          │
      │ ─────── 下载成功 ─────>           │                          │
      │         流程结束                   │                          │
      │                                   │                          │
      │ ─────── 下载失败 ─────>           │                          │
      │                                   │                          │
      │ 10. POST /api/downloads/cancel    │                          │
      │    { job_id }                     │                          │
      │ ─────────────────────────────────>│                          │
      │                                   │ 11. 解冻积分返还          │
      │<──────────────────────────────────│                          │
      │         积分已返还                 │                          │
      └───────────────────────────────────┘                          │
```

---

## API接口详情

### 1. 查询积分余额

**请求**
```
GET /api/credits/balance
Headers:
  X-LC-UID: <用户objectId>
  X-LC-Session: <sessionToken>
```

**响应**
```json
{
  "lc_uid": "abc123",
  "credits_balance": 100,      // 总余额
  "credits_frozen": 10,        // 冻结中的积分
  "credits_available": 90      // 可用余额 = 总余额 - 冻结
}
```

**说明**
- 首次查询会自动创建账户并赠送100积分
- 发起下载后积分会被冻结，体现在 `credits_frozen`

---

### 2. 发起下载任务（核心接口）

**请求**
```
POST /api/downloads/start
Headers:
  X-LC-UID: <用户objectId>
  X-LC-Session: <sessionToken>
Content-Type: application/json

{
  "url": "https://www.douyin.com/video/xxx"
}
```

**成功响应** (HTTP 200)
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "platform": "douyin",
  "cost_credits": 10,
  "status": "pending_confirm",
  "message": "视频解析成功，积分已冻结。请展示视频信息供用户确认，确认后调用confirm接口",
  "video_info": { /* TikHub原始响应，见下方结构说明 */ }
}
```

**video_info 结构说明（TikHub原始响应）**

⚠️ 返回的是TikHub API原始数据，App端需自行解析

```json
{
  "data": {
    "aweme_detail": {
      "desc": "视频标题/描述",
      "author": {
        "nickname": "作者名",
        "avatar_thumb": { "url_list": ["头像链接"] }
      },
      "video": {
        "cover": { "url_list": ["封面链接1", "封面链接2"] },
        "play_addr": { "url_list": ["下载链接1", "下载链接2"] },
        "duration": 15000
      },
      "statistics": {
        "digg_count": 12345,
        "comment_count": 678,
        "share_count": 90
      }
    }
  }
}
```

**常用字段路径**
| 数据 | 路径 |
|------|------|
| 视频标题 | `video_info.data.aweme_detail.desc` |
| 作者名 | `video_info.data.aweme_detail.author.nickname` |
| 封面图 | `video_info.data.aweme_detail.video.cover.url_list[0]` |
| 下载链接 | `video_info.data.aweme_detail.video.play_addr.url_list[0]` |
| 时长(ms) | `video_info.data.aweme_detail.video.duration` |
```

**错误响应**

| HTTP状态码 | 说明 |
|-----------|------|
| 401 | 身份验证失败 |
| 402 | 积分不足 |
| 500 | 视频解析失败 |

```json
// 积分不足示例
{
  "detail": "积分不足。可用余额: 5, 需要: 10"
}
```

**App处理逻辑**
```swift
func startDownload(url: String) async throws -> DownloadStartResponse {
    let response = try await api.post("/api/downloads/start", body: ["url": url])
    
    if response.status == "pending_confirm" {
        // 解析视频信息
        let title = response.video_info.data.aweme_detail.desc
        let cover = response.video_info.data.aweme_detail.video.cover.url_list.first
        
        // 展示确认弹窗
        showConfirmDialog(
            title: title,
            cover: cover,
            cost: response.cost_credits,
            onConfirm: { await confirmDownload(response.job_id) },
            onCancel: { await cancelDownload(response.job_id) }
        )
    }
    return response
}
```

---

### 3. 确认下载（用户点击确认后调用）

**请求**
```
POST /api/downloads/confirm
Headers:
  X-LC-UID: <用户objectId>
  X-LC-Session: <sessionToken>
Content-Type: application/json

{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**成功响应**
```json
{
  "success": true,
  "message": "确认成功，积分已扣除",
  "credits_deducted": 10,
  "video_info": {
    "data": {
      "aweme_detail": {
        "video": {
          "play_addr": {
            "url_list": ["https://实际下载链接"]
          }
        }
      }
    }
  }
}
```

**App处理逻辑**
```swift
func confirmDownload(jobId: String) async throws {
    let result = try await api.post("/api/downloads/confirm", body: ["job_id": jobId])
    
    if result.success {
        // 获取下载链接
        let downloadUrl = result.video_info.data.aweme_detail.video.play_addr.url_list.first
        
        // 开始下载视频
        try await downloadVideo(from: downloadUrl)
    }
}
```

---

### 4. 取消下载（用户取消或下载失败时调用）

**请求**
```
POST /api/downloads/cancel
Headers:
  X-LC-UID: <用户objectId>
  X-LC-Session: <sessionToken>
Content-Type: application/json

{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**成功响应**
```json
{
  "success": true,
  "message": "取消成功，积分已返还",
  "credits_refunded": 10
}
```

**调用时机**
1. 用户在确认弹窗点击"取消"
2. 视频文件下载失败（网络错误等）
3. 视频保存到相册失败

---

### 5. 查询下载状态（可选）

**请求**
```
GET /api/downloads/status?job_id=xxx
Headers:
  X-LC-UID: <用户objectId>
  X-LC-Session: <sessionToken>
```

**响应**
```json
{
  "job_id": "xxx",
  "status": "pending_confirm",  // 或 "succeeded", "failed", "cancelled"
  "confirmed": 0,               // 0=未确认, 1=已确认, -1=已取消
  "cost_credits": 10,
  "result_data": { ... },       // 视频信息
  "error_message": null
}
```

---

## 积分扣费规则

| 平台 | 消耗积分 |
|------|---------|
| 抖音 (douyin) | 10 |
| 其他平台 | 20 |

---

## 状态流转

```
           ┌─────────────────┐
           │     start       │
           │   (创建任务)     │
           └────────┬────────┘
                    │
                    ▼
           ┌─────────────────┐
           │ pending_confirm │ ← 积分已冻结
           │   (等待确认)     │
           └────────┬────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌───────────────┐       ┌───────────────┐
│   succeeded   │       │   cancelled   │
│  (下载成功)    │       │   (已取消)    │
│  积分已扣除    │       │  积分已返还    │
└───────────────┘       └───────────────┘
```

---

## 错误处理最佳实践

```swift
func handleDownloadFlow(url: String) async {
    do {
        // 1. 发起下载
        let startResult = try await startDownload(url: url)
        
        // 2. 展示确认弹窗
        let confirmed = await showConfirmDialog(videoInfo: startResult.video_info)
        
        if confirmed {
            // 3. 用户确认
            let confirmResult = try await confirmDownload(jobId: startResult.job_id)
            
            // 4. 下载视频文件
            do {
                let downloadUrl = confirmResult.video_info.downloadUrl
                try await downloadAndSaveVideo(url: downloadUrl)
                showSuccess("下载成功！")
            } catch {
                // 5. 下载失败，取消任务返还积分
                try await cancelDownload(jobId: startResult.job_id)
                showError("下载失败，积分已返还")
            }
        } else {
            // 用户取消
            try await cancelDownload(jobId: startResult.job_id)
        }
        
    } catch APIError.insufficientCredits {
        showError("积分不足，请充值")
    } catch APIError.authFailed {
        showError("请重新登录")
    } catch {
        showError("操作失败：\(error)")
    }
}
```

---

## 重要提醒

1. **下载完成后才算成功** - 不是调用confirm就结束，要等视频真正保存到相册
2. **失败必须调用cancel** - 否则积分会一直处于冻结状态
3. **confirm失败也要调用cancel** - Server不会自动返还积分
4. **不要直接调用第三方API** - 所有视频信息通过 `/api/downloads/start` 获取
5. **job_id要保存** - 用于后续的confirm/cancel操作
6. **video_info是TikHub原始结构** - App端需自行解析所需字段

---

## 接口地址

**生产环境**: `https://download.mygolfai.com.cn`

**完整URL示例**:
- `POST https://download.mygolfai.com.cn/api/downloads/start`
- `POST https://download.mygolfai.com.cn/api/downloads/confirm`
- `POST https://download.mygolfai.com.cn/api/downloads/cancel`
- `GET https://download.mygolfai.com.cn/api/credits/balance`

---

## 版本历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2024-12-26 | v2.0 | 新架构：App不再直接调用第三方API，统一由Server处理 |
| 2024-12-25 | v1.0 | 初版积分系统上线 |

