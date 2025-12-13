@echo off
chcp 65001 >nul
echo ================================
echo 高尔夫视频下载 API - 停止服务
echo ================================
echo.

echo 正在停止服务...
wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker-compose -f docker-compose.golf.yml down"

echo.
echo 服务已停止
echo 按任意键退出...
pause >nul

