#!/usr/bin/env python3
"""
===================================================================
AOG INDIA ESPORTS — AUTOMATED WEEKLY SEO ENGINE
100% Free Automated Search Keyword Discovery & Meta Tag Optimizer
===================================================================
Discovers live search terms typed by brands in India, filters for high
search intent, updates HTML meta tags, JSON-LD Schema, and sitemap.xml,
and optionally purges Cloudflare CDN cache via API.
"""

import os
import re
import json
import urllib.request
import urllib.parse
from datetime import datetime

# ─── SEED KEYWORD TOPICS (HIGH-INTENT BRAND QUERIES IN INDIA) ───────
SEED_TOPICS = [
    "gaming marketing agency india",
    "bgmi creator agency",
    "mobile game marketing india",
    "gaming influencer agency",
    "gaming product seeding india",
    "esports marketing agency india",
    "gen z creator agency india",
    "gaming influencer campaign cost"
]

# ─── NEGATIVE KEYWORDS TO FILTER OUT UNWANTED SEARCHES ──────────────
NEGATIVE_KEYWORDS = {
    "hack", "mod", "cheat", "download", "free", "apk", "crack", 
    "script", "bug", "redeem", "code", "password", "login", "leak"
}

# ─── BASE CORE BRAND KEYWORDS (ALWAYS RETAINED) ─────────────────────
CORE_KEYWORDS = [
    "gaming marketing agency india",
    "influencer marketing agency india",
    "gaming influencer marketing india",
    "BGMI creator campaigns",
    "mobile game marketing india",
    "paid promotions gaming creators india",
    "gaming product seeding",
    "white-label influencer marketing",
    "esports agency india",
    "YouTube gaming creators india",
    "Instagram gaming influencers india"
]

def fetch_google_suggestions(query):
    """Fetch live search suggestions from Google Autocomplete API for India (gl=in)."""
    encoded = urllib.parse.quote(query)
    url = f"https://suggestqueries.google.com/complete/search?client=chrome&hl=en&gl=in&q={encoded}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, list) and len(data) > 1:
                return data[1]  # list of suggested search terms
    except Exception as e:
        print(f"[SEO Engine] Warning fetching suggestions for '{query}': {e}")
    return []

def discover_keywords():
    """Discover, clean, and rank live search terms."""
    discovered = set(CORE_KEYWORDS)
    print("[SEO Engine] Discovering live brand search queries in India...")

    for seed in SEED_TOPICS:
        suggestions = fetch_google_suggestions(seed)
        for term in suggestions:
            term_clean = term.strip().lower()
            # Filter out terms with negative keywords or too short
            words = set(term_clean.split())
            if not words.intersection(NEGATIVE_KEYWORDS) and len(term_clean) > 8:
                discovered.add(term_clean)

    # Sort & return top 20 clean keywords
    keyword_list = list(discovered)[:20]
    print(f"[SEO Engine] Discovered {len(keyword_list)} high-intent brand search terms.")
    return keyword_list

def update_html_keywords(file_path, keyword_str, keyword_list):
    """Update <meta name="keywords"> and JSON-LD knowsAbout in HTML file."""
    if not os.path.exists(file_path):
        print(f"[SEO Engine] File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update <meta name="keywords" content="...">
    meta_pattern = r'(<meta\s+name="keywords"\s+content=")[^"]*(".*?>)'
    if re.search(meta_pattern, content):
        content = re.sub(meta_pattern, f'\\g<1>{keyword_str}\\g<2>', content)
        print(f"[SEO Engine] Updated meta keywords in {os.path.basename(file_path)}")
    else:
        # Insert after <meta name="description"> if meta keywords tag doesn't exist
        desc_pattern = r'(<meta\s+name="description"\s+content="[^"]*".*?>)'
        new_meta = f'\n  <meta name="keywords" content="{keyword_str}">'
        content = re.sub(desc_pattern, f'\\1{new_meta}', content)
        print(f"[SEO Engine] Added meta keywords tag to {os.path.basename(file_path)}")

    # 2. Update JSON-LD "knowsAbout" array if present
    knows_pattern = r'("knowsAbout":\s*\[)[^\]]*(\])'
    if re.search(knows_pattern, content):
        knows_json = json.dumps(keyword_list, indent=10).replace('\n', '\n          ')
        content = re.sub(knows_pattern, f'"knowsAbout": {knows_json}', content)
        print(f"[SEO Engine] Updated JSON-LD knowsAbout in {os.path.basename(file_path)}")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

def update_sitemap(sitemap_path):
    """Update lastmod dates in sitemap.xml to current date."""
    if not os.path.exists(sitemap_path):
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    with open(sitemap_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = re.sub(r'<lastmod>[^<]*</lastmod>', f'<lastmod>{today_str}</lastmod>', content)

    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[SEO Engine] Updated sitemap.xml lastmod timestamps to {today_str}")

def purge_cloudflare_cache():
    """Purge Cloudflare CDN cache via API if Secrets environment variables exist."""
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")

    if not zone_id or not api_token:
        print("[SEO Engine] Cloudflare API secrets not set in environment. Skipping automatic CDN cache purge.")
        return

    print("[SEO Engine] Purging Cloudflare CDN cache via API...")
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    payload = json.dumps({"purge_everything": True}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            res_data = json.loads(resp.read().decode("utf-8"))
            if res_data.get("success"):
                print("[SEO Engine] Cloudflare CDN Cache purged successfully!")
            else:
                print(f"[SEO Engine] Cloudflare Cache purge failed: {res_data}")
    except Exception as e:
        print(f"[SEO Engine] Error purging Cloudflare cache: {e}")

def main():
    print("==========================================================")
    print("  AOG INDIA ESPORTS — AUTOMATED SEO DISCOVERY & UPDATE   ")
    print("==========================================================")
    
    keywords = discover_keywords()
    keyword_str = ", ".join(keywords)

    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    index_html = os.path.join(root_dir, "index.html")
    for_brands_html = os.path.join(root_dir, "for-brands.html")
    for_agencies_html = os.path.join(root_dir, "for-agencies.html")
    sitemap_xml = os.path.join(root_dir, "sitemap.xml")

    update_html_keywords(index_html, keyword_str, keywords)
    update_html_keywords(for_brands_html, keyword_str, keywords)
    update_html_keywords(for_agencies_html, keyword_str, keywords)
    update_sitemap(sitemap_xml)
    purge_cloudflare_cache()

    print("[SEO Engine] Automated SEO update completed successfully!")

if __name__ == "__main__":
    main()
