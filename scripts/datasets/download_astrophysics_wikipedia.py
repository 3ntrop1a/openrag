#!/usr/bin/env python3
"""
Download French Wikipedia articles about Astrophysics

Usage:
    python3 download_astrophysics_wikipedia.py --limit 500 --output /tmp/astrophysics_fr_500.json
"""

import requests
import json
import time
import argparse
from typing import List, Dict
from pathlib import Path


def download_astrophysics_articles(limit: int = 500, output_file: str = None) -> List[Dict]:
    """
    Download French Wikipedia articles about astrophysics
    
    Args:
        limit: Number of articles to download
        output_file: Output JSON file path
        
    Returns:
        List of articles with title, content, url
    """
    
    print(f"🌌 Downloading {limit} French Wikipedia articles about Astrophysics...")
    
    API_URL = "https://fr.wikipedia.org/w/api.php"
    articles = []
    
    # Catégories astrophysiques à explorer
    categories = [
        "Catégorie:Astrophysique",
        "Catégorie:Étoile",
        "Catégorie:Galaxie",
        "Catégorie:Planète",
        "Catégorie:Cosmologie",
        "Catégorie:Exoplanète",
        "Catégorie:Trou_noir"
    ]
    
    seen_titles = set()
    
    for category in categories:
        if len(articles) >= limit:
            break
            
        print(f"\n📂 Exploring category: {category}")
        
        try:
            # Get articles from category
            params = {
                "action": "query",
                "format": "json",
                "list": "categorymembers",
                "cmtitle": category,
                "cmlimit": min(500, limit),
                "cmnamespace": 0  # Main namespace only
            }
            
            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            members = data.get("query", {}).get("categorymembers", [])
            print(f"  Found {len(members)} articles")
            
            for i, member in enumerate(members):
                if len(articles) >= limit:
                    break
                    
                title = member["title"]
                
                # Skip if already processed
                if title in seen_titles:
                    continue
                
                seen_titles.add(title)
                
                try:
                    # Get full article content
                    content_params = {
                        "action": "query",
                        "format": "json",
                        "titles": title,
                        "prop": "extracts",
                        "explaintext": True,
                        "exlimit": 1
                    }
                    
                    content_response = requests.get(API_URL, params=content_params, timeout=30)
                    content_response.raise_for_status()
                    pages = content_response.json()["query"]["pages"]
                    
                    for page_id, page_data in pages.items():
                        if "extract" in page_data and len(page_data["extract"]) > 200:
                            articles.append({
                                "title": page_data["title"],
                                "content": page_data["extract"],
                                "url": f"https://fr.wikipedia.org/wiki/{page_data['title'].replace(' ', '_')}",
                                "source": "wikipedia_fr",
                                "category": category.replace("Catégorie:", ""),
                                "page_id": page_id,
                                "domain": "astrophysics"
                            })
                            
                            if len(articles) % 50 == 0:
                                print(f"  ✓ Downloaded {len(articles)}/{limit} articles...")
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    print(f"  ⚠️ Error downloading '{title}': {e}")
                    continue
                    
        except Exception as e:
            print(f"  ❌ Error exploring category '{category}': {e}")
            continue
    
    print(f"\n✅ Successfully downloaded {len(articles)} astrophysics articles")
    
    # Save to JSON
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved to {output_file}")
        
        # Stats
        total_chars = sum(len(a["content"]) for a in articles)
        avg_chars = total_chars / len(articles) if articles else 0
        
        # Category breakdown
        categories_count = {}
        for a in articles:
            cat = a["category"]
            categories_count[cat] = categories_count.get(cat, 0) + 1
        
        print(f"\n📊 Statistics:")
        print(f"  - Total articles: {len(articles)}")
        print(f"  - Total characters: {total_chars:,}")
        print(f"  - Average chars per article: {avg_chars:,.0f}")
        print(f"  - Estimated chunks (2000 chars): {total_chars // 2000:,}")
        
        print(f"\n🏷️ Categories:")
        for cat, count in sorted(categories_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {cat}: {count}")
    
    return articles


def main():
    parser = argparse.ArgumentParser(
        description="Download French Wikipedia articles about Astrophysics"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Number of articles to download (default: 500)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/astrophysics_fr_500.json",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    try:
        articles = download_astrophysics_articles(
            limit=args.limit,
            output_file=args.output
        )
        
        print(f"\n🎉 Download complete!")
        print(f"📂 Next step: Import to OpenRAG")
        print(f"   python3 scripts/datasets/import_to_openrag.py {args.output}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
