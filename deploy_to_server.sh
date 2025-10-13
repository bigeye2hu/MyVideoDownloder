#!/bin/bash

# Douyin_TikTok_Download_API 部署更新脚本
# 用于在服务器 165.232.131.40 上更新部署

echo "=========================================="
echo "Douyin_TikTok_Download_API 部署更新脚本"
echo "服务器: 165.232.131.40"
echo "=========================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

echo "✅ Docker 和 Docker Compose 已安装"

# 停止当前运行的容器和服务
echo "🛑 停止当前运行的服务..."
sudo systemctl stop Douyin_TikTok_Download_API.service 2>/dev/null || echo "服务未运行或不存在"

# 停止当前运行的Docker容器
echo "🛑 停止当前的Docker容器..."
docker stop douyin_tiktok_api 2>/dev/null || echo "容器未运行或不存在"

# 删除旧的容器
echo "🗑️ 删除旧的容器..."
docker rm douyin_tiktok_api 2>/dev/null || echo "容器不存在或已删除"

# 删除旧的镜像（可选，节省空间）
echo "🗑️ 删除旧的镜像..."
docker rmi evil0ctal/douyin_tiktok_download_api:current 2>/dev/null || echo "旧镜像不存在"

# 给新镜像打标签为 current
echo "🏷️ 拉取最新镜像并打标签..."
docker pull evil0ctal/douyin_tiktok_download_api:latest
docker tag evil0ctal/douyin_tiktok_download_api:latest evil0ctal/douyin_tiktok_download_api:current

# 重新创建并启动容器
echo "🚀 重新创建并启动容器..."
docker-compose up -d

# 检查容器状态
echo "🔍 检查容器状态..."
docker ps | grep douyin_tiktok_api

if [ $? -eq 0 ]; then
    echo "✅ 容器启动成功！"
    echo ""
    echo "📋 服务信息:"
    echo "   - 容器名: douyin_tiktok_api"
    echo "   - 端口映射: 8080 -> 80"
    echo "   - API地址: http://165.232.131.40:8081"
    echo "   - API文档: http://165.232.131.40:8080/docs"
    echo ""
    echo "🔧 配置文件位置:"
    echo "   - /www/wwwroot/Douyin_TikTok_Download_API/config.yaml"
    echo ""
    echo "📝 日志文件位置:"
    echo "   - /www/wwwroot/Douyin_TikTok_Download_API/logs/"
else
    echo "❌ 容器启动失败，请检查日志"
    docker logs douyin_tiktok_api
fi

echo "=========================================="
echo "部署完成！"
echo "=========================================="

