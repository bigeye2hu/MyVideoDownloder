@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 高尔夫视频下载 API 一键部署
echo ========================================
echo.

cd /d "%~dp0"

REM 检查 Docker Desktop 是否运行
docker ps >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Desktop 未运行！
    echo.
    echo 请先启动 Docker Desktop，然后重新运行此脚本
    pause
    exit /b 1
)

echo ✅ Docker Desktop 运行正常
echo.

REM 检查 .env 文件
if not exist ".env" (
    echo ⚠️  未找到 .env 文件
    echo.
    echo 正在创建 .env 文件...
    copy .env.example .env >nul 2>&1
    echo.
    echo ========================================
    echo 📝 请按以下步骤配置 CloudFlare Tunnel:
    echo ========================================
    echo.
    echo 1. 访问 https://one.dash.cloudflare.com/
    echo.
    echo 2. 进入 Access -^> Tunnels -^> Create a tunnel
    echo.
    echo 3. 创建名为 'golf-video-api' 的 tunnel
    echo.
    echo 4. 复制 Tunnel Token
    echo.
    echo 5. 在 CloudFlare 配置 Public Hostname:
    echo    - Subdomain: golf-video-api ^(或你喜欢的名字^)
    echo    - Domain: 选择你的域名
    echo    - Service: HTTP -^> video_downloader_api:80
    echo.
    echo 6. 打开 .env 文件，将 Token 粘贴进去
    echo.
    echo ========================================
    echo.
    pause
    notepad .env
    echo.
    echo 请保存 .env 文件后，重新运行此脚本
    pause
    exit /b 0
)

REM 检查 TUNNEL_TOKEN 是否已配置
findstr /C:"TUNNEL_TOKEN=你的cloudflare_tunnel_token" .env >nul 2>&1
if not errorlevel 1 (
    echo ❌ 请先在 .env 文件中配置你的 TUNNEL_TOKEN
    echo.
    echo 正在打开 .env 文件...
    notepad .env
    echo.
    echo 请保存后重新运行此脚本
    pause
    exit /b 1
)

echo ✅ 环境变量配置正确
echo.

REM 停止旧服务
echo 📦 停止旧服务...
wsl docker-compose -f docker-compose.cloudflare.yml down 2>nul
echo.

REM 构建并启动服务
echo 🚀 构建并启动服务...
echo 这可能需要几分钟时间...
echo.
wsl docker-compose -f docker-compose.cloudflare.yml up -d --build

echo.
echo ⏳ 等待服务启动...
timeout /t 15 /nobreak >nul

REM 检查服务状态
echo.
echo 📊 服务状态：
wsl docker-compose -f docker-compose.cloudflare.yml ps

echo.
echo ========================================
echo ✅ 部署完成！
echo ========================================
echo.
echo 📝 服务信息：
echo   - 本地访问: http://localhost:8081/docs
echo   - 公网访问: https://你配置的域名/docs
echo.
echo 🔧 管理命令：
echo   查看日志: wsl docker-compose -f docker-compose.cloudflare.yml logs -f
echo   停止服务: wsl docker-compose -f docker-compose.cloudflare.yml down
echo   重启服务: wsl docker-compose -f docker-compose.cloudflare.yml restart
echo.
echo 📱 在高尔夫 App 中使用：
echo   API 基础 URL: https://你配置的域名
echo   视频解析接口: POST /api/hybrid/video_data
echo.
echo 💡 提示：服务会在 Docker Desktop 启动时自动运行
echo.

pause

