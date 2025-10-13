#!/bin/bash

# Douyin_TikTok_Download_API 部署测试脚本
# 用于验证部署是否成功

echo "=========================================="
echo "Douyin_TikTok_Download_API 部署测试"
echo "服务器: 165.232.131.40"
echo "=========================================="

SERVER_IP="165.232.131.40"
API_BASE="http://$SERVER_IP:8081"
DOCS_URL="http://$SERVER_IP:8080/docs"

# 测试链接
TEST_URL="https://www.douyin.com/video/7550257032533658940"

echo "🔍 测试服务连通性..."
if curl -s --connect-timeout 10 "$API_BASE/api/douyin/app/v3/fetch_one_video_by_url?url=$TEST_URL" > /dev/null; then
    echo "✅ API服务连通正常"
else
    echo "❌ API服务连接失败，请检查服务是否正常运行"
    echo "   - 检查端口 8081 是否开放"
    echo "   - 检查防火墙设置"
    echo "   - 确认容器是否正常运行: docker ps"
    exit 1
fi

echo ""
echo "🔍 测试API文档访问..."
if curl -s --connect-timeout 10 "$DOCS_URL" > /dev/null; then
    echo "✅ API文档访问正常"
    echo "   文档地址: $DOCS_URL"
else
    echo "⚠️ API文档访问失败，但API服务正常"
    echo "   这可能是端口映射问题"
fi

echo ""
echo "🔍 测试实际API调用..."
echo "📝 测试视频解析API..."

# 构造API请求
API_URL="$API_BASE/api/douyin/app/v3/fetch_one_video_by_url?url=$TEST_URL"

# 发送请求并检查响应
if RESPONSE=$(curl -s --connect-timeout 30 "$API_URL" 2>/dev/null); then
    echo "✅ API请求成功"

    # 检查响应是否包含预期的字段
    if echo "$RESPONSE" | grep -q "video_list\|error"; then
        echo "✅ 响应格式正确"

        # 检查是否有错误信息
        if echo "$RESPONSE" | grep -q '"error"'; then
            echo "⚠️ API返回错误，但服务正常运行"
            echo "   可能需要更新Cookie或其他配置"
        else
            echo "✅ API返回成功，无错误信息"
        fi

        echo ""
        echo "📊 响应摘要:"
        echo "$RESPONSE" | head -c 200
        echo "..."

    else
        echo "❌ 响应格式异常"
    fi

else
    echo "❌ API请求失败"
    echo "   请检查网络连接或服务配置"
fi

echo ""
echo "=========================================="
echo "测试完成"
echo "=========================================="

echo ""
echo "📋 服务状态检查命令（在服务器上执行）:"
echo "   docker ps                    # 查看运行中的容器"
echo "   docker logs douyin_tiktok_api # 查看容器日志"
echo "   netstat -tlnp | grep 8081    # 检查端口监听状态"
echo ""
echo "🔧 如果有问题，请检查:"
echo "   1. Docker服务是否运行: systemctl status docker"
echo "   2. 容器是否正常运行: docker ps"
echo "   3. 端口8081是否开放: netstat -tlnp | grep 8081"
echo "   4. 防火墙设置是否正确"
echo "   5. 配置文件中的Cookie是否有效"

