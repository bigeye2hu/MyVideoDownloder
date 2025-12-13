@echo off
chcp 65001 >nul

echo ========================================
echo 测试高尔夫视频下载 API
echo ========================================
echo.

cd /d "%~dp0"

echo 1. 测试本地访问...
echo.
curl -f http://localhost:8081/docs >nul 2>&1
if errorlevel 1 (
    echo ❌ 本地服务未响应
    echo    请检查服务是否正在运行
) else (
    echo ✅ 本地服务正常: http://localhost:8081/docs
)

echo.
echo 2. 测试 API 端点...
echo.

REM 测试混合解析接口
echo 测试视频解析接口...
curl -X POST http://localhost:8081/api/hybrid/video_data ^
     -H "Content-Type: application/json" ^
     -d "{\"url\":\"test\"}" ^
     -w "\nHTTP 状态码: %%{http_code}\n"

echo.
echo 3. 查看服务状态...
echo.
wsl docker-compose -f docker-compose.cloudflare.yml ps

echo.
echo ========================================
echo 测试完成
echo ========================================
echo.

pause

