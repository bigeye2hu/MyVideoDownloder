@echo off
chcp 65001 >nul

echo 重启高尔夫视频下载 API 服务...
echo.

cd /d "%~dp0"

wsl docker-compose -f docker-compose.cloudflare.yml restart

echo.
echo ✅ 服务已重启
pause

