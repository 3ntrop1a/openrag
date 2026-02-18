#!/bin/bash

# Script d'upload des documentations WTE/Cisco dans OpenRAG

DOCS_DIR="docs_wte"
API_URL="http://localhost:8000"
COLLECTION_ID="wte_cisco"

echo "=========================================="
echo "Upload des documentations WTE/Cisco"
echo "=========================================="
echo ""

# Compteurs
TOTAL=0
SUCCESS=0
FAILED=0

# Upload de chaque fichier PDF
for file in "$DOCS_DIR"/*.pdf; do
    if [ -f "$file" ]; then
        TOTAL=$((TOTAL + 1))
        filename=$(basename "$file")
        echo "[$TOTAL] Upload: $filename"
        
        # Upload du fichier avec metadata
        response=$(curl -s -X POST "$API_URL/documents/upload" \
            -F "file=@$file" \
            -F "collection_id=$COLLECTION_ID" \
            -F "metadata={\"source\":\"WTE Orange\",\"type\":\"documentation\",\"category\":\"cisco\"}")
        
        # Vérification du succès
        if echo "$response" | grep -q "document_id"; then
            doc_id=$(echo "$response" | jq -r '.document_id' 2>/dev/null || echo "N/A")
            echo "   ✅ Uploadé - ID: $doc_id"
            SUCCESS=$((SUCCESS + 1))
        else
            echo "   ❌ Erreur: $response"
            FAILED=$((FAILED + 1))
        fi
        
        # Petite pause pour éviter de surcharger
        sleep 0.5
    fi
done

echo ""
echo "=========================================="
echo "Résumé"
echo "=========================================="
echo "Total:   $TOTAL fichiers"
echo "Succès:  $SUCCESS fichiers"
echo "Échecs:  $FAILED fichiers"
echo ""

if [ $SUCCESS -gt 0 ]; then
    echo "✅ Upload terminé !"
    echo ""
    echo "Pour vérifier le statut du traitement:"
    echo "  curl http://localhost:8000/documents | jq '.documents[] | {filename, status, chunks_count}'"
    echo ""
    echo "Pour interroger les documents WTE:"
    echo "  curl -X POST http://localhost:8000/query \\"
    echo "    -H 'Content-Type: application/json' \\"
    echo "    -d '{\"query\": \"Comment configurer un standard automatique ?\", \"collection_id\": \"$COLLECTION_ID\", \"use_llm\": true}' | jq '.'"
fi
