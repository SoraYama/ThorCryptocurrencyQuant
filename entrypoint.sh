#!/bin/bash

# ThorCryptoCurrency Strategy Library 启动脚本

set -e

echo "=========================================="
echo "ThorCryptoCurrency Strategy Library"
echo "=========================================="

# 检查环境变量
echo "检查环境变量..."
if [ -z "$API_KEY" ] || [ -z "$API_SECRET" ]; then
    echo "错误: 请设置 API_KEY 和 API_SECRET 环境变量"
    exit 1
fi

echo "交易所: ${EXCHANGE:-binance}"
echo "交易对: ${ORDER_SYMBOL:-ETH/USDT}"
echo "API Key: ${API_KEY:0:8}..."

# 等待 MongoDB 启动
echo "等待 MongoDB 启动..."
until python -c "import pymongo; pymongo.MongoClient('${MONGO_URI:-mongodb://mongo:27017/binance}').admin.command('ping')" 2>/dev/null; do
    echo "MongoDB 未就绪，等待 5 秒..."
    sleep 5
done
echo "MongoDB 已就绪"

# 创建日志目录
mkdir -p /app/logs

# 启动策略
echo "启动交易策略..."
exec python src/bitmex_main-xbt.py
