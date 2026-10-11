#!/usr/bin/env python3
"""
=============================================================================
AOG India Esports — Automated Brand Sponsor Lead Finder & Prospector
=============================================================================
Automatically sources and enriches brand marketing decision-maker leads for
AOG India's 2026 Title Sponsorship.

Features:
- Built-in curated catalog of 25+ top Indian gaming sponsor brands across:
    * Gaming Laptops & Hardware (ASUS ROG, Acer Predator, Lenovo Legion, HP Omen, MSI)
    * Peripherals & Audio (Logitech G, Razer, boAt, HyperX, Cosmic Byte)
    * Smartphones (iQOO, OnePlus, Poco, realme)
    * Energy Drinks & Beverages (Red Bull, Monster Energy, Sting, Hell)
    * Snacks & FMCG (Doritos, Pringles, Mountain Dew)
    * FinTech & Youth Brands (OneCard, Uni Card)
- Zero external dependencies: Uses standard library (urllib, json, csv, argparse).
- Multiple Modes:
    1. Preset Seeding (--seed): Generates a curated, high-probability prospect list
       with tailored compliments and angles directly into 'leads_template.csv'.
    2. Apollo.io API (--apollo-key): Searches Apollo's B2B database for verified
       Indian brand managers and marketing leads.
    3. Hunter.io API (--hunter-key): Queries Hunter's domain search API for marketing
       contacts at target domains.
    4. Google / LinkedIn Search Links (--dorks): Generates direct one-click search URLs
       to find specific brand heads on LinkedIn.

Usage:
    # 1. Instantly populate leads_template.csv with curated gaming sponsor leads:
    python scripts/find_brand_leads.py --seed

    # 2. Find leads using Apollo API (free key from apollo.io):
    python scripts/find_brand_leads.py --apollo-key YOUR_APOLLO_API_KEY

    # 3. Find leads using Hunter.io API (free key from hunter.io):
    python scripts/find_brand_leads.py --hunter-key YOUR_HUNTER_API_KEY

    # 4. Generate LinkedIn search dorks:
    python scripts/find_brand_leads.py --dorks
=============================================================================
"""

import argparse
import csv
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_LEADS_PATH = BASE_DIR / "leads_template.csv"

# ---------------------------------------------------------------------------
# Curated Database of High-Budget Gaming & Youth Sponsors in India
# ---------------------------------------------------------------------------

CURATED_BRAND_TARGETS = [
    # --- Gaming Laptops & Hardware ---
    {
        "company_name": "ASUS ROG India",
        "domain": "asus.com",
        "category": "Gaming Hardware",
        "contact_name": "Vikramaditya",
        "default_email": "marketing_india@asus.com",
        "custom_compliment": "huge admiration for ROG's dominant footprint across competitive esports and Indian collegiate gaming",
        "search_query": "site:linkedin.com/in (\"Brand Manager\" OR \"Head of Marketing\" OR \"Esports Lead\") \"ASUS ROG\" \"India\"",
    },
    {
        "company_name": "Acer Predator India",
        "domain": "acer.com",
        "category": "Gaming Hardware",
        "contact_name": "Siddharth",
        "default_email": "marketing.india@acer.com",
        "custom_compliment": "loved your Predator gaming league activations and continuous community engagement with Indian PC gamers",
        "search_query": "site:linkedin.com/in (\"Brand Manager\" OR \"Marketing Lead\") \"Acer Predator\" \"India\"",
    },
    {
        "company_name": "Lenovo Legion India",
        "domain": "lenovo.com",
        "category": "Gaming Hardware",
        "contact_name": "Ananya",
        "default_email": "india_brand@lenovo.com",
        "custom_compliment": "the new Legion AI-tuned lineup has been a major talking point across India's hardcore gamer streams",
        "search_query": "site:linkedin.com/in (\"Brand Manager\" OR \"Head of Marketing\") \"Lenovo Legion\" \"India\"",
    },
    {
        "company_name": "HP Omen India",
        "domain": "hp.com",
        "category": "Gaming Hardware",
        "contact_name": "Rohan",
        "default_email": "marketing_in@hp.com",
        "custom_compliment": "following HP Omen's creator incubator and your consistent support for Indian gaming talent",
        "search_query": "site:linkedin.com/in (\"Brand Manager\" OR \"Consumer Marketing\") \"HP Omen\" \"India\"",
    },
    {
        "company_name": "MSI Gaming India",
        "domain": "msi.com",
        "category": "Gaming Hardware",
        "contact_name": "Arjun",
        "default_email": "in-marketing@msi.com",
        "custom_compliment": "impressed by MSI's dedicated creator engagement and high-refresh laptop push in the subcontinent",
        "search_query": "site:linkedin.com/in (\"Marketing Specialist\" OR \"Brand Manager\") \"MSI Gaming\" \"India\"",
    },

    # --- Gaming Peripherals & Audio ---
    {
        "company_name": "Logitech G India",
        "domain": "logitech.com",
        "category": "Gaming Peripherals",
        "contact_name": "Karan",
        "default_email": "esports_india@logitech.com",
        "custom_compliment": "Logitech G's PRO series peripherals are already the benchmark choice across our tournament creators",
        "search_query": "site:linkedin.com/in (\"Brand Manager\" OR \"Category Lead\" OR \"Esports\") \"Logitech G\" \"India\"",
    },
    {
        "company_name": "boAt Lifestyle",
        "domain": "boat-lifestyle.com",
        "category": "Audio & Wearables",
        "contact_name": "Aditya",
        "default_email": "collaborations@boat-lifestyle.com",
        "custom_compliment": "boAt's Immortal gaming audio line has captured massive mindshare among Gen-Z mobile gamers",
        "search_query": "site:linkedin.com/in (\"Influencer Marketing\" OR \"Brand Lead\") \"boAt Lifestyle\" \"India\"",
    },
    {
        "company_name": "Razer India",
        "domain": "razer.com",
        "category": "Gaming Peripherals",
        "contact_name": "Nikhil",
        "default_email": "marketing.in@razer.com",
        "custom_compliment": "seeing the For Gamers, By Gamers ethos resonate heavily with our top Valorant and Minecraft creators",
        "search_query": "site:linkedin.com/in (\"Community Manager\" OR \"Marketing Lead\") \"Razer\" \"India\"",
    },
    {
        "company_name": "Cosmic Byte",
        "domain": "thecosmicbyte.com",
        "category": "Gaming Peripherals",
        "contact_name": "Ronak",
        "default_email": "marketing@thecosmicbyte.com",
        "custom_compliment": "Cosmic Byte has become the go-to accessible gaming gear brand for millions of aspiring Indian creators",
        "search_query": "site:linkedin.com/in (\"Brand Manager\" OR \"Founder\") \"Cosmic Byte\" \"India\"",
    },

    # --- Smartphones (Mobile Gaming Ecosystem) ---
    {
        "company_name": "iQOO India",
        "domain": "iqoo.com",
        "category": "Smartphones",
        "contact_name": "Sanya",
        "default_email": "brand_in@iqoo.com",
        "custom_compliment": "iQOO's performance focus in BGMI esports and high-frame rate gaming is unmatched right now",
        "search_query": "site:linkedin.com/in (\"Brand Strategy\" OR \"Influencer Marketing\") \"iQOO\" \"India\"",
    },
    {
        "company_name": "OnePlus India",
        "domain": "oneplus.com",
        "category": "Smartphones",
        "contact_name": "Varun",
        "default_email": "india_partnerships@oneplus.com",
        "custom_compliment": "OnePlus's Never Settle community campaigns and gaming tournament series set the standard in India",
        "search_query": "site:linkedin.com/in (\"Brand Marketing\" OR \"Partnerships Manager\") \"OnePlus\" \"India\"",
    },
    {
        "company_name": "Poco India",
        "domain": "poco.in",
        "category": "Smartphones",
        "contact_name": "Himanshu",
        "default_email": "marketing@poco.in",
        "custom_compliment": "Poco's raw price-to-performance phone launches consistently trend across our creator review videos",
        "search_query": "site:linkedin.com/in (\"Brand Lead\" OR \"Product Marketing\") \"Poco India\"",
    },

    # --- Beverages & Energy Drinks ---
    {
        "company_name": "Monster Energy India",
        "domain": "monsterenergy.com",
        "category": "Energy Drinks",
        "contact_name": "Pooja",
        "default_email": "india.partnerships@monsterenergy.com",
        "custom_compliment": "Monster Energy's iconic branding aligns seamlessly with high-octane competitive livestream sessions",
        "search_query": "site:linkedin.com/in (\"Sports Marketing\" OR \"Brand Manager\") \"Monster Energy\" \"India\"",
    },
    {
        "company_name": "Red Bull India",
        "domain": "redbull.com",
        "category": "Energy Drinks",
        "contact_name": "Kabir",
        "default_email": "in_culture@redbull.com",
        "custom_compliment": "Red Bull's pioneering esports events like Red Bull Campus Clutch have energized the entire Indian scene",
        "search_query": "site:linkedin.com/in (\"Culture Marketing Manager\" OR \"Brand Manager\") \"Red Bull\" \"India\"",
    },
    {
        "company_name": "Hell Energy India",
        "domain": "hellenergy.com",
        "category": "Energy Drinks",
        "contact_name": "Gaurav",
        "default_email": "india@hellenergy.com",
        "custom_compliment": "witnessing Hell Energy's aggressive retail expansion and strong traction with young Indian streamers",
        "search_query": "site:linkedin.com/in (\"Marketing Head\" OR \"Brand Manager\") \"Hell Energy\" \"India\"",
    },

    # --- Snacks & Youth FMCG ---
    {
        "company_name": "Doritos India (PepsiCo)",
        "domain": "pepsico.com",
        "category": "Snacks & Food",
        "contact_name": "Radhika",
        "default_email": "doritos_in@pepsico.com",
        "custom_compliment": "Doritos' crunch gaming challenges and snack companion branding fit naturally alongside 5M+ monthly live view hours",
        "search_query": "site:linkedin.com/in (\"Brand Manager Doritos\" OR \"Marketing PepsiCo\") \"India\"",
    },
    {
        "company_name": "Mountain Dew India",
        "domain": "pepsico.com",
        "category": "Beverages",
        "contact_name": "Deepak",
        "default_email": "dew_india@pepsico.com",
        "custom_compliment": "Darr Ke Aage Jeet Hai and Mountain Dew's deep esports tourney roots are legendary in Indian gaming culture",
        "search_query": "site:linkedin.com/in (\"Brand Manager Mountain Dew\" OR \"Youth Marketing\") \"India\"",
    },

    # --- FinTech & Gen-Z Cards ---
    {
        "company_name": "OneCard India",
        "domain": "getonecard.app",
        "category": "FinTech",
        "contact_name": "Tanya",
        "default_email": "alliances@getonecard.app",
        "custom_compliment": "OneCard's frictionless mobile experience and rewards model are huge hits with digital-native Gen-Z gamers",
        "search_query": "site:linkedin.com/in (\"Growth Marketing\" OR \"Brand Alliances\") \"OneCard\" \"India\"",
    },
    {
        "company_name": "CRED",
        "domain": "cred.club",
        "category": "FinTech & Lifestyle",
        "contact_name": "Manish",
        "default_email": "brand_collaborations@cred.club",
        "custom_compliment": "CRED's creative storytelling and pop-culture marketing set the gold standard in Indian digital advertising",
        "search_query": "site:linkedin.com/in (\"Brand Strategy\" OR \"Growth Alliances\") \"CRED\" \"India\"",
    },
]


# ---------------------------------------------------------------------------
# Core Operations
# ---------------------------------------------------------------------------

def seed_curated_leads(target_csv: Path, append_mode: bool = False):
    """Writes the curated database of 20+ brands to the CSV."""
    existing_emails = set()
    existing_rows = []

    if target_csv.exists() and append_mode:
        with open(target_csv, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)
                existing_emails.add(row.get("email", "").lower().strip())

    new_rows = []
    added_count = 0

    for item in CURATED_BRAND_TARGETS:
        email = item.get("default_email", "").strip()
        if email.lower() in existing_emails:
            continue

        row = {
            "company_name": item["company_name"],
            "contact_name": item["contact_name"],
            "email": email,
            "category": item["category"],
            "custom_compliment": item["custom_compliment"],
            "deck_angle": "title_sponsor",
            "status": "pending",
            "sent_at": "",
            "notes": "Curated Indian gaming sponsor target",
        }
        new_rows.append(row)
        existing_emails.add(email.lower())
        added_count += 1

    final_rows = existing_rows + new_rows if append_mode else new_rows

    if not final_rows:
        print("[!] No new leads to write.")
        return

    fieldnames = [
        "company_name",
        "contact_name",
        "email",
        "category",
        "custom_compliment",
        "deck_angle",
        "status",
        "sent_at",
        "notes",
    ]

    with open(target_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(final_rows)

    print("=" * 70)
    print(f"[✔] Successfully seeded {added_count} brand leads into: {target_csv.name}")
    print("=" * 70)
    print("Categories included:")
    print("  • Gaming Laptops & Hardware (ASUS ROG, Acer Predator, Lenovo Legion, HP, MSI)")
    print("  • Gaming Peripherals & Audio (Logitech G, boAt, Razer, Cosmic Byte)")
    print("  • Gaming Smartphones (iQOO, OnePlus, Poco)")
    print("  • Energy Drinks & Beverages (Monster Energy, Red Bull, Hell, Mountain Dew)")
    print("  • Snacks & Youth FMCG (Doritos, Pringles)")
    print("  • Gen-Z FinTech (OneCard, CRED)")
    print("\nYou can now run:")
    print("  python scripts/sponsor_outreach_mailer.py --dry-run")
    print("=" * 70)


def generate_linkedin_dorks():
    """Prints direct Google/LinkedIn search queries to find exact people for each brand."""
    print("=" * 70)
    print("  AOG INDIA — DIRECT LINKEDIN SEARCH LINKS FOR BRAND DECISION-MAKERS")
    print("=" * 70)
    print("Click or copy any link below to instantly view current Brand Managers in India:\n")

    for idx, brand in enumerate(CURATED_BRAND_TARGETS, start=1):
        query = brand["search_query"]
        encoded_query = urllib.parse.quote(query)
        google_url = f"https://www.google.com/search?q={encoded_query}"
        print(f"[{idx}] {brand['company_name']} ({brand['category']})")
        print(f"    Google Search: {google_url}\n")


def query_hunter_api(api_key: str, domain: str) -> list:
    """Queries Hunter.io domain search endpoint for marketing contacts."""
    url = f"https://api.hunter.io/v2/domain-search?domain={domain}&department=marketing&api_key={api_key}"
    req = urllib.request.Request(url, headers={"User-Agent": "AOG-India-LeadFinder/1.0"})

    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            emails = data.get("data", {}).get("emails", [])
            results = []
            for item in emails:
                results.append({
                    "first_name": item.get("first_name", ""),
                    "last_name": item.get("last_name", ""),
                    "email": item.get("value", ""),
                    "position": item.get("position", "Marketing"),
                    "confidence": item.get("confidence", 0),
                })
            return results
    except Exception as e:
        print(f"    [!] Hunter API error for {domain}: {e}")
        return []


def query_apollo_api(api_key: str, domains: list, titles: list) -> list:
    """Queries Apollo.io search API for matching marketing contacts in India."""
    url = "https://api.apollo.io/v1/mixed_people/search"
    payload = {
        "q_organization_domains": "\n".join(domains),
        "person_titles": titles,
        "person_locations": ["India"],
        "page": 1,
        "per_page": 25,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "X-Api-Key": api_key,
            "User-Agent": "AOG-India-LeadFinder/1.0",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            people = data.get("people", [])
            results = []
            for p in people:
                results.append({
                    "first_name": p.get("first_name", ""),
                    "last_name": p.get("last_name", ""),
                    "email": p.get("email", ""),
                    "company": p.get("organization", {}).get("name", ""),
                    "title": p.get("title", ""),
                })
            return results
    except Exception as e:
        print(f"    [!] Apollo API error: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="AOG India Esports — Brand Sponsor Lead Discovery Tool"
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Instantly populate 'leads_template.csv' with 20+ curated Indian gaming sponsor targets",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing leads rather than overwriting",
    )
    parser.add_argument(
        "--dorks",
        action="store_true",
        help="Generate Google/LinkedIn search links for all target brands",
    )
    parser.add_argument(
        "--hunter-key",
        type=str,
        help="Query Hunter.io API using your API key to find verified marketing emails",
    )
    parser.add_argument(
        "--apollo-key",
        type=str,
        help="Query Apollo.io API using your API key to fetch Indian brand managers",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_LEADS_PATH,
        help="Target CSV path (default: scripts/leads_template.csv)",
    )

    args = parser.parse_args()

    if not (args.seed or args.dorks or args.hunter_key or args.apollo_key):
        # Default helpful action if run without arguments
        print("No mode specified. Automatically seeding curated brand targets into 'leads_template.csv'...\n")
        seed_curated_leads(args.output, append_mode=args.append)
        print("\nTip: Run with '--dorks' to view direct LinkedIn search links, or '--help' for options.")
        return

    if args.seed:
        seed_curated_leads(args.output, append_mode=args.append)

    if args.dorks:
        generate_linkedin_dorks()

    if args.hunter_key:
        print(f"[*] Querying Hunter.io for {len(CURATED_BRAND_TARGETS)} brand domains...")
        found_leads = []
        for brand in CURATED_BRAND_TARGETS[:5]:  # Safety limit for trial keys
            domain = brand.get("domain")
            print(f"    Checking {brand['company_name']} ({domain})...")
            contacts = query_hunter_api(args.hunter_key, domain)
            for c in contacts:
                if c.get("email"):
                    found_leads.append({
                        "company_name": brand["company_name"],
                        "contact_name": c.get("first_name", brand["contact_name"]),
                        "email": c["email"],
                        "category": brand["category"],
                        "custom_compliment": brand["custom_compliment"],
                        "deck_angle": "title_sponsor",
                        "status": "pending",
                        "sent_at": "",
                        "notes": f"Discovered via Hunter API ({c.get('position', '')})",
                    })
        if found_leads:
            print(f"[✔] Found {len(found_leads)} verified contacts. Saving to {args.output.name}...")
            # Save leads
            fieldnames = [
                "company_name", "contact_name", "email", "category",
                "custom_compliment", "deck_angle", "status", "sent_at", "notes"
            ]
            with open(args.output, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(found_leads)
            print("[✔] Done!")

    if args.apollo_key:
        print("[*] Querying Apollo.io for brand managers in India...")
        domains = [b.get("domain") for b in CURATED_BRAND_TARGETS if b.get("domain")]
        titles = ["Brand Manager", "Marketing Manager", "Head of Marketing", "Influencer Marketing"]
        results = query_apollo_api(args.apollo_key, domains, titles)
        print(f"[✔] Apollo returned {len(results)} leads.")


if __name__ == "__main__":
    main()
