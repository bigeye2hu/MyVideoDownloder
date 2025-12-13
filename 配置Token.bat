@echo off
chcp 65001 >nul
echo 正在配置 Token...

wsl -d Ubuntu-22.04 bash -c "cd ~/projects/MyVideoDownloader/MyVideoDownloder && echo TUNNEL_TOKEN=eyJhIjoiYjI3MWFkZDVhMTFmNzc1NDJiZTgzY2U3ZGIwMDgxYWQiLCJ0IjoiMmJiOTg4N2MtMjc1Zi00YWJkLWI3ODktZmM4MTdjMTYzMjRmIiwicyI6Ik9EWmtNREUwWW1RdE1tRTFPQzAwTUdFNUxXRTFNemd0WWpVMk1USmtNREUxWWpZNCJ9 > .env && echo TZ=Asia/Shanghai >> .env && echo 配置完成 && cat .env"

echo.
echo ✓ Token 配置完成！
echo.
pause

