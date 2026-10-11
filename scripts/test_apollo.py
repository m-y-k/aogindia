import json
import urllib.request
import urllib.parse

API_KEY = "Y9YhFFBk6NZJV-gOhkvfIg"

def test_apollo():
    url = "https://api.apollo.io/api/v1/mixed_people/search"
    
    payload = {
        "q_organization_domains": "asus.com",
        "person_locations": ["India"],
        "person_titles": ["Marketing", "Brand Manager", "Influencer"],
        "page": 1,
        "per_page": 5
    }
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": API_KEY,
        "User-Agent": "AOG-Test/1.0"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            people = data.get("people", [])
            print(f"Status: {resp.status}, Total contacts found: {len(people)}")
            for idx, p in enumerate(people, start=1):
                email = p.get('email')
                pid = p.get('id')
                name = p.get('name')
                title = p.get('title')
                print(f"[{idx}] {name} | {title} | Email: {email} | ID: {pid}")
                
                # If email is hidden in search, test match/unlock
                if not email and pid:
                    match_url = "https://api.apollo.io/api/v1/people/match"
                    match_req = urllib.request.Request(
                        match_url,
                        data=json.dumps({"id": pid}).encode("utf-8"),
                        headers=headers,
                        method="POST"
                    )
                    try:
                        with urllib.request.urlopen(match_req, timeout=10) as mresp:
                            mdata = json.loads(mresp.read().decode("utf-8"))
                            m_email = mdata.get("person", {}).get("email")
                            print(f"    -> Unlocked Email via Match API: {m_email}")
                    except Exception as me:
                        print(f"    -> Match error: {me}")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print(f"HTTPError {e.code}: {body}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_apollo()
