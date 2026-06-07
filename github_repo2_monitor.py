#!/usr/bin/env python3
"""
Customs Regulation Monitor — Track trade regulation changes in real-time.
"""

import argparse
import json
import time
import hashlib
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError


SOURCES = [
    {
        'name': 'WTO_TBT',
        'url': 'https://api.wto.org/tbt/notifications',
        'country_filter': True,
    },
    {
        'name': 'EU_TAXUD',
        'url': 'https://ec.europa.eu/taxud/customs/api/updates',
        'country_filter': False,
    },
    {
        'name': 'China_Customs',
        'url': 'https://www.customs.gov.cn/api/regulation-updates',
        'country_filter': True,
    },
]


def fetch_source(source, countries=None):
    """Fetch regulation updates from a source."""
    url = source['url']
    if source['country_filter'] and countries:
        url += f"?countries={','.join(countries)}"
    
    try:
        req = Request(url, headers={'User-Agent': 'ComplianceMonitor/1.0'})
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            return data.get('notifications', data.get('updates', []))
    except Exception as e:
        print(f"  ⚠ {source['name']}: {e}")
        return []


def check_relevance(item, keywords):
    """Check if a regulation update is relevant to tracked keywords."""
    text = json.dumps(item).lower()
    return any(kw.lower() in text for kw in keywords)


def generate_digest(items, keywords):
    """Generate a digest of relevant regulation changes."""
    relevant = [i for i in items if check_relevance(i, keywords)]
    
    digest = []
    for item in relevant[:20]:  # Top 20
        digest.append({
            'title': item.get('title', item.get('subject', 'Untitled')),
            'date': item.get('date', item.get('publication_date', 'Unknown')),
            'country': item.get('country', item.get('member', 'Unknown')),
            'summary': item.get('description', item.get('summary', ''))[:200],
            'url': item.get('url', item.get('link', '#')),
        })
    
    return digest


def main():
    parser = argparse.ArgumentParser(
        description='Monitor international customs and trade regulation changes'
    )
    parser.add_argument('--track', '-t', default='china,us,eu',
                       help='Countries to track (comma-separated)')
    parser.add_argument('--keywords', '-k',
                       default='certificate of origin,apostille,customs clearance',
                       help='Keywords to filter for relevance')
    parser.add_argument('--output', '-o', default='digest.json',
                       help='Output file path')
    
    args = parser.parse_args()
    countries = [c.strip() for c in args.track.split(',')]
    keywords = [k.strip() for k in args.keywords.split(',')]
    
    print(f"🔍 Monitoring regulation changes for: {', '.join(countries)}")
    print(f"📋 Filtering for: {', '.join(keywords)}")
    print()
    
    all_items = []
    for source in SOURCES:
        print(f"  Fetching {source['name']}...")
        items = fetch_source(source, countries)
        all_items.extend(items)
        print(f"    → {len(items)} items found")
    
    digest = generate_digest(all_items, keywords)
    
    report = {
        'generated_at': datetime.utcnow().isoformat(),
        'countries_monitored': countries,
        'keywords': keywords,
        'total_items': len(all_items),
        'relevant_items': len(digest),
        'digest': digest,
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Digest generated: {args.output}")
    print(f"   Total items: {len(all_items)}")
    print(f"   Relevant items: {len(digest)}")


if __name__ == '__main__':
    main()
