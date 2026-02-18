#!/usr/bin/env python3
"""
Download French Wikipedia articles from Sciences category

Usage:
    python download_wikipedia.py --limit 1000 --output /tmp/wikipedia_fr_sciences.json
"""

import requests
import json
import time
import argparse
from typing import List, Dict
from pathlib import Path


def download_wikipedia_fr_sciences(limit: int = 1000, output_file: str = None) -> List[Dict]:
    """
    Download French Wikipedia articles from Sciences category
    
    Args:
        limit: Number of articles to download
        output_file: Output JSON file path
        
    Returns:
        List of articles with title, content, url
    """
    
    print(f"📥 Downloading {limit} French Wikipedia articles from Sciences category...")
    
    # Wikipedia API endpoint
    API_URL = "https://fr.wikipedia.org/w/api.php"
    
    articles = []
    
    # Step 1: Get list of articles in Sciences category
    print("🔍 Step 1: Getting list of articles in Sciences category...")
    
    params = {
        "action": "query",
        "format": "json",
        "list": "categorymembers",
        "cmtitle": "Catégorie:Sciences",
        "cmlimit": min(500, limit),  # API max is 500
        "cmnamespace": 0  # Main namespace only (articles)
    }
    
    response = requests.get(API_URL, params=params)
    response.raise_for_status()
    data = response.json()
    
    members = data.get("query", {}).get("categorymembers", [])
    print(f"✅ Found {len(members)} articles in category")
    
    # Step 2: Download full content for each article
    print(f"📖 Step 2: Downloading full content for articles...")
    
    for i, member in enumerate(members[:limit]):
        try:
            # Get full article content
            content_params = {
                "action": "query",
                "format": "json",
                "titles": member["title"],
                "prop": "extracts",
                "explaintext": True,  # Plain text, no HTML
                "exlimit": 1
            }
            
            content_response = requests.get(API_URL, params=content_params)
            content_response.raise_for_status()
            pages = content_response.json()["query"]["pages"]
            
            for page_id, page_data in pages.items():
                if "extract" in page_data and len(page_data["extract"]) > 100:
                    articles.append({
                        "title": page_data["title"],
                        "content": page_data["extract"],
                        "url": f"https://fr.wikipedia.org/wiki/{page_data['title'].replace(' ', '_')}",
                        "source": "wikipedia_fr",
                        "category": "Sciences",
                        "page_id": page_id
                    })
                    
                    if (i + 1) % 50 == 0:
                        print(f"  ✓ Downloaded {i + 1}/{limit} articles...")
            
            # Rate limiting: be nice to Wikipedia API
            time.sleep(0.1)
            
        except Exception as e:
            print(f"  ⚠️ Error downloading '{member['title']}': {e}")
            continue
    
    print(f"\n✅ Successfully downloaded {len(articles)} articles")
    
    # Save to JSON if output file specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved to {output_file}")
        
        # Stats
        total_chars = sum(len(a["content"]) for a in articles)
        avg_chars = total_chars / len(articles) if articles else 0
        print(f"\n📊 Statistics:")
        print(f"  - Total articles: {len(articles)}")
        print(f"  - Total characters: {total_chars:,}")
        print(f"  - Average chars per article: {avg_chars:,.0f}")
        print(f"  - Estimated chunks (2000 chars): {total_chars // 2000:,}")
    
    return articles


def main():
    parser = argparse.ArgumentParser(
        description="Download French Wikipedia articles from Sciences category"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Number of articles to download (default: 1000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/wikipedia_fr_sciences_1000.json",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    try:
        articles = download_wikipedia_fr_sciences(
            limit=args.limit,
            output_file=args.output
        )
        
        print(f"\n🎉 Download complete!")
        print(f"📂 Next step: Import to OpenRAG")
        print(f"   python scripts/datasets/import_to_openrag.py {args.output}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
