#!/usr/bin/env python3
"""
Import JSON dataset into OpenRAG system

Usage:
    python import_to_openrag.py /tmp/wikipedia_fr_sciences_1000.json
    python import_to_openrag.py /tmp/arxiv_cs_ai_1000.json --api http://localhost:8000
"""

import json
import requests
import time
import argparse
from pathlib import Path
from typing import List, Dict


def import_dataset_to_openrag(dataset_file: str, api_url: str = "http://localhost:8000"):
    """
    Import JSON dataset into OpenRAG
    
    Args:
        dataset_file: Path to JSON file with articles/papers
        api_url: OpenRAG API URL
    """
    
    # Load dataset
    print(f"📂 Loading dataset from {dataset_file}...")
    with open(dataset_file, "r", encoding="utf-8") as f:
        documents = json.load(f)
    
    print(f"📚 Found {len(documents)} documents to import")
    
    # Verify API is accessible
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        response.raise_for_status()
        print(f"✅ API is accessible at {api_url}")
    except Exception as e:
        print(f"❌ Cannot connect to API at {api_url}: {e}")
        print(f"💡 Make sure OpenRAG is running: docker-compose up -d")
        return 1
    
    # Import documents
    print(f"\n📥 Importing documents into OpenRAG...")
    
    success_count = 0
    error_count = 0
    
    for i, doc in enumerate(documents):
        try:
            # Create filename (sanitize)
            source = doc.get("source", "unknown")
            title = doc.get("title", f"document_{i+1}")
            filename = f"{source}_{i+1:05d}_{title[:50]}.txt"
            filename = filename.replace("/", "_").replace("\\", "_").replace(":", "_")
            
            # Create content with metadata
            content_parts = [
                f"Title: {doc['title']}",
                "",
                f"Source: {doc.get('url', 'N/A')}",
                f"Category: {doc.get('category', doc.get('primary_category', 'N/A'))}",
                ""
            ]
            
            # Add authors if available
            if "authors" in doc and doc["authors"]:
                authors = ", ".join(doc["authors"][:5])  # First 5 authors
                if len(doc["authors"]) > 5:
                    authors += f" et al. ({len(doc['authors'])} total)"
                content_parts.append(f"Authors: {authors}")
                content_parts.append("")
            
            # Add published date if available
            if "published" in doc:
                content_parts.append(f"Published: {doc['published']}")
                content_parts.append("")
            
            # Main content
            content_parts.append("Content:")
            content_parts.append(doc["content"])
            
            content = "\n".join(content_parts)
            
            # Upload via API
            files = {"file": (filename, content.encode("utf-8"), "text/plain")}
            
            response = requests.post(
                f"{api_url}/upload",
                files=files,
                timeout=30
            )
            response.raise_for_status()
            
            success_count += 1
            
            if (i + 1) % 100 == 0:
                print(f"  ✓ Imported {i + 1}/{len(documents)} documents ({success_count} success, {error_count} errors)")
            
            # Rate limiting to avoid overwhelming the system
            time.sleep(0.05)
        
        except Exception as e:
            error_count += 1
            if error_count <= 10:  # Only show first 10 errors
                print(f"  ❌ Error importing document {i + 1} ('{doc.get('title', 'N/A')[:50]}'): {e}")
    
    # Summary
    print(f"\n🎉 Import complete!")
    print(f"  ✅ Success: {success_count}/{len(documents)}")
    print(f"  ❌ Errors: {error_count}/{len(documents)}")
    
    if success_count > 0:
        print(f"\n⏳ Documents are being processed in the background...")
        print(f"   Monitor processing: docker-compose logs -f orchestrator")
        print(f"   Check status: curl http://localhost:8000/documents")
        print(f"\n🔍 Estimated processing time: ~{success_count * 2} seconds ({success_count} docs × ~2s/doc)")
        print(f"   For {success_count} documents with 768D embeddings")
    
    return 0 if error_count == 0 else 1


def main():
    parser = argparse.ArgumentParser(
        description="Import JSON dataset into OpenRAG system"
    )
    parser.add_argument(
        "dataset_file",
        type=str,
        help="Path to JSON file with documents"
    )
    parser.add_argument(
        "--api",
        type=str,
        default="http://localhost:8000",
        help="OpenRAG API URL (default: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    # Verify file exists
    if not Path(args.dataset_file).exists():
        print(f"❌ File not found: {args.dataset_file}")
        return 1
    
    try:
        return import_dataset_to_openrag(args.dataset_file, args.api)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
