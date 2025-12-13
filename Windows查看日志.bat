@echo off
chcp 65001 >nul
echo ================================
echo 高尔夫视频下载 API - 服务日志
echo ================================
echo.
echo 选择要查看的日志：
echo 1. API 服务日志
echo 2. CloudFlare Tunnel 日志
echo 3. 所有日志
echo.

set /p choice=请输入选项 (1-3): 

if "%choice%"=="1" (
    wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker logs -f golf_video_api"
) else if "%choice%"=="2" (
    wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker logs -f golf_cloudflare_tunnel"
) else if "%choice%"=="3" (
    wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker-compose -f docker-compose.golf.yml logs -f"
) else (
    echo 无效选项
    pause
)

