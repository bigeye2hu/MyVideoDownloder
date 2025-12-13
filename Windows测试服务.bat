@echo off
chcp 65001 >nul
echo ================================
echo 高尔夫视频下载 API - 服务测试
echo ================================
echo.

echo 测试 API 服务...
echo.

echo 1. 测试 API 文档页面
curl -s http://localhost:8081/docs >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] API 文档页面访问正常
) else (
    echo [×] API 文档页面访问失败 - 请检查服务是否启动
)

echo.
echo 2. 测试视频解析接口
curl -s -X POST "http://localhost:8081/api/hybrid/video_data" -H "Content-Type: application/json" -d "{\"url\": \"https://v.douyin.com/iJsyErwJ/\"}" >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] 视频解析接口响应正常
) else (
    echo [×] 视频解析接口响应异常
)

echo.
echo 3. 查看容器状态
echo.
wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker-compose -f docker-compose.golf.yml ps"

echo.
echo ================================
echo 测试完成！
echo ================================
echo.
echo 如果所有测试通过，你的 API 已准备就绪
echo 本地访问：http://localhost:8081/docs
echo.
echo 按任意键退出...
pause >nul

