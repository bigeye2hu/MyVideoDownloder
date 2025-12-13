@echo off
chcp 65001 >nul

echo 停止高尔夫视频下载 API 服务...
echo.

cd /d "%~dp0"

wsl docker-compose -f docker-compose.cloudflare.yml down

echo.
echo ✅ 服务已停止
pause

