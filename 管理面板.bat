@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:menu
cls
echo ========================================
echo   高尔夫视频下载 API - 管理面板
echo ========================================
echo.
echo   当前时间: %date% %time%
echo.
echo ========================================
echo   [1] 启动服务
echo   [2] 停止服务
echo   [3] 重启服务
echo   [4] 查看状态
echo   [5] 查看日志
echo   [6] 测试服务
echo   [7] 打开本地文档
echo   [8] 打开配置文件
echo   [0] 退出
echo ========================================
echo.

set /p choice=请选择操作 (0-8): 

if "%choice%"=="1" goto start_service
if "%choice%"=="2" goto stop_service
if "%choice%"=="3" goto restart_service
if "%choice%"=="4" goto show_status
if "%choice%"=="5" goto show_logs
if "%choice%"=="6" goto test_service
if "%choice%"=="7" goto open_docs
if "%choice%"=="8" goto open_config
if "%choice%"=="0" goto end
goto menu

:start_service
echo.
echo 正在启动服务...
wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && ./部署到高尔夫.sh"
pause
goto menu

:stop_service
echo.
echo 正在停止服务...
wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker-compose -f docker-compose.golf.yml down"
echo.
echo 服务已停止
pause
goto menu

:restart_service
echo.
echo 正在重启服务...
wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker-compose -f docker-compose.golf.yml restart"
echo.
echo 服务已重启
pause
goto menu

:show_status
echo.
echo 服务状态：
wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker-compose -f docker-compose.golf.yml ps"
echo.
pause
goto menu

:show_logs
cls
echo 选择要查看的日志：
echo   [1] API 服务日志
echo   [2] CloudFlare Tunnel 日志
echo   [3] 所有服务日志
echo   [0] 返回主菜单
echo.
set /p log_choice=请选择 (0-3): 

if "%log_choice%"=="1" (
    wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker logs -f --tail 100 golf_video_api"
) else if "%log_choice%"=="2" (
    wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker logs -f --tail 100 golf_cloudflare_tunnel"
) else if "%log_choice%"=="3" (
    wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && docker-compose -f docker-compose.golf.yml logs -f --tail 100"
) else if "%log_choice%"=="0" (
    goto menu
)
pause
goto menu

:test_service
echo.
echo 正在测试服务...
echo.
wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && ./测试服务.sh"
pause
goto menu

:open_docs
echo.
echo 正在打开本地 API 文档...
start http://localhost:8081/docs
pause
goto menu

:open_config
echo.
echo 正在打开配置文件...
notepad \\wsl.localhost\Ubuntu-22.04\home\huxiaoran\projects\MyVideoDownloader\MyVideoDownloder\.env
pause
goto menu

:end
echo.
echo 感谢使用！
exit /b 0

