#!/bin/bash

# 一键测试脚本 - 测试服务是否正常运行

echo "测试本地 API 服务..."
echo ""

# 测试 API 文档页面
echo "1. 测试 API 文档页面..."
if curl -s http://localhost:8081/docs > /dev/null; then
    echo "✓ API 文档页面访问正常"
else
    echo "✗ API 文档页面访问失败"
fi

echo ""

# 测试混合视频解析接口
echo "2. 测试混合视频解析接口（使用测试链接）..."
response=$(curl -s -X POST "http://localhost:8081/api/hybrid/video_data" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://v.douyin.com/iJsyErwJ/"}' 2>&1)

if echo "$response" | grep -q "code"; then
    echo "✓ 视频解析接口响应正常"
    echo "响应: $response" | head -c 200
    echo "..."
else
    echo "✗ 视频解析接口响应异常"
    echo "响应: $response"
fi

echo ""
echo ""

# 显示容器状态
echo "3. 容器运行状态："
docker-compose -f docker-compose.golf.yml ps

echo ""
echo "测试完成！"

