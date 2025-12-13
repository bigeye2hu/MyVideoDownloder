@echo off
chcp 65001 >nul
echo ================================
echo 高尔夫视频下载 API - Windows 启动
echo ================================
echo.

echo 正在切换到 WSL Ubuntu 环境...
wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && bash 部署到高尔夫.sh"

echo.
echo 按任意键退出...
pause >nul

