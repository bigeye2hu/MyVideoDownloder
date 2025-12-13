@echo off
chcp 65001 >nul
echo ================================
echo 高尔夫视频下载 API - 服务状态
echo ================================
echo.

wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker-compose -f docker-compose.golf.yml ps"

echo.
echo 按任意键退出...
pause >nul

