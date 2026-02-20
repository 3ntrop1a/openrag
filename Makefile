# Makefile for OpenRAG

.PHONY: help install start stop restart logs clean test status pull build rebuild \
        backup restore monitoring-start monitoring-stop stats update dev prod

# Default target
.DEFAULT_GOAL := help

help: ## Show available commands
	@echo "OpenRAG - Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Initial setup and configuration
	@echo "Installing OpenRAG..."
	@bash scripts/setup.sh

start: ## Start all services
	@echo "Starting services..."
	@docker-compose up -d
	@echo "Services started"
	@make status

stop: ## Stop all services
	@echo "Stopping services..."
	@docker-compose down
	@echo "Services stopped"

restart: ## Restart all services
	@echo "Restarting services..."
	@docker-compose restart
	@echo "Services restarted"

logs: ## Stream logs for all services
	@docker-compose logs -f

logs-%: ## Stream logs for a specific service (e.g. make logs-api)
	@docker-compose logs -f $*

status: ## Show service status and health
	@echo "Service status:"
	@docker-compose ps
	@echo ""
	@echo "Health check:"
	@curl -s http://localhost:8000/health | jq '.' 2>/dev/null || echo "API not reachable"

pull: ## Pull latest images
	@echo "Pulling images..."
	@docker-compose pull

build: ## Build images
	@echo "Building images..."
	@docker-compose build

rebuild: ## Rebuild and restart services
	@make build
	@make restart

clean: ## Remove all containers and volumes (WARNING: destroys data)
	@echo "WARNING: This will destroy all containers and volumes"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "Cleanup done"; \
	else \
		echo "Aborted"; \
	fi

test: ## Run the test suite
	@echo "Running tests..."
	@bash scripts/test.sh

shell-%: ## Open a shell in a container (e.g. make shell-api)
	@docker exec -it openrag-$* /bin/bash

psql: ## Open a PostgreSQL client
	@docker exec -it openrag-postgres psql -U openrag -d openrag_db

redis-cli: ## Open a Redis client
	@docker exec -it openrag-redis redis-cli

ollama: ## List Ollama models
	@docker exec -it openrag-ollama ollama list
	@echo ""
	@echo "To pull a model:"
	@echo "  docker exec -it openrag-ollama ollama pull <model>"

backup: ## Backup the database
	@echo "Backing up database..."
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	docker-compose exec -T postgres pg_dump -U openrag openrag_db > backups/db_$$timestamp.sql; \
	echo "Backup saved: backups/db_$$timestamp.sql"

restore: ## Restore the database from a backup
	@echo "Available backups:"
	@ls -1 backups/db_*.sql 2>/dev/null || echo "No backups found"
	@read -p "Enter backup file path: " backup_file; \
	if [ -f "$$backup_file" ]; then \
		docker-compose exec -T postgres psql -U openrag -d openrag_db < $$backup_file; \
		echo "Database restored"; \
	else \
		echo "File not found"; \
	fi

monitoring-start: ## Start monitoring stack (Prometheus + Grafana)
	@echo "Starting monitoring..."
	@docker-compose --profile monitoring up -d
	@echo "Monitoring started"
	@echo "   Prometheus: http://localhost:9090"
	@echo "   Grafana:    http://localhost:3001 (admin/admin)"

monitoring-stop: ## Stop monitoring stack
	@docker-compose --profile monitoring down

stats: ## Show document and collection statistics
	@echo "Usage statistics:"
	@curl -s http://localhost:8000/documents | jq '{total: (.documents | length), by_status: (.documents | group_by(.status) | map({status: .[0].status, count: length}) | from_entries)}' 2>/dev/null || echo "API not reachable"

update: ## Pull latest changes and restart
	@echo "Updating OpenRAG..."
	@git pull
	@make pull
	@make restart
	@echo "Update complete"

dev: ## Start in development mode (with hot-reload)
	@echo "Starting in development mode..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

prod: ## Start in production mode
	@echo "Starting in production mode..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Aliases
up: start
down: stop
ps: status
tail: logs
