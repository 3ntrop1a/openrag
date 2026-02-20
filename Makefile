# Makefile for OpenRAG

.PHONY: help install start stop restart logs clean test status pull backup restore push-public

# Default target
.DEFAULT_GOAL := help

help: ## Affiche cette aide
	@echo "OpenRAG - Commandes disponibles:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

install: ## Installation et configuration initiale
	@echo "🚀 Installation d'OpenRAG..."
	@bash scripts/setup.sh

start: ## Démarre tous les services
	@echo "▶️  Démarrage des services..."
	@docker-compose up -d
	@echo "✅ Services démarrés"
	@make status

stop: ## Arrête tous les services
	@echo "⏹️  Arrêt des services..."
	@docker-compose down
	@echo "✅ Services arrêtés"

restart: ## Redémarre tous les services
	@echo "🔄 Redémarrage des services..."
	@docker-compose restart
	@echo "✅ Services redémarrés"

logs: ## Affiche les logs de tous les services
	@docker-compose logs -f

logs-%: ## Affiche les logs d'un service spécifique (ex: make logs-api)
	@docker-compose logs -f $*

status: ## Affiche le statut des services
	@echo "📊 Statut des services:"
	@docker-compose ps
	@echo ""
	@echo "🏥 Health checks:"
	@curl -s http://localhost:8000/health | jq '.' 2>/dev/null || echo "API non accessible"

pull: ## Télécharge les dernières images
	@echo "📥 Téléchargement des images..."
	@docker-compose pull

build: ## Reconstruit les images
	@echo "🔨 Construction des images..."
	@docker-compose build

rebuild: ## Reconstruit et redémarre les services
	@make build
	@make restart

clean: ## Supprime tous les conteneurs et volumes (⚠️ SUPPRIME LES DONNÉES)
	@echo "⚠️  ATTENTION: Cette commande va supprimer tous les conteneurs et volumes"
	@read -p "Êtes-vous sûr? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		echo "✅ Nettoyage terminé"; \
	else \
		echo "❌ Annulé"; \
	fi

test: ## Lance la suite de tests
	@echo "🧪 Lancement des tests..."
	@bash scripts/test.sh

shell-%: ## Ouvre un shell dans un conteneur (ex: make shell-api)
	@docker exec -it openrag-$* /bin/bash

psql: ## Ouvre un client PostgreSQL
	@docker exec -it openrag-postgres psql -U openrag -d openrag_db

redis-cli: ## Ouvre un client Redis
	@docker exec -it openrag-redis redis-cli

ollama: ## Ouvre le CLI Ollama
	@docker exec -it openrag-ollama ollama list
	@echo ""
	@echo "Pour télécharger un modèle:"
	@echo "  docker exec -it openrag-ollama ollama pull <model>"

backup: ## Sauvegarde les données
	@echo "💾 Sauvegarde des données..."
	@mkdir -p backups
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	docker-compose exec -T postgres pg_dump -U openrag openrag_db > backups/db_$$timestamp.sql; \
	echo "✅ Base de données sauvegardée: backups/db_$$timestamp.sql"

restore: ## Restaure les données depuis une sauvegarde
	@echo "📥 Restauration des données..."
	@echo "Fichiers de sauvegarde disponibles:"
	@ls -1 backups/db_*.sql 2>/dev/null || echo "Aucune sauvegarde trouvée"
	@read -p "Entrez le nom du fichier: " backup_file; \
	if [ -f "$$backup_file" ]; then \
		docker-compose exec -T postgres psql -U openrag -d openrag_db < $$backup_file; \
		echo "✅ Données restaurées"; \
	else \
		echo "❌ Fichier non trouvé"; \
	fi

monitoring-start: ## Démarre le monitoring (Prometheus + Grafana)
	@echo "📊 Démarrage du monitoring..."
	@docker-compose --profile monitoring up -d
	@echo "✅ Monitoring démarré"
	@echo "   • Prometheus: http://localhost:9090"
	@echo "   • Grafana:    http://localhost:3000 (admin/admin)"

monitoring-stop: ## Arrête le monitoring
	@docker-compose --profile monitoring down

docs: ## Démarre le serveur de documentation
	@echo "📚 Démarrage de la documentation..."
	@cd docs && npx mintlify dev

stats: ## Affiche les statistiques d'utilisation
	@echo "📈 Statistiques d'utilisation:"
	@curl -s http://localhost:8000/documents | jq '{total: (.documents | length), by_status: (.documents | group_by(.status) | map({status: .[0].status, count: length}) | from_entries)}' 2>/dev/null || echo "API non accessible"

env-check: ## Vérifie la configuration
	@echo "⚙️  Vérification de la configuration..."
	@bash scripts/check-requirements.sh || true

update: ## Met à jour le projet
	@echo "🔄 Mise à jour d'OpenRAG..."
	@git pull
	@make pull
	@make restart
	@echo "✅ Mise à jour terminée"

push-public: ## Sync public openrag repo (strips docs/, docs_wte/, guide_openrag.txt)
	@bash scripts/push-public.sh

dev: ## Mode développement (avec hot-reload)
	@echo "🔧 Mode développement..."
	@docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

prod: ## Mode production
	@echo "🚀 Mode production..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Aliases
up: start
down: stop
ps: status
tail: logs
