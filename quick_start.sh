#!/bin/bash

# 高尔夫视频下载 API - 快速启动脚本

set -e

echo "======================================"
echo "高尔夫视频下载 API - CloudFlare 部署"
echo "======================================"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "❌ 错误: 未找到 .env 文件"
    echo "请先复制 .env.example 到 .env 并填入你的 TUNNEL_TOKEN"
    echo ""
    echo "运行以下命令："
    echo "  cp .env.example .env"
    echo "  然后编辑 .env 文件填入你的 CloudFlare Tunnel Token"
    exit 1
fi

# 检查 TUNNEL_TOKEN
source .env
if [ "$TUNNEL_TOKEN" == "your_tunnel_token_here" ] || [ -z "$TUNNEL_TOKEN" ]; then
    echo "❌ 错误: TUNNEL_TOKEN 未配置"
    echo "请编辑 .env 文件，填入你的 CloudFlare Tunnel Token"
    exit 1
fi

echo ""
echo "✅ 配置检查通过"
echo ""

# 停止旧服务
echo "停止旧服务..."
docker-compose -f docker-compose.cloudflare.yml down 2>/dev/null || true

echo ""
echo "构建并启动服务..."
docker-compose -f docker-compose.cloudflare.yml up -d --build

echo ""
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo ""
echo "======================================"
echo "服务状态："
echo "======================================"
docker-compose -f docker-compose.cloudflare.yml ps

echo ""
echo "======================================"
echo "✅ 部署完成！"
echo "======================================"
echo ""
echo "📝 服务信息："
echo "  - 本地访问: http://localhost:8081/docs"
echo "  - 公网访问: https://你的域名/docs"
echo ""
echo "🔍 查看日志："
echo "  - API 日志: docker logs -f golf_video_downloader_api"
echo "  - Tunnel 日志: docker logs -f golf_cloudflare_tunnel"
echo ""
echo "🛠️  管理命令："
echo "  - 停止服务: docker-compose -f docker-compose.cloudflare.yml down"
echo "  - 重启服务: docker-compose -f docker-compose.cloudflare.yml restart"
echo "  - 查看状态: docker-compose -f docker-compose.cloudflare.yml ps"
echo ""

