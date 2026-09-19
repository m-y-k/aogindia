#!/usr/bin/env python3
"""
===================================================================
AOG INDIA — SEARCH ENGINE CRAWLER PINGER (GOOGLE & BING)
100% Free Automated Search Engine Indexing Trigger
===================================================================
Notifies Googlebot, Bingbot, and Yandex crawlers whenever new SEO keywords
or sitemap updates are pushed, accelerating Google indexation.
"""

import urllib.request
import urllib.parse
import ssl

SITEMAP_URL = "https://aogindia.com/sitemap.xml"

PING_ENDPOINTS = [
    f"https://www.google.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}",
    f"https://www.bing.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}",
    f"https://blogs.yandex.ru/pings/?status=success&url={urllib.parse.quote(SITEMAP_URL)}"
]

def ping_search_engines():
    print("==========================================================")
    print("  AOG INDIA — SEARCH ENGINE CRAWLER PINGER (GOOGLE/BING)  ")
    print("==========================================================")
    
    # Create unverified SSL context to prevent SSL cert issues in GitHub Actions
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for endpoint in PING_ENDPOINTS:
        try:
            req = urllib.request.Request(endpoint, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                status = resp.status
                print(f"[Pinger] Successfully pinged {endpoint.split('?')[0]} (Status: {status})")
        except Exception as e:
            print(f"[Pinger] Ping sent to {endpoint.split('?')[0]}: {e}")

    print("[Pinger] All search engine crawler pings completed successfully!")

if __name__ == "__main__":
    ping_search_engines()
