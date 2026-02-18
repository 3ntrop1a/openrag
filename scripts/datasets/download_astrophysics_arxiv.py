#!/usr/bin/env python3
"""
Download astrophysics papers from arXiv (astro-ph category)
Uses direct API calls - no external dependencies needed

Usage:
    /usr/bin/python3 download_astrophysics_arxiv.py --limit 500 --output /tmp/astrophysics_500.json
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import time
import argparse
from typing import List, Dict
from pathlib import Path


def download_arxiv_astrophysics(limit: int = 500, output_file: str = None) -> List[Dict]:
    """
    Download astrophysics papers from arXiv
    
    Args:
        limit: Number of papers to download
        output_file: Output JSON file path
        
    Returns:
        List of papers with title, abstract, authors, etc.
    """
    
    print(f"🌌 Downloading {limit} astrophysics papers from arXiv...")
    
    base_url = "http://export.arxiv.org/api/query?"
    papers = []
    batch_size = 100  # arXiv API max results per request
    
    # arXiv astro-ph categories:
    # astro-ph.CO - Cosmology and Nongalactic Astrophysics
    # astro-ph.EP - Earth and Planetary Astrophysics
    # astro-ph.GA - Astrophysics of Galaxies
    # astro-ph.HE - High Energy Astrophysical Phenomena
    # astro-ph.IM - Instrumentation and Methods for Astrophysics
    # astro-ph.SR - Solar and Stellar Astrophysics
    
    query = "cat:astro-ph*"  # All astrophysics categories
    
    num_batches = (limit + batch_size - 1) // batch_size
    
    for batch_num in range(num_batches):
        start = batch_num * batch_size
        max_results = min(batch_size, limit - len(papers))
        
        if max_results <= 0:
            break
        
        print(f"\n📥 Batch {batch_num + 1}/{num_batches}: Fetching {max_results} papers (start={start})...")
        
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        url = base_url + urllib.parse.urlencode(params)
        
        try:
            # Add User-Agent header to avoid blocking
            req = urllib.request.Request(url, headers={
                'User-Agent': 'OpenRAG/1.0 (Educational project; mailto:admin@example.com)'
            })
            
            with urllib.request.urlopen(req, timeout=60) as response:
                xml_data = response.read().decode('utf-8')
            
            # Parse XML
            root = ET.fromstring(xml_data)
            
            # Namespace for arXiv API
            ns = {'atom': 'http://www.w3.org/2005/Atom',
                  'arxiv': 'http://arxiv.org/schemas/atom'}
            
            entries = root.findall('atom:entry', ns)
            
            if not entries:
                print(f"  ⚠️ No entries found in batch {batch_num + 1}")
                break
            
            for entry in entries:
                try:
                    # Extract paper information
                    title = entry.find('atom:title', ns).text.strip().replace('\n', ' ')
                    summary = entry.find('atom:summary', ns).text.strip().replace('\n', ' ')
                    published = entry.find('atom:published', ns).text.strip()
                    updated_elem = entry.find('atom:updated', ns)
                    updated = updated_elem.text.strip() if updated_elem is not None else published
                    
                    # Main link
                    link = entry.find('atom:id', ns).text.strip()
                    
                    # PDF link
                    pdf_link = None
                    for link_elem in entry.findall('atom:link', ns):
                        if link_elem.get('title') == 'pdf':
                            pdf_link = link_elem.get('href')
                            break
                    
                    # Authors
                    authors = []
                    for author in entry.findall('atom:author', ns):
                        name = author.find('atom:name', ns)
                        if name is not None:
                            authors.append(name.text.strip())
                    
                    # Categories
                    categories = []
                    for category in entry.findall('atom:category', ns):
                        term = category.get('term')
                        if term:
                            categories.append(term)
                    
                    # Primary category
                    primary_cat = entry.find('arxiv:primary_category', ns)
                    primary_category = primary_cat.get('term') if primary_cat is not None else 'astro-ph'
                    
                    papers.append({
                        "title": title,
                        "content": summary,  # Abstract
                        "authors": authors,
                        "url": link,
                        "pdf_url": pdf_link,
                        "published": published,
                        "updated": updated,
                        "categories": categories,
                        "source": "arxiv",
                        "primary_category": primary_category,
                        "domain": "astrophysics"
                    })
                    
                except Exception as e:
                    print(f"  ⚠️ Error parsing entry: {e}")
                    continue
            
            print(f"  ✓ Downloaded {len(papers)}/{limit} papers...")
            
            # Rate limiting (arXiv recommends 3 seconds between requests)
            if batch_num < num_batches - 1:
                print(f"  ⏳ Waiting 3 seconds (arXiv rate limit)...")
                time.sleep(3)
            
        except Exception as e:
            print(f"  ❌ Error fetching batch {batch_num + 1}: {e}")
            break
    
    print(f"\n✅ Successfully downloaded {len(papers)} astrophysics papers")
    
    # Save to JSON
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved to {output_file}")
        
        # Stats
        total_chars = sum(len(p["content"]) for p in papers)
        avg_chars = total_chars / len(papers) if papers else 0
        
        # Categories breakdown
        all_categories = {}
        for p in papers:
            for cat in p["categories"]:
                all_categories[cat] = all_categories.get(cat, 0) + 1
        
        print(f"\n📊 Statistics:")
        print(f"  - Total papers: {len(papers)}")
        print(f"  - Total characters: {total_chars:,}")
        print(f"  - Average chars per abstract: {avg_chars:,.0f}")
        print(f"  - Estimated chunks (2000 chars): {total_chars // 2000:,}")
        
        print(f"\n🏷️ Top Categories:")
        for cat, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {cat}: {count}")
    
    return papers


def main():
    parser = argparse.ArgumentParser(
        description="Download astrophysics papers from arXiv"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Number of papers to download (default: 500)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="/tmp/astrophysics_arxiv_500.json",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    try:
        papers = download_arxiv_astrophysics(
            limit=args.limit,
            output_file=args.output
        )
        
        print(f"\n🎉 Download complete!")
        print(f"📂 Next step: Import to OpenRAG")
        print(f"   /usr/bin/python3 scripts/datasets/import_to_openrag.py {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
