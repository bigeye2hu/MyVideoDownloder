#!/bin/bash

# 停止高尔夫视频下载 API 服务

echo "正在停止服务..."
docker-compose -f docker-compose.cloudflare.yml down

echo ""
echo "✅ 服务已停止"
