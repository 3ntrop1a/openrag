#!/bin/bash

# OpenRAG Test Script
# Teste l'installation et le fonctionnement du système

set -e

echo "🧪 OpenRAG Test Suite"
echo "===================="
echo

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Counters
TESTS_PASSED=0
TESTS_FAILED=0

# Functions
test_pass() {
    echo -e "${GREEN}✓ PASS${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}✗ FAIL${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

# Test 1: Check if services are running
echo "Test 1: Services en cours d'exécution"
if docker compose ps | grep -q "Up"; then
    test_pass "Au moins un service est en cours d'exécution"
else
    test_fail "Aucun service n'est en cours d'exécution"
fi
echo

# Test 2: API Health Check
echo "Test 2: API Health Check"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$response" -eq 200 ]; then
    test_pass "API Health Check réussi (HTTP 200)"
else
    test_fail "API Health Check échoué (HTTP $response)"
fi
echo

# Test 3: API Root Endpoint
echo "Test 3: API Root Endpoint"
response=$(curl -s http://localhost:8000/)
if echo "$response" | grep -q "OpenRAG"; then
    test_pass "API Root retourne une réponse valide"
else
    test_fail "API Root ne répond pas correctement"
fi
echo

# Test 4: Embedding Service
echo "Test 4: Embedding Service Health"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8002/health)
if [ "$response" -eq 200 ]; then
    test_pass "Embedding Service accessible"
else
    test_fail "Embedding Service inaccessible (HTTP $response)"
fi
echo

# Test 5: MinIO
echo "Test 5: MinIO Health"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live)
if [ "$response" -eq 200 ]; then
    test_pass "MinIO opérationnel"
else
    test_fail "MinIO non accessible"
fi
echo

# Test 6: Qdrant
echo "Test 6: Qdrant Health"
response=$(curl -s http://localhost:6333/health)
if echo "$response" | grep -q "ok\|healthy"; then
    test_pass "Qdrant opérationnel"
else
    test_fail "Qdrant non accessible"
fi
echo

# Test 7: Upload a test document
echo "Test 7: Upload de document"
echo "Test document for OpenRAG" > /tmp/test_openrag.txt
response=$(curl -s -w "%{http_code}" -o /tmp/upload_response.json \
    -X POST http://localhost:8000/documents/upload \
    -F "file=@/tmp/test_openrag.txt" \
    -F "collection_id=test")

if [ "$response" -eq 200 ]; then
    doc_id=$(cat /tmp/upload_response.json | grep -o '"document_id":"[^"]*' | cut -d'"' -f4)
    test_pass "Document uploadé avec succès (ID: ${doc_id:0:8}...)"
else
    test_fail "Échec de l'upload de document (HTTP $response)"
    doc_id=""
fi
echo

# Test 8: Wait for processing
if [ -n "$doc_id" ]; then
    echo "Test 8: Traitement du document"
    max_attempts=15
    attempt=0
    processed=false
    
    while [ $attempt -lt $max_attempts ]; do
        sleep 2
        status=$(curl -s "http://localhost:8000/documents/$doc_id" | grep -o '"status":"[^"]*' | cut -d'"' -f4)
        
        if [ "$status" = "processed" ]; then
            processed=true
            break
        fi
        
        attempt=$((attempt + 1))
    done
    
    if [ "$processed" = true ]; then
        test_pass "Document traité avec succès"
    else
        test_fail "Timeout du traitement du document (status: $status)"
    fi
    echo
    
    # Test 9: Query the system
    if [ "$processed" = true ]; then
        echo "Test 9: Requête au système"
        response=$(curl -s -w "%{http_code}" -o /tmp/query_response.json \
            -X POST http://localhost:8000/query \
            -H "Content-Type: application/json" \
            -d '{"query": "What is this document about?", "use_llm": false}')
        
        if [ "$response" -eq 200 ]; then
            sources=$(cat /tmp/query_response.json | grep -o '"sources":\[[^]]*\]' || echo "")
            if [ -n "$sources" ] && [ "$sources" != '"sources":[]' ]; then
                test_pass "Requête exécutée et sources trouvées"
            else
                test_fail "Requête exécutée mais aucune source trouvée"
            fi
        else
            test_fail "Échec de la requête (HTTP $response)"
        fi
        echo
    fi
    
    # Test 10: LLM Query (if enabled)
    echo "Test 10: Requête avec LLM"
    LLM_PROVIDER=$(grep "^LLM_PROVIDER=" .env | cut -d '=' -f2)
    
    if [ -n "$LLM_PROVIDER" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/llm_response.json \
            -X POST http://localhost:8000/query \
            -H "Content-Type: application/json" \
            -d '{"query": "What is this document about?", "use_llm": true}')
        
        if [ "$response" -eq 200 ]; then
            answer=$(cat /tmp/llm_response.json | grep -o '"answer":"[^"]*' | cut -d'"' -f4)
            if [ -n "$answer" ] && [ "$answer" != "null" ]; then
                test_pass "Requête LLM réussie avec réponse"
            else
                test_fail "Requête LLM sans réponse"
            fi
        else
            test_fail "Échec de la requête LLM (HTTP $response)"
        fi
    else
        echo -e "${YELLOW}⊘ SKIP${NC} LLM non configuré"
    fi
    echo
    
    # Cleanup
    echo "Nettoyage: Suppression du document de test"
    curl -s -X DELETE "http://localhost:8000/documents/$doc_id" > /dev/null
    rm -f /tmp/test_openrag.txt /tmp/upload_response.json /tmp/query_response.json /tmp/llm_response.json
fi

# Summary
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Résumé des tests"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}Tests réussis: $TESTS_PASSED${NC}"
echo -e "${RED}Tests échoués: $TESTS_FAILED${NC}"
TOTAL=$((TESTS_PASSED + TESTS_FAILED))
echo "Total: $TOTAL"
echo

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Tous les tests sont passés !${NC}"
    echo
    exit 0
else
    echo -e "${RED}✗ Certains tests ont échoué${NC}"
    echo
    echo "Conseils de dépannage:"
    echo "  • Vérifiez les logs: docker-compose logs -f"
    echo "  • Redémarrez les services: docker-compose restart"
    echo "  • Vérifiez le fichier .env"
    echo
    exit 1
fi
