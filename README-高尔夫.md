# 高尔夫视频下载 API

为高尔夫 App 提供视频下载服务，支持抖音、TikTok、B站等平台。

## 📦 项目文件说明

### 配置文件
- `docker-compose.golf.yml` - 高尔夫专用 Docker 配置
- `.env` - 环境变量（需自己创建，包含 CloudFlare Token）
- `config.yaml` - API 配置文件

### Windows 快捷脚本
- `Windows启动.bat` - 一键启动服务
- `Windows查看状态.bat` - 查看服务状态
- `Windows查看日志.bat` - 查看服务日志
- `Windows停止服务.bat` - 停止服务

### Linux 脚本
- `部署到高尔夫.sh` - 完整部署脚本
- `测试服务.sh` - 测试服务是否正常

### 文档
- `快速部署-高尔夫.md` - 快速部署指南（⭐ 从这里开始）
- `高尔夫API使用指南.md` - 完整使用文档

## 🚀 快速开始

### 1. 创建配置文件

在项目目录创建 `.env` 文件：

```env
TUNNEL_TOKEN=你的CloudFlare_Token
TZ=Asia/Shanghai
```

### 2. 启动服务

**Windows:**
双击运行 `Windows启动.bat`

**Linux/WSL:**
```bash
./部署到高尔夫.sh
```

### 3. 配置 CloudFlare

在 CloudFlare Tunnel 中配置：
- Service: `http://golf_video_api:80`
- Domain: 你的域名

### 4. 完成

访问：`https://你的域名/docs`

## 📖 详细文档

完整部署和使用说明请查看：[快速部署-高尔夫.md](快速部署-高尔夫.md)

## 🔗 API 端点

```
POST /api/hybrid/video_data  # 解析视频信息
GET  /api/download           # 直接下载视频
GET  /docs                   # API 文档
```

## 📱 支持平台

- ✅ 抖音（Douyin）
- ✅ TikTok
- ✅ 哔哩哔哩（Bilibili）

## 🛠️ 技术栈

- FastAPI (Python Web 框架)
- Docker Desktop (容器化)
- CloudFlare Tunnel (公网暴露)
- WSL 2 Ubuntu (开发环境)

## 📝 许可

本项目基于原项目：[Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API)

