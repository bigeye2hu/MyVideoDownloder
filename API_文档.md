# 抖音视频下载 API 文档

## 概述

本API服务基于 TikHub API 提供抖音视频解析和下载功能，用户只需传入抖音视频链接即可获取完整的视频信息和下载地址。

## 基础信息

- **服务地址**: `http://165.232.131.40:8081`
- **API版本**: v3
- **数据格式**: JSON
- **编码**: UTF-8

## API 端点

### 1. 通过视频链接获取视频信息

**端点**: `GET /api/douyin/app/v3/fetch_one_video_by_url`

**描述**: 传入抖音视频链接，自动解析并返回完整的视频信息，包括下载链接

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|--------|------|------|------|------|
| url | string | 是 | 抖音视频链接 | `https://www.douyin.com/video/7550257032533658940` |

#### 请求示例

```bash
curl "http://165.232.131.40:8081/api/douyin/app/v3/fetch_one_video_by_url?url=https://www.douyin.com/video/7550257032533658940"
```

#### 响应格式

```json
{
  "code": 200,
  "message": "Request successful. This request will incur a charge.",
  "message_zh": "请求成功，本次请求将被计费。",
  "time": "2025-09-16 03:14:02",
  "data": {
    "aweme_id": "7550257032533658940",
    "desc": "第一次打 培养个新爱好\n#高尔夫练习 #健身 #挥杆",
    "author": {
      "nickname": "甜甜的天天",
      "avatar_thumb": {
        "url_list": ["https://..."]
      }
    },
    "video": {
      "play_addr_h264": {
        "url_list": [
          "https://v5-hl-zenl-ov.zjcdn.com/8bde3e9e98c1a7cbacd6aa67d8457544/68ca3150/video/tos/cn/tos-cn-ve-15c000-ce/oEcBvE0DgyBCTavFfKR7JQAuIfINGjEXe8v3I8/..."
        ],
        "width": 576,
        "height": 1024,
        "data_size": 1226079
      },
      "download_addr": {
        "url_list": [
          "https://v5-hl-zenl-ov.zjcdn.com/0f56d10797a77d6e25ab85ed79fed0c7/68ca30dc/video/tos/cn/tos-cn-ve-15c000-ce/ok0a3Q8DRC5uyGvFEB1eyAIfBJTHfj2gN7Evr8/..."
        ],
        "width": 720,
        "height": 720,
        "data_size": 1927852
      },
      "bit_rate": [
        {
          "gear_name": "1080_1_1",
          "quality_type": 3,
          "bit_rate": 1242724,
          "play_addr": {
            "url_list": [
              "https://v5-hl-zenl-ov.zjcdn.com/974a58c48706e1407c17cc4bfd9f18a0/68ca30dc/video/tos/cn/tos-cn-ve-15c000-ce/ocgBvEeTRJOzFy8uADCAnyXjFQaI8Ef7cBNfI0/..."
            ],
            "width": 1080,
            "height": 1920,
            "data_size": 1287773
          }
        }
      ],
      "cover": {
        "url_list": [
          "https://p3-sign.douyinpic.com/tos-cn-p-0015c000-ce/oMyH8faE4N7TBIhEnCFRA53Dg08KsJ2sfejBvu~tplv-dy-resize-walign-adapt-aq:540:q75.webp?..."
        ],
        "width": 540,
        "height": 960
      },
      "duration": 8289,
      "has_watermark": true
    },
    "statistics": {
      "digg_count": 11437,
      "share_count": 1781,
      "comment_count": 119,
      "collect_count": 2179,
      "download_count": 168
    }
  }
}
```

### 2. 通过视频ID获取视频信息

**端点**: `GET /api/douyin/app/v3/fetch_one_video`

**描述**: 通过抖音视频ID (aweme_id) 获取视频信息

#### 请求参数

| 参数名 | 类型 | 必填 | 描述 | 示例 |
|--------|------|------|------|------|
| aweme_id | string | 是 | 抖音作品ID | `7550257032533658940` |

#### 请求示例

```bash
curl "http://165.232.131.40:8081/api/douyin/app/v3/fetch_one_video?aweme_id=7550257032533658940"
```

## 视频下载链接说明

### 下载链接类型

1. **无水印视频** (`video.play_addr_h264.url_list[0]`)
   - 格式: H.264
   - 特点: 无水印，适合直接观看
   - 分辨率: 通常为540p

2. **带水印视频** (`video.download_addr.url_list[0]`)
   - 格式: H.264
   - 特点: 带有抖音水印
   - 分辨率: 通常为720p

3. **多清晰度视频** (`video.bit_rate[].play_addr.url_list[0]`)
   - 格式: 支持H.264和H.265
   - 清晰度: 1080p, 720p, 540p等
   - 特点: 可选择不同质量

### 下载方式

#### 方法1: 直接下载
```bash
# 获取视频信息
response=$(curl -s "http://165.232.131.40:8081/api/douyin/app/v3/fetch_one_video_by_url?url=https://www.douyin.com/video/7550257032533658940")

# 提取下载链接
download_url=$(echo $response | jq -r '.data.video.play_addr_h264.url_list[0]')

# 下载视频
curl -o video.mp4 "$download_url"
```

#### 方法2: 前端下载
```javascript
// 获取视频信息
const response = await fetch('/api/douyin/app/v3/fetch_one_video_by_url?url=https://www.douyin.com/video/7550257032533658940');
const data = await response.json();

// 提取下载链接
const downloadUrl = data.data.video.play_addr_h264.url_list[0];

// 创建下载链接
const a = document.createElement('a');
a.href = downloadUrl;
a.download = 'video.mp4';
a.click();
```

## 错误码说明

| 错误码 | 描述 | 解决方案 |
|--------|------|----------|
| 200 | 请求成功 | - |
| 400 | 请求参数错误 | 检查url参数格式 |
| 500 | 服务器配置错误 | 检查TIKHUB_API_KEY配置 |
| 502 | TikHub上游服务错误 | 稍后重试 |

## 使用注意事项

1. **API密钥**: 服务需要配置有效的 TikHub API 密钥
2. **请求频率**: 请遵守 TikHub API 的使用限制
3. **链接有效期**: 视频下载链接有时效性，建议及时下载
4. **版权声明**: 请遵守相关法律法规，仅用于个人学习研究

## 完整示例

### Python 示例
```python
import requests
import json

def download_douyin_video(video_url):
    # 获取视频信息
    api_url = "http://165.232.131.40:8081/api/douyin/app/v3/fetch_one_video_by_url"
    params = {"url": video_url}
    
    response = requests.get(api_url, params=params)
    data = response.json()
    
    if data["code"] == 200:
        video_info = data["data"]
        
        # 获取无水印下载链接
        download_url = video_info["video"]["play_addr_h264"]["url_list"][0]
        
        # 下载视频
        video_response = requests.get(download_url)
        with open("video.mp4", "wb") as f:
            f.write(video_response.content)
        
        print(f"视频下载完成: {video_info['desc']}")
        return True
    else:
        print(f"获取视频信息失败: {data['message']}")
        return False

# 使用示例
download_douyin_video("https://www.douyin.com/video/7550257032533658940")
```

### JavaScript 示例
```javascript
async function downloadDouyinVideo(videoUrl) {
    try {
        // 获取视频信息
        const response = await fetch(`/api/douyin/app/v3/fetch_one_video_by_url?url=${encodeURIComponent(videoUrl)}`);
        const data = await response.json();
        
        if (data.code === 200) {
            const videoInfo = data.data;
            
            // 获取无水印下载链接
            const downloadUrl = videoInfo.video.play_addr_h264.url_list[0];
            
            // 创建下载链接
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = `${videoInfo.desc.substring(0, 20)}.mp4`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            
            console.log('视频下载开始:', videoInfo.desc);
            return true;
        } else {
            console.error('获取视频信息失败:', data.message);
            return false;
        }
    } catch (error) {
        console.error('下载失败:', error);
        return false;
    }
}

// 使用示例
downloadDouyinVideo("https://www.douyin.com/video/7550257032533658940");
```

## 更新日志

- **v3.0.0** (2025-09-16)
  - 集成 TikHub API
  - 新增 `fetch_one_video_by_url` 端点
  - 支持通过视频链接直接获取下载地址
  - 移除其他平台支持，专注抖音视频下载

---

**技术支持**: 如有问题请联系技术支持团队
