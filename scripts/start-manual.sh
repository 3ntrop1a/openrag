#!/bin/bash

# Manual startup script for OpenRAG
# Run this script to start all services

echo "🚀 Starting OpenRAG..."
echo "======================"
echo

# Make sure we are in the right directory
cd /home/adminrag/openrag

# Check that Docker is running
echo "Step 1/6: Checking Docker..."
if sudo docker info > /dev/null 2>&1; then
    echo "✅ Docker is running"
else
    echo "❌ Docker is not running. Starting..."
    sudo systemctl start docker
    sleep 3
fi

# Pull images
echo
echo "Step 2/6: Pulling Docker images..."
echo "(This may take 5-10 minutes depending on your connection)"
sudo docker-compose pull

# Start infrastructure services
echo
echo "Step 3/6: Starting infrastructure (PostgreSQL, Redis, MinIO, Qdrant)..."
sudo docker-compose up -d postgres redis minio qdrant

# Wait for infrastructure to be ready
echo
echo "Step 4/6: Waiting for infrastructure to start (30 seconds)..."
sleep 30

# Start Ollama
echo
echo "Step 5/6: Starting Ollama (LLM server)..."
sudo docker-compose up -d ollama

# Wait for Ollama to be ready
sleep 10

# Start application services
echo
echo "Step 6/6: Starting application services..."
sudo docker-compose up -d embedding-service orchestrator api

# Wait for full startup
echo
echo "⏳ Waiting for full startup (30 seconds)..."
sleep 30

# Show service status
echo
echo "📊 Service status:"
sudo docker-compose ps

# Check API health
echo
echo "🏥 Testing the API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API is up at http://localhost:8000"
else
    echo "⚠️  API not ready yet. Wait 1-2 minutes and test:"
    echo "   curl http://localhost:8000/health"
fi

echo
echo "✅ Startup complete!"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 OpenRAG is ready!"
echo
echo "📍 Service URLs:"
echo "   • Chat UI:            http://localhost:3000"
echo "   • API Documentation:  http://localhost:8000/docs"
echo "   • MinIO Console:      http://localhost:9001 (admin/admin123456)"
echo "   • Qdrant Dashboard:   http://localhost:6333/dashboard"
echo
echo "📝 Next steps:"
echo
echo "1. Pull the LLM model (Ollama):"
echo "   sudo docker exec -it openrag-ollama ollama pull llama3.1:8b"
echo
echo "2. Upload a test document:"
echo "   curl -X POST http://localhost:8000/documents/upload \\"
echo "        -F \"file=@your_document.pdf\""
echo
echo "3. Ask a question:"
echo "   curl -X POST http://localhost:8000/query \\"
echo "        -H \"Content-Type: application/json\" \\"
echo "        -d '{\"query\": \"Your question here\"}'"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "💡 Useful commands:"
echo "   • Stream logs:   sudo docker-compose logs -f"
echo "   • Stop:          sudo docker-compose down"
echo "   • Restart:       sudo docker-compose restart"
echo "   • Status:        sudo docker-compose ps"
echo

echo "🚀 Démarrage d'OpenRAG..."
echo "========================"
echo

# S'assurer que nous sommes dans le bon répertoire
cd /home/adminrag/openrag

# Vérifier que Docker fonctionne
echo "Étape 1/6: Vérification de Docker..."
if sudo docker info > /dev/null 2>&1; then
    echo "✅ Docker est actif"
else
    echo "❌ Docker n'est pas actif. Démarrage..."
    sudo systemctl start docker
    sleep 3
fi

# Télécharger les images
echo
echo "Étape 2/6: Téléchargement des images Docker..."
echo "(Cela peut prendre 5-10 minutes selon votre connexion)"
sudo docker-compose pull

# Démarrer les services d'infrastructure
echo
echo " Étape 3/6: Démarrage de l'infrastructure (PostgreSQL, Redis, MinIO, Qdrant)..."
sudo docker-compose up -d postgres redis minio qdrant

# Attendre que l'infrastructure soit prête
echo
echo "Étape 4/6: Attente du démarrage de l'infrastructure (30 secondes)..."
sleep 30

# Démarrer Ollama
echo
echo "Étape 5/6: Démarrage d'Ollama (serveur LLM)..."
sudo docker-compose up -d ollama

# Attendre qu'Ollama soit prêt
sleep 10

# Démarrer les services applicatifs
echo
echo "Étape 6/6: Démarrage des services applicatifs..."
sudo docker-compose up -d embedding-service orchestrator api

# Attendre le démarrage complet
echo
echo "⏳ Attente du démarrage complet (30 secondes)..."
sleep 30

# Vérifier le statut
echo
echo "📊 Statut des services:"
sudo docker-compose ps

# Vérifier la santé de l'API
echo
echo "🏥 Test de l'API..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API opérationnelle sur http://localhost:8000"
else
    echo "⚠️  API pas encore prête. Attendez 1-2 minutes et testez:"
    echo "   curl http://localhost:8000/health"
fi

echo
echo "✅ Démarrage terminé !"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 OpenRAG est prêt !"
echo
echo "📍 Accès aux services:"
echo "   • API Documentation:  http://localhost:8000/docs"
echo "   • MinIO Console:      http://localhost:9001 (admin/admin123456)"
echo "   • Qdrant Dashboard:   http://localhost:6333/dashboard"
echo
echo "📝 Prochaines étapes:"
echo
echo "1. Télécharger le modèle LLM (Ollama):"
echo "   sudo docker exec -it openrag-ollama ollama pull llama3.1:8b"
echo
echo "2. Uploader un document de test:"
echo "   curl -X POST http://localhost:8000/documents/upload \\"
echo "        -F \"file=@votre_document.pdf\""
echo
echo "3. Poser une question:"
echo "   curl -X POST http://localhost:8000/query \\"
echo "        -H \"Content-Type: application/json\" \\"
echo "        -d '{\"query\": \"Votre question ici\"}'"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "💡 Commandes utiles:"
echo "   • Voir les logs:        sudo docker-compose logs -f"
echo "   • Arrêter les services: sudo docker-compose down"
echo "   • Redémarrer:           sudo docker-compose restart"
echo "   • Status:               sudo docker-compose ps"
echo
