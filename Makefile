.PHONY: help build up down logs test clean format lint

help:
	@echo "BrainCell Development Commands"
	@echo "=============================="
	@echo "make build          - Build Docker images"
	@echo "make up             - Start all services"
	@echo "make down           - Stop all services"
	@echo "make logs           - View application logs"
	@echo "make test           - Run test suite"
	@echo "make format         - Format code with black"
	@echo "make lint           - Lint code with ruff"
	@echo "make clean          - Clean up temporary files"
	@echo "make psql           - Connect to PostgreSQL"
	@echo "make redis          - Connect to Redis CLI"
	@echo "make migrate        - Run database migrations"
	@echo "make seed           - Seed database with sample data"

build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services starting... Waiting for health checks..."
	@sleep 5
	curl -s http://localhost:8000/health | python3 -m json.tool
	@echo "\nAPI running at http://localhost:8000"
	@echo "Swagger docs at http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f braincell-api

test:
	docker-compose exec braincell-api pytest tests/ -v

test-api:
	python3 test_api.py

format:
	black src/

lint:
	ruff check src/

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".egg-info" -delete

psql:
	docker-compose exec postgres psql -U braincell -d braincell

redis:
	docker-compose exec redis redis-cli

ps:
	docker-compose ps

restart:
	docker-compose restart

reset:
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d

deps:
	pip install -r requirements.txt

dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

shell:
	docker-compose exec braincell-api /bin/bash
