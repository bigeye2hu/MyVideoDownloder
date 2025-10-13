#!/bin/bash

# 抖音API测试脚本
# 测试我们的API节点和官方TikHub API对不同类型链接的处理能力

echo "🚀 开始抖音API测试"
echo "============================================================"

# 配置
OUR_API_BASE="http://165.232.131.40:8081/api/douyin/app/v3"
TIKHUB_API_BASE="https://api.tikhub.io/api/v1"
TIKHUB_API_KEY="15UHOdNA1nO0wzCjLY3PzU3dLAWLBMZc3ieJih+qbObgoVOWPiatKzmaMw=="

# 测试结果统计
TOTAL_TESTS=0
OUR_SUCCESS=0
TIKHUB_WEB_SUCCESS=0
TIKHUB_APP_SUCCESS=0

# 测试函数
test_our_api() {
    local url="$1"
    local test_name="$2"
    
    echo ""
    echo "🔍 测试我们的API - $test_name"
    echo "URL: $url"
    
    response=$(curl -s -w "\n%{http_code}" "$OUR_API_BASE/fetch_one_video_by_url?url=$(echo "$url" | sed 's/:/%3A/g; s/\//%2F/g; s/\?/%3F/g; s/=/%3D/g; s/&/%26/g')")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo "✅ 成功"
        # 尝试提取视频标题
        title=$(echo "$body" | grep -o '"desc":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -n "$title" ]; then
            echo "视频标题: $title"
        fi
        ((OUR_SUCCESS++))
    else
        echo "❌ 失败 (HTTP $http_code)"
        echo "错误信息: $body"
    fi
}

test_tikhub_web_api() {
    local url="$1"
    local test_name="$2"
    
    echo ""
    echo "🔍 测试官方TikHub Web API - $test_name"
    echo "URL: $url"
    
    # 首先获取aweme_id
    echo "步骤1: 获取aweme_id"
    aweme_response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TIKHUB_API_KEY" \
        "$TIKHUB_API_BASE/douyin/web/get_aweme_id?url=$(echo "$url" | sed 's/:/%3A/g; s/\//%2F/g; s/\?/%3F/g; s/=/%3D/g; s/&/%26/g')")
    aweme_http_code=$(echo "$aweme_response" | tail -n1)
    aweme_body=$(echo "$aweme_response" | sed '$d')
    
    if [ "$aweme_http_code" != "200" ]; then
        echo "❌ 获取aweme_id失败 (HTTP $aweme_http_code)"
        echo "错误信息: $aweme_body"
        return
    fi
    
    # 提取aweme_id
    aweme_id=$(echo "$aweme_body" | grep -o '"data":"[^"]*"' | cut -d'"' -f4)
    if [ -z "$aweme_id" ]; then
        echo "❌ 无法提取aweme_id"
        echo "响应: $aweme_body"
        return
    fi
    
    echo "获取到aweme_id: $aweme_id"
    
    # 使用aweme_id获取视频信息
    echo "步骤2: 获取视频信息"
    response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TIKHUB_API_KEY" \
        "$TIKHUB_API_BASE/douyin/web/fetch_one_video?aweme_id=$aweme_id")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo "✅ 成功"
        # 尝试提取视频标题
        title=$(echo "$body" | grep -o '"desc":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -n "$title" ]; then
            echo "视频标题: $title"
        fi
        ((TIKHUB_WEB_SUCCESS++))
    else
        echo "❌ 失败 (HTTP $http_code)"
        echo "错误信息: $body"
    fi
}

test_tikhub_app_api() {
    local url="$1"
    local test_name="$2"
    
    echo ""
    echo "🔍 测试官方TikHub App API - $test_name"
    echo "URL: $url"
    
    # 首先获取aweme_id
    echo "步骤1: 获取aweme_id"
    aweme_response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TIKHUB_API_KEY" \
        "$TIKHUB_API_BASE/douyin/web/get_aweme_id?url=$(echo "$url" | sed 's/:/%3A/g; s/\//%2F/g; s/\?/%3F/g; s/=/%3D/g; s/&/%26/g')")
    aweme_http_code=$(echo "$aweme_response" | tail -n1)
    aweme_body=$(echo "$aweme_response" | sed '$d')
    
    if [ "$aweme_http_code" != "200" ]; then
        echo "❌ 获取aweme_id失败 (HTTP $aweme_http_code)"
        echo "错误信息: $aweme_body"
        return
    fi
    
    # 提取aweme_id
    aweme_id=$(echo "$aweme_body" | grep -o '"data":"[^"]*"' | cut -d'"' -f4)
    if [ -z "$aweme_id" ]; then
        echo "❌ 无法提取aweme_id"
        echo "响应: $aweme_body"
        return
    fi
    
    echo "获取到aweme_id: $aweme_id"
    
    # 使用aweme_id获取视频信息
    echo "步骤2: 获取视频信息"
    response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $TIKHUB_API_KEY" \
        "$TIKHUB_API_BASE/douyin/app/v3/fetch_one_video?aweme_id=$aweme_id")
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" = "200" ]; then
        echo "✅ 成功"
        # 尝试提取视频标题
        title=$(echo "$body" | grep -o '"desc":"[^"]*"' | head -1 | cut -d'"' -f4)
        if [ -n "$title" ]; then
            echo "视频标题: $title"
        fi
        ((TIKHUB_APP_SUCCESS++))
    else
        echo "❌ 失败 (HTTP $http_code)"
        echo "错误信息: $body"
    fi
}

# 测试1: 标准视频链接
echo ""
echo "==================== 标准视频链接 ===================="
test_url="https://www.douyin.com/video/7550257032533658940"
((TOTAL_TESTS++))
test_our_api "$test_url" "标准视频链接"
sleep 1
test_tikhub_web_api "$test_url" "标准视频链接"
sleep 1
test_tikhub_app_api "$test_url" "标准视频链接"
sleep 2

# 测试2: 短链接
echo ""
echo "==================== 短链接 ===================="
test_url="https://v.douyin.com/vsmmotm2-nw/"
((TOTAL_TESTS++))
test_our_api "$test_url" "短链接"
sleep 1
test_tikhub_web_api "$test_url" "短链接"
sleep 1
test_tikhub_app_api "$test_url" "短链接"
sleep 2

# 测试3: 搜索链接
echo ""
echo "==================== 搜索链接 ===================="
test_url="https://www.douyin.com/search/挥杆?modal_id=7527168133914037514&type=general"
((TOTAL_TESTS++))
test_our_api "$test_url" "搜索链接"
sleep 1
test_tikhub_web_api "$test_url" "搜索链接"
sleep 1
test_tikhub_app_api "$test_url" "搜索链接"
sleep 2

# 测试4: 分享文本中的链接
echo ""
echo "==================== 分享文本链接 ===================="
# 从分享文本中提取URL
share_text="8.23 复制打开抖音，看看【申东赫⛳️的作品】不懂但跟 # 高尔夫 # 高尔夫挥杆 # 高尔夫球... https://v.douyin.com/vsmmotm2-nw/ eBt:/ C@U.yt 04/06"
test_url=$(echo "$share_text" | grep -o 'https://v\.douyin\.com/[^[:space:]]*' | head -1)
if [ -n "$test_url" ]; then
    echo "从分享文本中提取的URL: $test_url"
    ((TOTAL_TESTS++))
    test_our_api "$test_url" "分享文本链接"
    sleep 1
    test_tikhub_web_api "$test_url" "分享文本链接"
    sleep 1
    test_tikhub_app_api "$test_url" "分享文本链接"
else
    echo "❌ 无法从分享文本中提取有效URL"
fi

# 生成测试报告
echo ""
echo "============================================================"
echo "📊 测试报告"
echo "============================================================"
echo "总测试数: $TOTAL_TESTS"
echo "我们的API成功率: $OUR_SUCCESS/$TOTAL_TESTS ($(( OUR_SUCCESS * 100 / TOTAL_TESTS ))%)"
echo "TikHub Web API成功率: $TIKHUB_WEB_SUCCESS/$TOTAL_TESTS ($(( TIKHUB_WEB_SUCCESS * 100 / TOTAL_TESTS ))%)"
echo "TikHub App API成功率: $TIKHUB_APP_SUCCESS/$TOTAL_TESTS ($(( TIKHUB_APP_SUCCESS * 100 / TOTAL_TESTS ))%)"

echo ""
echo "📋 结论:"
if [ $OUR_SUCCESS -eq $TOTAL_TESTS ]; then
    echo "✅ 我们的API完全支持所有类型的链接"
elif [ $OUR_SUCCESS -gt 0 ]; then
    echo "⚠️  我们的API部分支持，需要优化"
else
    echo "❌ 我们的API需要重大改进"
fi

if [ $TIKHUB_WEB_SUCCESS -gt $TIKHUB_APP_SUCCESS ]; then
    echo "📝 TikHub Web API表现更好"
elif [ $TIKHUB_APP_SUCCESS -gt $TIKHUB_WEB_SUCCESS ]; then
    echo "📝 TikHub App API表现更好"
else
    echo "📝 TikHub Web和App API表现相当"
fi
