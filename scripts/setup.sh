#!/bin/bash

# OpenRAG Setup Script
# Initialise et configure l'environnement OpenRAG

set -e

echo "🚀 OpenRAG Setup Script"
echo "======================="
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check prerequisites
echo "📋 Vérification des prérequis..."
echo

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
    print_success "Docker installé (version $DOCKER_VERSION)"
else
    print_error "Docker n'est pas installé"
    echo "Installez Docker depuis: https://www.docker.com/get-started"
    exit 1
fi

# Check Docker Compose
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short)
    print_success "Docker Compose installé (version $COMPOSE_VERSION)"
else
    print_error "Docker Compose n'est pas installé"
    echo "Installez Docker Compose depuis: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    print_error "Le daemon Docker ne fonctionne pas"
    echo "Démarrez Docker et relancez ce script"
    exit 1
fi

print_success "Docker daemon en cours d'exécution"
echo

# Setup environment file
echo "⚙️  Configuration de l'environnement..."
echo

if [ -f .env ]; then
    print_info "Le fichier .env existe déjà"
    read -p "Voulez-vous le remplacer? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        print_success "Fichier .env créé depuis .env.example"
    else
        print_info "Fichier .env conservé"
    fi
else
    cp .env.example .env
    print_success "Fichier .env créé depuis .env.example"
fi
echo

# Ask for LLM configuration
echo "🤖 Configuration du LLM"
echo

PS3="Choisissez votre fournisseur LLM: "
options=("Ollama (local)" "OpenAI" "Anthropic Claude" "Garder la configuration actuelle")
select opt in "${options[@]}"
do
    case $opt in
        "Ollama (local)")
            sed -i.bak 's/^LLM_PROVIDER=.*/LLM_PROVIDER=ollama/' .env
            print_success "Configuration: Ollama (local)"
            
            echo
            echo "Modèles Ollama disponibles:"
            echo "1) llama3.1:8b (recommandé, ~4.7GB)"
            echo "2) phi3:mini (léger, ~2.3GB)"
            echo "3) gemma:7b (~4.8GB)"
            echo "4) mistral:7b (~4.1GB)"
            read -p "Entrez le modèle souhaité [llama3.1:8b]: " model
            model=${model:-llama3.1:8b}
            sed -i.bak "s/^LLM_MODEL=.*/LLM_MODEL=$model/" .env
            print_success "Modèle configuré: $model"
            break
            ;;
        "OpenAI")
            sed -i.bak 's/^LLM_PROVIDER=.*/LLM_PROVIDER=openai/' .env
            read -p "Entrez votre clé API OpenAI: " api_key
            sed -i.bak "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=$api_key/" .env
            
            read -p "Modèle OpenAI [gpt-4-turbo]: " model
            model=${model:-gpt-4-turbo}
            sed -i.bak "s/^LLM_MODEL=.*/LLM_MODEL=$model/" .env
            print_success "Configuration OpenAI terminée"
            break
            ;;
        "Anthropic Claude")
            sed -i.bak 's/^LLM_PROVIDER=.*/LLM_PROVIDER=anthropic/' .env
            read -p "Entrez votre clé API Anthropic: " api_key
            sed -i.bak "s/^ANTHROPIC_API_KEY=.*/ANTHROPIC_API_KEY=$api_key/" .env
            
            read -p "Modèle Claude [claude-3-sonnet-20240229]: " model
            model=${model:-claude-3-sonnet-20240229}
            sed -i.bak "s/^LLM_MODEL=.*/LLM_MODEL=$model/" .env
            print_success "Configuration Anthropic terminée"
            break
            ;;
        "Garder la configuration actuelle")
            print_info "Configuration LLM inchangée"
            break
            ;;
        *) echo "Option invalide $REPLY";;
    esac
done

# Cleanup backup files
rm -f .env.bak

echo
echo "📦 Téléchargement et démarrage des services..."
echo

# Pull images
docker compose pull

# Start services
docker compose up -d

echo
echo "⏳ Attente du démarrage des services..."
sleep 10

# Check services health
echo
echo "🏥 Vérification de la santé des services..."
echo

max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        print_success "API Gateway est opérationnel"
        break
    fi
    
    attempt=$((attempt + 1))
    if [ $attempt -eq $max_attempts ]; then
        print_error "Timeout: API Gateway ne répond pas"
        echo "Vérifiez les logs: docker-compose logs api"
        exit 1
    fi
    
    echo -n "."
    sleep 2
done

echo

# Download Ollama model if needed
if grep -q "LLM_PROVIDER=ollama" .env; then
    echo
    echo "📥 Téléchargement du modèle Ollama..."
    LLM_MODEL=$(grep "^LLM_MODEL=" .env | cut -d '=' -f2)
    
    print_info "Téléchargement de $LLM_MODEL (cela peut prendre quelques minutes)..."
    docker exec openrag-ollama ollama pull "$LLM_MODEL"
    
    if [ $? -eq 0 ]; then
        print_success "Modèle $LLM_MODEL téléchargé avec succès"
    else
        print_error "Échec du téléchargement du modèle"
        print_info "Vous pouvez le télécharger manuellement: docker exec -it openrag-ollama ollama pull $LLM_MODEL"
    fi
fi

echo
echo "✅ Installation terminée !"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "🎉 OpenRAG est prêt à l'emploi !"
echo
echo "📍 Accès aux services:"
echo "   • API Documentation:  http://localhost:8000/docs"
echo "   • MinIO Console:      http://localhost:9001 (admin/admin123456)"
echo "   • Qdrant Dashboard:   http://localhost:6333/dashboard"
echo
echo "📚 Prochaines étapes:"
echo "   1. Uploadez vos premiers documents:"
echo "      curl -X POST http://localhost:8000/documents/upload \\"
echo "           -F \"file=@document.pdf\""
echo
echo "   2. Posez une question:"
echo "      curl -X POST http://localhost:8000/query \\"
echo "           -H \"Content-Type: application/json\" \\"
echo "           -d '{\"query\": \"Votre question ici\"}'"
echo
echo "   3. Consultez la documentation complète:"
echo "      cd docs && npx mintlify dev"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "💡 Commandes utiles:"
echo "   • Voir les logs:        docker-compose logs -f"
echo "   • Arrêter les services: docker-compose down"
echo "   • Redémarrer:           docker-compose restart"
echo "   • Status:               docker-compose ps"
echo
echo "🆘 Besoin d'aide? https://docs.openrag.io"
echo
