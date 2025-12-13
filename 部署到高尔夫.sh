#!/bin/bash

# 高尔夫视频下载 API - 一键部署脚本
# 在 WSL Ubuntu 环境下运行，通过 CloudFlare 暴露服务

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}高尔夫视频下载 API 部署脚本${NC}"
echo -e "${GREEN}================================${NC}"

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}未找到 .env 文件，正在创建...${NC}"
    cp .env.example .env
    echo -e "${RED}请编辑 .env 文件，填入你的 TUNNEL_TOKEN${NC}"
    echo -e "${YELLOW}获取 Token: https://one.dash.cloudflare.com/${NC}"
    echo ""
    echo "步骤："
    echo "1. 访问 CloudFlare Zero Trust Dashboard"
    echo "2. 进入 Networks -> Tunnels"
    echo "3. 创建新的 Tunnel 或选择现有的"
    echo "4. 复制 Token 并粘贴到 .env 文件中"
    echo ""
    read -p "配置完成后按回车继续..."
fi

# 检查 TUNNEL_TOKEN
source .env
if [ -z "$TUNNEL_TOKEN" ] || [ "$TUNNEL_TOKEN" = "your_tunnel_token_here" ]; then
    echo -e "${RED}错误: TUNNEL_TOKEN 未设置${NC}"
    echo -e "${YELLOW}请编辑 .env 文件并设置有效的 TUNNEL_TOKEN${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 配置文件检查通过${NC}"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: 未安装 Docker${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker 已安装${NC}"

# 检查 Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}错误: 未安装 Docker Compose${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker Compose 已安装${NC}"

# 创建必要的目录
mkdir -p download logs

echo -e "${GREEN}✓ 目录结构已创建${NC}"

# 停止旧服务
echo -e "${YELLOW}停止旧服务...${NC}"
docker-compose -f docker-compose.golf.yml down 2>/dev/null || true

# 构建并启动服务
echo -e "${GREEN}构建并启动服务...${NC}"
docker-compose -f docker-compose.golf.yml up -d --build

# 等待服务启动
echo -e "${YELLOW}等待服务启动...${NC}"
sleep 10

# 检查服务状态
echo -e "${GREEN}检查服务状态...${NC}"
docker-compose -f docker-compose.golf.yml ps

# 检查 API 健康状态
echo -e "${YELLOW}检查 API 健康状态...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8081/docs > /dev/null; then
        echo -e "${GREEN}✓ API 服务运行正常${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}警告: API 服务可能未正常启动${NC}"
        echo -e "${YELLOW}查看日志: docker logs golf_video_api${NC}"
    fi
    sleep 2
done

# 检查 CloudFlare Tunnel 状态
echo -e "${YELLOW}检查 CloudFlare Tunnel 状态...${NC}"
sleep 5
if docker logs golf_cloudflare_tunnel 2>&1 | grep -q "Registered"; then
    echo -e "${GREEN}✓ CloudFlare Tunnel 已连接${NC}"
else
    echo -e "${YELLOW}CloudFlare Tunnel 正在连接...${NC}"
    echo -e "${YELLOW}查看日志: docker logs golf_cloudflare_tunnel${NC}"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "本地访问："
echo "  API 文档: http://localhost:8081/docs"
echo ""
echo "公网访问（需在 CloudFlare 配置）："
echo "  https://你的域名/docs"
echo ""
echo "管理命令："
echo "  查看状态: docker-compose -f docker-compose.golf.yml ps"
echo "  查看日志: docker-compose -f docker-compose.golf.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.golf.yml down"
echo "  重启服务: docker-compose -f docker-compose.golf.yml restart"
echo ""
echo "下一步："
echo "1. 访问 CloudFlare Tunnel Dashboard"
echo "2. 配置 Public Hostname："
echo "   - Service: http://golf_video_api:80"
echo "   - Domain: 你的域名"
echo "3. 在高尔夫 App 中配置 API 地址"
echo ""

