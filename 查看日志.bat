@echo off
chcp 65001 >nul

echo 查看高尔夫视频下载 API 日志...
echo 按 Ctrl+C 退出
echo.

cd /d "%~dp0"

wsl docker-compose -f docker-compose.cloudflare.yml logs -f

