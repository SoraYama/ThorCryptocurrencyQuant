#!/bin/bash

# ThorCryptoCurrency Strategy Library 部署脚本
# 适用于阿里云 Ubuntu 系统

set -e

echo "=========================================="
echo "ThorCryptoCurrency Strategy Library"
echo "Docker 容器化部署脚本"
echo "=========================================="

# 检查是否为 root 用户
if [ "$EUID" -eq 0 ]; then
    echo "请不要使用 root 用户运行此脚本"
    exit 1
fi

# 检查操作系统
if [ ! -f /etc/os-release ]; then
    echo "无法检测操作系统版本"
    exit 1
fi

. /etc/os-release

if [ "$ID" != "ubuntu" ] && [ "$ID" != "debian" ]; then
    echo "此脚本仅支持 Ubuntu/Debian 系统"
    exit 1
fi

echo "检测到操作系统: $PRETTY_NAME"

# 更新系统包
echo "更新系统包..."
sudo apt update

# 安装 Docker
echo "安装 Docker..."
if ! command -v docker &> /dev/null; then
    sudo apt install -y docker.io
    sudo systemctl start docker
    sudo systemctl enable docker
    echo "Docker 安装完成"
else
    echo "Docker 已安装"
fi

# 安装 Docker Compose
echo "安装 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo apt install -y docker-compose
    echo "Docker Compose 安装完成"
else
    echo "Docker Compose 已安装"
fi

# 将当前用户添加到 docker 组
echo "配置用户权限..."
sudo usermod -aG docker $USER
echo "已将用户 $USER 添加到 docker 组"

# 创建数据目录
echo "创建数据目录..."
sudo mkdir -p /data/docker/ThorCQ/mongo
sudo chown -R $USER:$USER /data/docker/ThorCQ
echo "数据目录创建完成: /data/docker/ThorCQ"

# 检查项目文件
echo "检查项目文件..."
if [ ! -f "docker-compose.yml" ]; then
    echo "错误: 未找到 docker-compose.yml 文件"
    echo "请确保在项目根目录下运行此脚本"
    exit 1
fi

if [ ! -f "env.example" ]; then
    echo "错误: 未找到 env.example 文件"
    exit 1
fi

# 配置环境变量
echo "配置环境变量..."
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "已创建 .env 文件，请编辑并填入您的 API 密钥"
    echo "编辑命令: nano .env"
else
    echo ".env 文件已存在"
fi

# 检查 API 密钥配置
echo "检查 API 密钥配置..."
if grep -q "your_.*_api_key_here" .env; then
    echo "警告: 请编辑 .env 文件并填入您的真实 API 密钥"
    echo "编辑命令: nano .env"
    read -p "是否现在编辑 .env 文件? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        nano .env
    fi
fi

# 构建并启动服务
echo "构建并启动服务..."
docker-compose up -d --build

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

# 显示日志
echo "显示应用日志..."
docker-compose logs --tail=20 app

echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo "常用命令："
echo "  查看服务状态: docker-compose ps"
echo "  查看日志: docker-compose logs -f app"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "  查看数据库: docker-compose exec mongo mongosh"
echo "=========================================="
echo "MongoDB 端口: 7399"
echo "数据目录: /data/docker/ThorCQ/mongo"
echo "=========================================="
