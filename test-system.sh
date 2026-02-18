#!/bin/bash

# Script de test rapide du système OpenRAG
# Usage: ./test-system.sh

echo "=================================="
echo "OpenRAG - Test Système Complet"
echo "=================================="
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Services actifs
echo "1. Vérification des services..."
SERVICES=$(sudo docker-compose ps --services | wc -l)
RUNNING=$(sudo docker-compose ps --filter "status=running" -q | wc -l)

if [ "$SERVICES" -eq 10 ] && [ "$RUNNING" -eq 10 ]; then
    echo -e "${GREEN}✓ Tous les services sont actifs (10/10)${NC}"
else
    echo -e "${RED}✗ Problème de services: $RUNNING/$SERVICES actifs${NC}"
fi
echo ""

# Test 2: API Health
echo "2. Test de santé de l'API..."
HEALTH=$(curl -s http://localhost:8000/health | jq -r '.status' 2>/dev/null)

if [ "$HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✓ API opérationnelle${NC}"
else
    echo -e "${RED}✗ API non accessible${NC}"
fi
echo ""

# Test 3: Vecteurs Qdrant
echo "3. Vérification base vectorielle..."
VECTORS=$(curl -s http://localhost:6333/collections/default 2>/dev/null | jq -r '.result.points_count' 2>/dev/null)

if [ ! -z "$VECTORS" ] && [ "$VECTORS" -gt 0 ]; then
    echo -e "${GREEN}✓ $VECTORS vecteurs indexés dans Qdrant${NC}"
else
    echo -e "${YELLOW}⚠ Aucun vecteur trouvé (collection vide ?)${NC}"
fi
echo ""

# Test 4: Documents traités
echo "4. Vérification documents..."
DOCS=$(curl -s http://localhost:8000/documents 2>/dev/null | jq '[.documents[] | select(.status=="processed")] | length' 2>/dev/null)

if [ ! -z "$DOCS" ] && [ "$DOCS" -gt 0 ]; then
    echo -e "${GREEN}✓ $DOCS documents traités${NC}"
else
    echo -e "${YELLOW}⚠ Aucun document traité${NC}"
fi
echo ""

# Test 5: Interface utilisateur
echo "5. Test interface utilisateur..."
USER_UI=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8501 2>/dev/null)

if [ "$USER_UI" = "200" ] || [ "$USER_UI" = "301" ]; then
    echo -e "${GREEN}✓ Interface utilisateur accessible sur http://localhost:8501${NC}"
else
    echo -e "${RED}✗ Interface utilisateur non accessible (code: $USER_UI)${NC}"
fi
echo ""

# Test 6: Panel admin
echo "6. Test panel administration..."
ADMIN_UI=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8502 2>/dev/null)

if [ "$ADMIN_UI" = "200" ] || [ "$ADMIN_UI" = "301" ]; then
    echo -e "${GREEN}✓ Panel admin accessible sur http://localhost:8502${NC}"
else
    echo -e "${RED}✗ Panel admin non accessible (code: $ADMIN_UI)${NC}"
fi
echo ""

# Test 7: Requête de recherche simple
echo "7. Test recherche vectorielle..."
SEARCH_TIME=$(curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Configuration téléphone",
    "collection_id": "default",
    "max_results": 3,
    "use_llm": false
  }' -w "%{time_total}" -o /tmp/search_result.json 2>/dev/null)

SEARCH_SOURCES=$(jq -r '.sources | length' /tmp/search_result.json 2>/dev/null)

if [ ! -z "$SEARCH_SOURCES" ] && [ "$SEARCH_SOURCES" -gt 0 ]; then
    echo -e "${GREEN}✓ Recherche fonctionnelle: $SEARCH_SOURCES sources trouvées en ${SEARCH_TIME}s${NC}"
else
    echo -e "${RED}✗ Échec de la recherche${NC}"
fi
echo ""

# Test 8: Requête LLM (optionnel, long)
echo "8. Test génération LLM (peut prendre 5-60s)..."
echo "   Requête: 'Qu'est-ce que WTE ?'"

START=$(date +%s)
LLM_RESPONSE=$(curl -s -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Qu'\''est-ce que WTE ?",
    "collection_id": "default",
    "max_results": 3,
    "use_llm": true
  }' | jq -r '.answer' 2>/dev/null)
END=$(date +%s)
DURATION=$((END - START))

if [ ! -z "$LLM_RESPONSE" ] && [ "$LLM_RESPONSE" != "null" ]; then
    # Vérifier qu'il n'y a pas de mention "Document"
    if echo "$LLM_RESPONSE" | grep -qi "Document [0-9]"; then
        echo -e "${YELLOW}⚠ LLM répond mais mentionne des numéros de documents${NC}"
        echo "   Réponse: ${LLM_RESPONSE:0:100}..."
    else
        echo -e "${GREEN}✓ LLM opérationnel (${DURATION}s)${NC}"
        echo "   Réponse: ${LLM_RESPONSE:0:150}..."
    fi
else
    echo -e "${RED}✗ LLM non fonctionnel${NC}"
fi
echo ""

# Résumé
echo "=================================="
echo "Résumé"
echo "=================================="
echo ""
echo "Accès rapide:"
echo "  • Chat utilisateur:  http://localhost:8501"
echo "  • Panel admin:       http://localhost:8502"
echo "  • API Swagger:       http://localhost:8000/docs"
echo "  • Qdrant Dashboard:  http://localhost:6333/dashboard"
echo "  • MinIO Console:     http://localhost:9001 (admin/admin123456)"
echo ""
echo "Documentation:"
echo "  • README.md: Présentation complète"
echo "  • RAPPORT_AMELIORATIONS.md: Détails des améliorations"
echo "  • RECAPITULATIF_FINAL.md: État final du système"
echo "  • docs/: Documentation Mintlify complète"
echo ""
echo "Commandes utiles:"
echo "  • Logs en direct:    sudo docker-compose logs -f"
echo "  • Redémarrer:        sudo docker-compose restart"
echo "  • Arrêter:           sudo docker-compose down"
echo "  • Relancer:          sudo docker-compose up -d"
echo ""
echo "=================================="
echo -e "${GREEN}Test système terminé ✓${NC}"
echo "=================================="
