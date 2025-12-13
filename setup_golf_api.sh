#!/bin/bash

# 高尔夫视频下载 API 部署脚本
# 用于在 Windows Docker Desktop + CloudFlare Tunnel 环境下部署

set -e

echo "========================================"
echo "高尔夫视频下载 API 部署脚本"
echo "========================================"
echo ""

# 检查是否存在 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件"
    echo ""
    echo "请按以下步骤操作："
    echo "1. 复制 .env.example 为 .env："
    echo "   cp .env.example .env"
    echo ""
    echo "2. 访问 CloudFlare Zero Trust: https://one.dash.cloudflare.com/"
    echo "3. 进入 Access → Tunnels → Create a tunnel"
    echo "4. 创建名为 'golf-video-api' 的 tunnel"
    echo "5. 复制 Tunnel Token 并填入 .env 文件"
    echo ""
    echo "6. 在 CloudFlare 配置 Public Hostname："
    echo "   - Subdomain: golf-video-api (或你喜欢的名字)"
    echo "   - Domain: 选择你的域名"
    echo "   - Service: HTTP → video_downloader_api:80"
    echo ""
    read -p "按 Enter 键退出并手动配置..."
    exit 1
fi

# 加载环境变量
source .env

# 检查 TUNNEL_TOKEN 是否已配置
if [ "$TUNNEL_TOKEN" = "你的cloudflare_tunnel_token" ] || [ -z "$TUNNEL_TOKEN" ]; then
    echo "❌ 请先在 .env 文件中配置你的 TUNNEL_TOKEN"
    exit 1
fi

echo "✅ 环境变量配置正确"
echo ""

# 停止旧服务
echo "📦 停止旧服务..."
docker-compose -f docker-compose.cloudflare.yml down 2>/dev/null || true
echo ""

# 构建并启动服务
echo "🚀 构建并启动服务..."
docker-compose -f docker-compose.cloudflare.yml up -d --build

echo ""
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "📊 服务状态："
docker-compose -f docker-compose.cloudflare.yml ps

echo ""
echo "========================================"
echo "✅ 部署完成！"
echo "========================================"
echo ""
echo "📝 服务信息："
echo "  - 本地访问: http://localhost:8081/docs"
echo "  - 公网访问: https://你配置的域名/docs"
echo ""
echo "🔧 管理命令："
echo "  查看日志: docker-compose -f docker-compose.cloudflare.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.cloudflare.yml down"
echo "  重启服务: docker-compose -f docker-compose.cloudflare.yml restart"
echo ""
echo "📱 在高尔夫 App 中使用："
echo "  API 基础 URL: https://你配置的域名"
echo "  视频解析接口: POST /api/hybrid/video_data"
echo ""

