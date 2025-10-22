.PHONY: help install dev start stop clean test lint format docker-build docker-up docker-down init-db

help:
	@echo "Lemo Recommender - 可用命令:"
	@echo ""
	@echo "  make install      - 安装依赖"
	@echo "  make dev          - 启动开发环境"
	@echo "  make start        - 启动应用"
	@echo "  make stop         - 停止所有服务"
	@echo "  make clean        - 清理临时文件"
	@echo "  make test         - 运行测试"
	@echo "  make lint         - 代码检查"
	@echo "  make format       - 代码格式化"
	@echo "  make docker-build - 构建Docker镜像"
	@echo "  make docker-up    - 启动Docker服务"
	@echo "  make docker-down  - 停止Docker服务"
	@echo "  make init-db      - 初始化数据库"
	@echo ""

install:
	@echo "📦 安装依赖..."
	poetry install

dev:
	@echo "🚀 启动开发环境..."
	@echo "1️⃣  启动MongoDB..."
	docker-compose up -d mongodb
	@echo "2️⃣  等待MongoDB就绪..."
	@sleep 5
	@echo "3️⃣  初始化数据库..."
	@make init-db
	@echo "4️⃣  启动应用..."
	@make start

start:
	@echo "🚀 启动应用..."
	poetry run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

stop:
	@echo "🛑 停止所有服务..."
	docker-compose down

clean:
	@echo "🧹 清理临时文件..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov dist build

test:
	@echo "🧪 运行测试..."
	poetry run pytest tests/ -v

lint:
	@echo "🔍 代码检查..."
	poetry run ruff check app/ tests/
	poetry run mypy app/

format:
	@echo "✨ 代码格式化..."
	poetry run ruff format app/ tests/
	poetry run ruff check --fix app/ tests/

docker-build:
	@echo "🐳 构建Docker镜像..."
	docker build -t lemo-recommender:latest .

docker-up:
	@echo "🐳 启动Docker服务..."
	docker-compose up -d

docker-down:
	@echo "🐳 停止Docker服务..."
	docker-compose down

init-db:
	@echo "📚 初始化数据库..."
	poetry run python scripts/init_db.py

# 快速开始
quick-start: install dev
	@echo "✅ 开发环境已就绪!"
	@echo "📖 访问 http://localhost:8080/api/v1/docs 查看API文档"

