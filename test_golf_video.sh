#!/bin/bash

echo "======================================"
echo "测试视频下载 API"
echo "======================================"
echo ""

VIDEO_URL="https://v.douyin.com/8Vmkh6lfxCA/"

echo "测试链接: $VIDEO_URL"
echo ""

echo "1. 本地测试 (localhost:18889)..."
echo "--------------------------------------"
curl -s "http://localhost:18889/api/hybrid/video_data?url=$VIDEO_URL" | head -100
echo ""
echo ""

echo "2. 公网测试 (download.mygolfai.com.cn)..."
echo "--------------------------------------"
curl -s "https://download.mygolfai.com.cn/api/hybrid/video_data?url=$VIDEO_URL" | head -100
echo ""
echo ""

echo "======================================"
echo "测试完成！"
echo "======================================"

