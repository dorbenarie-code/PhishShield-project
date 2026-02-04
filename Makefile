SHELL := /bin/bash

COMPOSE_FILE := docker/docker-compose.yml
COMPOSE := docker compose -f $(COMPOSE_FILE)

.PHONY: help up down restart logs ps build rebuild clean health urls

help:
	@echo "PhishShield - Commands:"
	@echo ""
	@echo "  make up        - Build & start UI+Backend"
	@echo "  make down      - Stop containers"
	@echo "  make restart   - Restart containers"
	@echo "  make logs      - Follow logs"
	@echo "  make ps        - Show container status"
	@echo "  make build     - Build images (cached)"
	@echo "  make rebuild   - Build images (no cache)"
	@echo "  make clean     - Stop + remove volumes"
	@echo "  make health    - Call API /health"
	@echo "  make urls      - Print local URLs"

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

restart:
	$(COMPOSE) down
	$(COMPOSE) up --build

logs:
	$(COMPOSE) logs -f --tail=200

ps:
	$(COMPOSE) ps

build:
	$(COMPOSE) build

rebuild:
	$(COMPOSE) build --no-cache

clean:
	$(COMPOSE) down -v

health:
	@curl -s http://localhost:8000/health || true
	@echo ""

urls:
	@echo "UI:      http://localhost:5173"
	@echo "API:     http://localhost:8000"
	@echo "API Docs http://localhost:8000/docs"

