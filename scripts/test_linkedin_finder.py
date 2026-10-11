import urllib.request
import urllib.parse
import re
import json

def search_duckduckgo_linkedin(company_name, query_title="Brand Manager OR Marketing"):
    query = f'site:linkedin.com/in ("{company_name}") ("{query_title}") India'
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
            
            # Find result snippets and titles
            # DuckDuckGo HTML titles are usually in <a class="result__snippet" ...> or <h2 class="result__title">
            results = []
            
            # Match titles like: "John Doe - Brand Manager - ASUS | LinkedIn"
            matches = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>.*?<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
            raw_titles = re.findall(r'<h2 class="result__title">\s*<a[^>]*>(.*?)</a>', html, re.DOTALL)
            
            for t in raw_titles:
                clean_t = re.sub(r'<[^>]+>', '', t).strip()
                # Clean up " ... - LinkedIn"
                clean_t = re.sub(r'\s*-\s*LinkedIn.*$', '', clean_t, flags=re.IGNORECASE)
                clean_t = re.sub(r'\|\s*LinkedIn.*$', '', clean_t, flags=re.IGNORECASE)
                if "-" in clean_t:
                    parts = [p.strip() for p in clean_t.split("-")]
                    name = parts[0]
                    title = " - ".join(parts[1:])
                    results.append({"name": name, "title": title, "raw": clean_t})
                elif "|" in clean_t:
                    parts = [p.strip() for p in clean_t.split("|")]
                    name = parts[0]
                    title = " | ".join(parts[1:])
                    results.append({"name": name, "title": title, "raw": clean_t})
            
            return results
    except Exception as e:
        print(f"Search error for {company_name}: {e}")
        return []

if __name__ == "__main__":
    for comp in ["ASUS India", "boAt Lifestyle", "iQOO India", "Monster Energy India"]:
        print(f"\nSearching for {comp}...")
        res = search_duckduckgo_linkedin(comp)
        print(f"Found {len(res)} results:")
        for r in res[:4]:
            print(f"  • Name: {r['name']} | Title: {r['title']}")
