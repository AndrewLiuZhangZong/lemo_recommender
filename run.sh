#!/bin/bash

echo "🚀 启动Lemo推荐系统开发环境"

# 检查Poetry是否安装
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry未安装，请先安装: https://python-poetry.org/docs/#installation"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
poetry install

# 检查.env文件
if [ ! -f .env ]; then
    echo "📝 创建.env文件..."
    cp .env.example .env
fi

# 启动数据库服务
echo "🐳 启动MongoDB服务..."
echo "   注意：使用本地已有的Redis和Kafka服务"
docker-compose up -d mongodb

# 等待服务就绪
echo "⏳ 等待数据库服务启动..."
sleep 10

# 启动应用
echo "🚀 启动FastAPI应用..."
poetry run python app/main.py

