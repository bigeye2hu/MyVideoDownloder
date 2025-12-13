# 高尔夫视频下载 API - CloudFlare Tunnel 部署指南

## 📋 部署概览

通过 CloudFlare Tunnel 将你的视频下载 API 安全地暴露到公网，供高尔夫 App 使用。使用 Docker Desktop 实现服务的持续化运行。

## 🚀 快速开始

### 步骤 1: 创建 CloudFlare Tunnel

1. 访问 [CloudFlare Zero Trust Dashboard](https://one.dash.cloudflare.com/)
2. 进入 **Access** → **Tunnels**
3. 点击 **Create a tunnel**
4. 选择 **Cloudflared**
5. 输入 Tunnel 名称（例如：`golf-video-api`）
6. 点击 **Save tunnel**

### 步骤 2: 配置 Tunnel Token

在 CloudFlare 界面会显示你的 Tunnel Token，复制它：

```bash
# 在项目根目录创建 .env 文件
cd MyVideoDownloder
cp .env.example .env
```

编辑 `.env` 文件，填入你的 Token：

```env
TUNNEL_TOKEN=你的实际token
```

### 步骤 3: 配置公网域名

在 CloudFlare Tunnel 配置页面的 **Public Hostname** 部分：

1. **Subdomain**: 填入子域名（例如：`golf-video-api`）
2. **Domain**: 选择你的域名（例如：`yourdomain.com`）
3. **Service**: 
   - Type: `HTTP`
   - URL: `video_downloader_api:80`
4. 点击 **Save hostname**

最终访问地址将是：`https://golf-video-api.yourdomain.com`

### 步骤 4: 启动服务

使用 Docker Desktop 启动服务：

```bash
# 构建并启动所有服务（包括 API 和 CloudFlare Tunnel）
docker-compose -f docker-compose.cloudflare.yml up -d --build
```

### 步骤 5: 验证服务

```bash
# 查看服务状态
docker-compose -f docker-compose.cloudflare.yml ps

# 查看 API 日志
docker logs golf_video_downloader_api

# 查看 Tunnel 日志
docker logs golf_cloudflare_tunnel
```

访问你的 API 文档：
- 公网：`https://golf-video-api.yourdomain.com/docs`
- 本地：`http://localhost:8081/docs`

## 📱 高尔夫 App 集成

在你的高尔夫 App 中使用以下 API 端点：

```
基础 URL: https://golf-video-api.yourdomain.com

API 文档: /docs
视频解析: /api/hybrid/video_data
下载接口: /api/download
```

### 示例请求

```bash
# 测试 API 连接
curl https://golf-video-api.yourdomain.com/docs

# 解析视频（混合接口，支持抖音、TikTok、B站等）
curl -X POST "https://golf-video-api.yourdomain.com/api/hybrid/video_data" \
  -H "Content-Type: application/json" \
  -d '{"url": "视频链接"}'
```

## 🔧 管理命令

### 启动服务
```bash
docker-compose -f docker-compose.cloudflare.yml up -d
```

### 停止服务
```bash
docker-compose -f docker-compose.cloudflare.yml down
```

### 重启服务
```bash
docker-compose -f docker-compose.cloudflare.yml restart
```

### 查看日志
```bash
# 所有服务日志
docker-compose -f docker-compose.cloudflare.yml logs -f

# 仅 API 日志
docker logs -f golf_video_downloader_api

# 仅 Tunnel 日志
docker logs -f golf_cloudflare_tunnel
```

### 重新构建
```bash
docker-compose -f docker-compose.cloudflare.yml up -d --build --force-recreate
```

## 🔒 安全配置

### 1. 添加 API 密钥验证（可选）

编辑 `config.yaml`，设置自定义 API Key：

```yaml
API:
  API_Key: "你的自定义密钥"
```

### 2. CloudFlare Access 策略（推荐）

在 CloudFlare Zero Trust 中配置访问策略：

1. 进入 **Access** → **Applications**
2. 点击 **Add an application**
3. 选择 **Self-hosted**
4. 配置你的域名和访问规则
5. 可以设置 IP 白名单、地理位置限制等

### 3. 限流保护

在 CloudFlare Dashboard 中：

1. 进入你的域名设置
2. **Security** → **WAF** → **Rate limiting rules**
3. 创建规则限制请求频率

## 📊 监控和维护

### 健康检查

API 服务自带健康检查，每 30 秒检查一次：

```bash
# 手动检查 API 健康状态
curl http://localhost:8081/docs
```

### 日志管理

日志存储在 `./logs` 目录：

```bash
# 查看最新日志
ls -lth logs/ | head

# 清理旧日志（可选）
find logs/ -name "*.log" -mtime +7 -delete
```

### 下载文件管理

下载的文件存储在 `./download` 目录：

```bash
# 查看下载文件
ls -lh download/

# 定期清理（建议设置定时任务）
find download/ -type f -mtime +1 -delete
```

## 🐛 故障排查

### Tunnel 连接失败

```bash
# 检查 Token 是否正确
docker logs golf_cloudflare_tunnel

# 重启 Tunnel
docker restart golf_cloudflare_tunnel
```

### API 服务无响应

```bash
# 检查服务状态
docker ps | grep golf

# 查看 API 日志
docker logs --tail 100 golf_video_downloader_api

# 重启 API 服务
docker restart golf_video_downloader_api
```

### 网络连接问题

```bash
# 测试容器间网络
docker exec golf_cloudflare_tunnel ping video_downloader_api

# 检查端口占用
netstat -ano | findstr :8081
```

## 🔄 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose -f docker-compose.cloudflare.yml up -d --build
```

## 📝 Docker Desktop 配置

### 确保服务自动启动

1. 打开 Docker Desktop
2. 进入 **Settings** → **General**
3. 勾选 **Start Docker Desktop when you log in**
4. 勾选 **Automatically check for updates**

### 资源配置

在 **Settings** → **Resources** 中：
- **CPUs**: 建议至少 2 核
- **Memory**: 建议至少 4GB
- **Disk**: 根据需要调整

## 🌐 支持的视频平台

- ✅ 抖音（Douyin）
- ✅ TikTok
- ✅ 哔哩哔哩（Bilibili）
- ✅ 快手（需要配置）
- ✅ YouTube Shorts（需要配置）

## 📞 技术支持

- API 文档：`https://你的域名/docs`
- 项目地址：https://github.com/Evil0ctal/Douyin_TikTok_Download_API
- 问题反馈：在项目 GitHub 提 Issue

## ⚠️ 注意事项

1. **合法使用**：仅用于学习和合法用途，遵守视频平台的使用条款
2. **流量控制**：建议在 CloudFlare 配置限流，防止滥用
3. **数据清理**：定期清理下载目录，避免磁盘占用过高
4. **安全更新**：定期更新服务镜像和依赖
5. **备份配置**：定期备份 `.env` 和 `config.yaml` 文件

## 📈 性能优化

### 1. 增加并发处理能力

编辑 `config.yaml`：

```yaml
API:
  Max_Workers: 4  # 增加工作线程数
```

### 2. CloudFlare 缓存优化

在 CloudFlare Dashboard 中：
- 启用 **Argo Smart Routing**（需付费）
- 配置 **Page Rules** 优化缓存策略

### 3. Docker 性能优化

```yaml
# 在 docker-compose.cloudflare.yml 中添加资源限制
services:
  video_downloader_api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## 🎯 完成！

你的高尔夫视频下载 API 现在已经：
- ✅ 通过 CloudFlare Tunnel 安全暴露到公网
- ✅ 使用 Docker Desktop 持续化运行
- ✅ 自动重启和健康检查
- ✅ 准备好供高尔夫 App 调用

访问 `https://你的域名/docs` 开始使用！

