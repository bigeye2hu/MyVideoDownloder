# 高尔夫视频下载 API - 使用指南

## 📋 快速开始

### 环境说明
- **开发环境**: WSL Ubuntu 22.04
- **容器运行**: Windows Docker Desktop
- **公网暴露**: CloudFlare Tunnel
- **应用场景**: 高尔夫 App 视频下载

## 🚀 部署步骤

### 步骤 1: 获取 CloudFlare Tunnel Token

1. 访问 [CloudFlare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. 导航到 **Networks** → **Tunnels**
3. 点击 **Create a tunnel**
4. 选择 **Cloudflared** 类型
5. 输入 Tunnel 名称（例如：`golf-video-api`）
6. 点击 **Save tunnel**
7. **复制显示的 Token**（格式类似：`eyJhIjoiXXXXXXXXXXXXX...`）

### 步骤 2: 配置环境变量

在 WSL Ubuntu 中：

```bash
cd ~/projects/MyVideoDownloader/MyVideoDownloder

# 复制示例配置
cp .env.example .env

# 编辑配置文件
nano .env
```

修改 `.env` 文件：

```env
# 粘贴你从 CloudFlare 复制的 Token
TUNNEL_TOKEN=eyJhIjoiXXXXXXXXXXXXX...

# API 密钥（可选，用于验证）
API_KEY=15UHOdNA1nO0wzCjLY3PzU3dLAWLBMZc3ieJih+qbObgoVOWPiatKzmaMw==

# 时区
TZ=Asia/Shanghai
```

保存并退出（Ctrl+X, Y, Enter）

### 步骤 3: 部署服务

#### 方式 A: 在 WSL 中部署（推荐）

```bash
cd ~/projects/MyVideoDownloader/MyVideoDownloder

# 添加执行权限
chmod +x 部署到高尔夫.sh

# 运行部署脚本
./部署到高尔夫.sh
```

#### 方式 B: 在 Windows 中部署

双击运行：`Windows启动.bat`

### 步骤 4: 配置 CloudFlare 公网访问

1. 返回 CloudFlare Tunnel Dashboard
2. 在你创建的 Tunnel 页面，找到 **Public Hostname** 部分
3. 点击 **Add a public hostname**
4. 配置：
   - **Subdomain**: `golf-video-api`（或你喜欢的名字）
   - **Domain**: 选择你的域名（需要先在 CloudFlare 添加域名）
   - **Service**:
     - Type: `HTTP`
     - URL: `golf_video_api:80`
5. 点击 **Save hostname**

完成后，你的 API 将可以通过以下地址访问：
- 公网：`https://golf-video-api.你的域名.com`
- 本地：`http://localhost:8081`

## 🔧 管理操作

### 查看服务状态

**WSL:**
```bash
cd ~/projects/MyVideoDownloader/MyVideoDownloder
docker-compose -f docker-compose.golf.yml ps
```

**Windows:**
双击：`Windows查看状态.bat`

### 查看日志

**WSL:**
```bash
# 查看 API 日志
docker logs -f golf_video_api

# 查看 CloudFlare Tunnel 日志
docker logs -f golf_cloudflare_tunnel

# 查看所有日志
docker-compose -f docker-compose.golf.yml logs -f
```

**Windows:**
双击：`Windows查看日志.bat`

### 停止服务

**WSL:**
```bash
cd ~/projects/MyVideoDownloader/MyVideoDownloder
docker-compose -f docker-compose.golf.yml down
```

**Windows:**
双击：`Windows停止服务.bat`

### 重启服务

**WSL:**
```bash
cd ~/projects/MyVideoDownloader/MyVideoDownloder
docker-compose -f docker-compose.golf.yml restart
```

### 更新服务

```bash
cd ~/projects/MyVideoDownloader/MyVideoDownloder

# 拉取最新代码
git pull

# 重新构建并启动
docker-compose -f docker-compose.golf.yml up -d --build
```

## 📱 在高尔夫 App 中使用

### API 基础信息

```
基础 URL: https://golf-video-api.你的域名.com
API 文档: https://golf-video-api.你的域名.com/docs
```

### 主要 API 端点

#### 1. 混合视频解析（推荐）

支持多个平台的视频链接自动识别和解析。

**端点:** `POST /api/hybrid/video_data`

**请求体:**
```json
{
  "url": "视频分享链接"
}
```

**示例:**

```bash
# 解析抖音视频
curl -X POST "https://golf-video-api.你的域名.com/api/hybrid/video_data" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://v.douyin.com/xxxxx/"
  }'

# 解析 TikTok 视频
curl -X POST "https://golf-video-api.你的域名.com/api/hybrid/video_data" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.tiktok.com/@username/video/xxxxx"
  }'
```

**响应示例:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "aweme_id": "7123456789012345678",
    "video_url": "https://...",
    "cover_url": "https://...",
    "title": "视频标题",
    "author": {
      "nickname": "作者昵称",
      "avatar": "https://..."
    },
    "statistics": {
      "like_count": 12345,
      "comment_count": 678,
      "share_count": 90
    }
  }
}
```

#### 2. 直接下载视频

**端点:** `GET /api/download`

**参数:**
- `url`: 视频链接
- `prefix`: 文件名前缀（可选）
- `with_watermark`: 是否包含水印（可选，默认 false）

**示例:**
```bash
curl "https://golf-video-api.你的域名.com/api/download?url=https://v.douyin.com/xxxxx/" \
  --output video.mp4
```

#### 3. iOS 快捷指令支持

**端点:** `POST /api/ios_shortcut`

专为 iOS 快捷指令优化的接口。

### Swift 代码示例

```swift
import Foundation

struct VideoDownloadRequest: Codable {
    let url: String
}

struct VideoResponse: Codable {
    let code: Int
    let message: String
    let data: VideoData
}

struct VideoData: Codable {
    let awemeId: String
    let videoUrl: String
    let coverUrl: String
    let title: String
    
    enum CodingKeys: String, CodingKey {
        case awemeId = "aweme_id"
        case videoUrl = "video_url"
        case coverUrl = "cover_url"
        case title
    }
}

class VideoDownloadService {
    static let shared = VideoDownloadService()
    private let baseURL = "https://golf-video-api.你的域名.com"
    
    func parseVideo(url: String, completion: @escaping (Result<VideoData, Error>) -> Void) {
        let endpoint = "\(baseURL)/api/hybrid/video_data"
        
        guard let requestURL = URL(string: endpoint) else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1)))
            return
        }
        
        var request = URLRequest(url: requestURL)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let body = VideoDownloadRequest(url: url)
        request.httpBody = try? JSONEncoder().encode(body)
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else {
                completion(.failure(NSError(domain: "No data", code: -1)))
                return
            }
            
            do {
                let response = try JSONDecoder().decode(VideoResponse.self, from: data)
                completion(.success(response.data))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    func downloadVideo(url: String, completion: @escaping (Result<URL, Error>) -> Void) {
        let endpoint = "\(baseURL)/api/download"
        
        guard var components = URLComponents(string: endpoint) else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1)))
            return
        }
        
        components.queryItems = [URLQueryItem(name: "url", value: url)]
        
        guard let requestURL = components.url else {
            completion(.failure(NSError(domain: "Invalid URL", code: -1)))
            return
        }
        
        let downloadTask = URLSession.shared.downloadTask(with: requestURL) { localURL, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let localURL = localURL else {
                completion(.failure(NSError(domain: "No file", code: -1)))
                return
            }
            
            // 移动到永久位置
            let documentsPath = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            let destinationURL = documentsPath.appendingPathComponent("downloaded_video.mp4")
            
            do {
                if FileManager.default.fileExists(atPath: destinationURL.path) {
                    try FileManager.default.removeItem(at: destinationURL)
                }
                try FileManager.default.moveItem(at: localURL, to: destinationURL)
                completion(.success(destinationURL))
            } catch {
                completion(.failure(error))
            }
        }
        downloadTask.resume()
    }
}

// 使用示例
VideoDownloadService.shared.parseVideo(url: "https://v.douyin.com/xxxxx/") { result in
    switch result {
    case .success(let videoData):
        print("视频标题: \(videoData.title)")
        print("视频 URL: \(videoData.videoUrl)")
    case .failure(let error):
        print("错误: \(error)")
    }
}
```

## 🎯 支持的平台

- ✅ 抖音（Douyin）
- ✅ TikTok（国际版）
- ✅ 哔哩哔哩（Bilibili）

## 🔒 安全配置

### 1. API 密钥验证（推荐）

如果启用了 API 密钥验证，需要在请求头中包含：

```bash
curl -X POST "https://golf-video-api.你的域名.com/api/hybrid/video_data" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 你的API密钥" \
  -d '{"url": "..."}'
```

### 2. CloudFlare 访问策略

在 CloudFlare Zero Trust 中配置访问控制：
1. 进入 **Access** → **Applications**
2. 添加应用
3. 配置访问规则（如：仅允许特定国家/IP 访问）

### 3. 速率限制

在 CloudFlare Dashboard 中：
1. 选择你的域名
2. **Security** → **WAF** → **Rate limiting rules**
3. 创建规则（例如：每分钟 60 请求）

## 📊 监控和维护

### 健康检查

```bash
# 检查 API 是否正常
curl https://golf-video-api.你的域名.com/docs

# 检查本地服务
curl http://localhost:8081/docs
```

### 日志管理

日志位置：`./logs/`

```bash
# 查看最新日志
ls -lth logs/ | head

# 清理 7 天前的日志
find logs/ -name "*.log" -mtime +7 -delete
```

### 磁盘空间管理

下载文件位置：`./download/`

```bash
# 查看下载目录大小
du -sh download/

# 清理下载目录
rm -rf download/*
```

## 🐛 故障排查

### 问题 1: CloudFlare Tunnel 连接失败

```bash
# 查看 Tunnel 日志
docker logs golf_cloudflare_tunnel

# 检查 Token 是否正确
cat .env | grep TUNNEL_TOKEN

# 重启 Tunnel
docker restart golf_cloudflare_tunnel
```

### 问题 2: API 无响应

```bash
# 查看 API 日志
docker logs golf_video_api --tail 100

# 检查端口占用
netstat -ano | grep 8081

# 重启 API 服务
docker restart golf_video_api
```

### 问题 3: 视频下载失败

可能原因：
- 视频链接失效
- 平台更新了接口
- 网络连接问题

解决方案：
```bash
# 检查日志中的错误信息
docker logs golf_video_api | grep ERROR

# 测试本地访问
curl -X POST http://localhost:8081/api/hybrid/video_data \
  -H "Content-Type: application/json" \
  -d '{"url": "测试链接"}'
```

## 🔄 Docker Desktop 配置

### 确保自动启动

1. 打开 Docker Desktop
2. **Settings** → **General**
3. 勾选 **Start Docker Desktop when you log in**
4. 勾选 **Use Docker Compose V2**

### 资源配置

**Settings** → **Resources**:
- **CPUs**: 建议至少 2 核
- **Memory**: 建议至少 4GB
- **Disk**: 根据视频下载量调整

### WSL 集成

**Settings** → **Resources** → **WSL Integration**:
- 勾选 **Enable integration with my default WSL distro**
- 启用 **Ubuntu-22.04**

## 📈 性能优化

### 1. 增加并发处理

编辑 `config.yaml`:

```yaml
API:
  Max_Workers: 4  # 增加工作线程
```

### 2. CloudFlare 性能优化

- 启用 **Argo Smart Routing**（加速全球访问）
- 配置 **Cache Rules**（缓存静态资源）
- 启用 **HTTP/3**（QUIC 协议）

### 3. Docker 资源限制

编辑 `docker-compose.golf.yml`:

```yaml
services:
  golf_video_api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## 🎉 完成！

你的高尔夫视频下载 API 现在已经：
- ✅ 在 WSL Ubuntu 中运行
- ✅ 通过 Docker Desktop 持续化
- ✅ 通过 CloudFlare Tunnel 公网可访问
- ✅ 随 Windows 开机自动启动

访问 API 文档开始使用：
- 本地：http://localhost:8081/docs
- 公网：https://golf-video-api.你的域名.com/docs

## 📞 技术支持

- 问题反馈: [GitHub Issues](https://github.com/Evil0ctal/Douyin_TikTok_Download_API/issues)
- API 文档: https://golf-video-api.你的域名.com/docs
- CloudFlare 文档: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/

