#!/usr/bin/env python3
"""
Download arXiv papers from specific category

Usage:
    pip install arxiv
    python download_arxiv.py --category cs.AI --limit 1000 --output /tmp/arxiv_cs_ai.json
"""

import time
import json
import argparse
from typing import List, Dict
from pathlib import Path

try:
    import arxiv
except ImportError:
    print("❌ Error: arxiv package not installed")
    print("Install with: pip install arxiv")
    exit(1)


def download_arxiv_papers(category: str = "cs.AI", limit: int = 1000, output_file: str = None) -> List[Dict]:
    """
    Download arXiv papers from specific category
    
    Args:
        category: arXiv category (cs.AI, cs.CL, cs.LG, cs.CV, etc.)
        limit: Number of papers to download
        output_file: Output JSON file path
        
    Returns:
        List of papers with title, abstract, authors, etc.
    """
    
    print(f"📥 Downloading {limit} arXiv papers from category '{category}'...")
    
    papers = []
    
    # Search query
    search = arxiv.Search(
        query=f"cat:{category}",
        max_results=limit,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    print("📖 Fetching papers...")
    
    for i, result in enumerate(search.results()):
        try:
            papers.append({
                "title": result.title,
                "content": result.summary,  # Abstract
                "authors": [author.name for author in result.authors],
                "url": result.entry_id,
                "pdf_url": result.pdf_url,
                "published": result.published.isoformat(),
                "updated": result.updated.isoformat() if result.updated else None,
                "categories": result.categories,
                "source": "arxiv",
                "primary_category": category
            })
            
            if (i + 1) % 100 == 0:
                print(f"  ✓ Downloaded {i + 1}/{limit} papers...")
            
            # Rate limiting (be nice to arXiv API)
            time.sleep(0.1)
            
        except Exception as e:
            print(f"  ⚠️ Error downloading paper {i + 1}: {e}")
            continue
    
    print(f"\n✅ Successfully downloaded {len(papers)} papers")
    
    # Save to JSON if output file specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved to {output_file}")
        
        # Stats
        total_chars = sum(len(p["content"]) for p in papers)
        avg_chars = total_chars / len(papers) if papers else 0
        print(f"\n📊 Statistics:")
        print(f"  - Total papers: {len(papers)}")
        print(f"  - Total characters: {total_chars:,}")
        print(f"  - Average chars per abstract: {avg_chars:,.0f}")
        print(f"  - Estimated chunks (2000 chars): {total_chars // 2000:,}")
        
        # Categories breakdown
        all_categories = {}
        for p in papers:
            for cat in p["categories"]:
                all_categories[cat] = all_categories.get(cat, 0) + 1
        
        print(f"\n🏷️ Categories:")
        for cat, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {cat}: {count}")
    
    return papers


def main():
    parser = argparse.ArgumentParser(
        description="Download arXiv papers from specific category"
    )
    parser.add_argument(
        "--category",
        type=str,
        default="cs.AI",
        help="arXiv category (cs.AI, cs.CL, cs.LG, cs.CV, etc.)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Number of papers to download (default: 1000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/arxiv_papers_1000.json",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    try:
        papers = download_arxiv_papers(
            category=args.category,
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
