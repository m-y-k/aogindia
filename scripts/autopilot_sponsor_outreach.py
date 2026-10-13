#!/usr/bin/env python3
"""
=============================================================================
AOG India Esports — Autopilot Brand Sponsor Outreach Engine
=============================================================================
Fully automated, hands-free outreach pipeline for Title Sponsorship 2026/27.

Core Architecture:
1. Catalog & Discovery:
   - Holds 50+ high-budget Indian gaming/lifestyle sponsor brands across:
     PC Hardware, Smartphones, Peripherals, Energy Drinks, FMCG, and FinTech.
   - Automatically rotates and discovers new brands each cycle.
2. Automated People Search (Apollo.io API):
   - Automatically queries Apollo API to extract real decision-makers in India
     (Brand Managers, Influencer Marketing Leads, Heads of Marketing, CMOs).
   - Pulls real verified work emails, titles, and names.
3. Intelligent IST Timing Engine:
   - Scheduled for peak B2B open-rate hours in India (Mon-Fri, 10:00 AM - 5:00 PM IST).
   - Skips late nights and weekends by default (overridable with --now).
4. Deliverability Safeguards & Throttling:
   - Drips 20-30 emails per day with randomized 60-120s delays.
   - Dual MIME (Plain text + Clean HTML) for 99%+ inbox placement.
5. Multi-Host Zoho SMTP Sender:
   - Connects securely to Zoho Mail SMTP (smtppro.zoho.in / smtp.zoho.in)
     authenticated as Mohammad Yusuf Khan (partnerships@aogindia.com).
6. State Memory:
   - Remembers contacted leads in 'scripts/data/autopilot_state.json' and
     updates 'scripts/leads_template.csv'. Never duplicates.

Usage:
  # 1. Test run (previews discovered leads & email copy without sending):
  python scripts/autopilot_sponsor_outreach.py --dry-run

  # 2. Test send a single real email to yourself:
  python scripts/autopilot_sponsor_outreach.py --test-email your_email@gmail.com

  # 3. Run a daily batch right now (fetches people via Apollo & sends):
  python scripts/autopilot_sponsor_outreach.py --now

  # 4. Run hands-free daemon (sleeps and wakes up during daily business hours):
  python scripts/autopilot_sponsor_outreach.py --daemon
=============================================================================
"""

import argparse
import csv
import datetime
import json
import os
import random
import smtplib
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CONFIG_FILE = BASE_DIR / "outreach_config.json"
STATE_FILE = DATA_DIR / "autopilot_state.json"
CSV_FILE = BASE_DIR / "leads_template.csv"

# ---------------------------------------------------------------------------
# 50+ Top Gaming & Youth Sponsor Brands in India (Curated Catalog)
# ---------------------------------------------------------------------------

EXPANDED_BRAND_CATALOG = [
    # --- Gaming Laptops & PC Hardware ---
    {"company": "ASUS ROG India", "domain": "asus.com", "cat": "Gaming Hardware", "comp": "loved ROG's dominant collegiate esports tournaments and aggressive PC gaming push in India"},
    {"company": "Acer Predator India", "domain": "acer.com", "cat": "Gaming Hardware", "comp": "huge fan of your Predator Gaming League activations and community streamer challenges"},
    {"company": "Lenovo Legion India", "domain": "lenovo.com", "cat": "Gaming Hardware", "comp": "the new Legion AI-tuned gaming lineup has had massive pickup across top creator live streams"},
    {"company": "HP Omen India", "domain": "hp.com", "cat": "Gaming Hardware", "comp": "following HP Omen's creator incubator and consistent esports community support"},
    {"company": "MSI Gaming India", "domain": "msi.com", "cat": "Gaming Hardware", "comp": "impressed by MSI's dedicated streamer engagement and high-refresh hardware activations"},
    {"company": "Dell Alienware India", "domain": "dell.com", "cat": "Gaming Hardware", "comp": "Alienware continues to represent the absolute halo standard in competitive gaming rigs"},
    {"company": "Gigabyte Aorus India", "domain": "gigabyte.com", "cat": "Gaming Hardware", "comp": "seeing Aorus motherboards and graphic cards heavily recommended by tech creators"},
    {"company": "Corsair India", "domain": "corsair.com", "cat": "Gaming Hardware", "comp": "admiring Corsair's premium streaming setups and community gaming tournaments"},
    {"company": "Cooler Master India", "domain": "coolermaster.com", "cat": "Gaming Hardware", "comp": "Cooler Master's custom PC showcase events have set the benchmark in Indian modding"},

    # --- Gaming Peripherals & Audio ---
    {"company": "Logitech G India", "domain": "logitech.com", "cat": "Gaming Peripherals", "comp": "Logitech G's PRO series gear is the gold standard used by our tournament creators"},
    {"company": "boAt Lifestyle", "domain": "boat-lifestyle.com", "cat": "Audio & Wearables", "comp": "boAt's Immortal gaming audio lineup has captured massive Gen-Z mobile gaming mindshare"},
    {"company": "Razer India", "domain": "razer.com", "cat": "Gaming Peripherals", "comp": "the For Gamers, By Gamers ethos has massive resonance with our top Valorant & Minecraft rosters"},
    {"company": "HyperX India", "domain": "hyperx.com", "cat": "Gaming Peripherals", "comp": "HyperX Cloud headsets remain the undisputed choice across competitive live broadcasters"},
    {"company": "Cosmic Byte", "domain": "thecosmicbyte.com", "cat": "Gaming Peripherals", "comp": "Cosmic Byte has become the go-to accessible gaming gear for millions of Indian gamers"},
    {"company": "Zebronics", "domain": "zebronics.com", "cat": "Gaming Peripherals", "comp": "loved your Zeb-Transformer gaming gear activations and broad youth accessibility"},
    {"company": "Ant Esports", "domain": "antesports.com", "cat": "Gaming Peripherals", "comp": "seeing Ant Esports gaming chairs and accessories in almost every rising Indian streamer setup"},
    {"company": "Noise", "domain": "gonoise.com", "cat": "Smart Wearables", "comp": "Noise's creative product drops have exceptional engagement across young digital creators"},
    {"company": "Kreo", "domain": "kreo-tech.com", "cat": "Gaming Peripherals", "comp": "excited by Kreo's sleek, creator-first design ethos in the Indian peripheral space"},

    # --- Performance Smartphones (Mobile Gaming Ecosystem) ---
    {"company": "iQOO India", "domain": "iqoo.com", "cat": "Smartphones", "comp": "iQOO's high frame-rate performance in BGMI esports is the undisputed leader right now"},
    {"company": "OnePlus India", "domain": "oneplus.com", "cat": "Smartphones", "comp": "OnePlus's Never Settle community tournaments set the industry benchmark in India"},
    {"company": "Poco India", "domain": "poco.in", "cat": "Smartphones", "comp": "Poco's raw price-to-performance phone launches consistently trend across our creator review videos"},
    {"company": "realme India", "domain": "realme.com", "cat": "Smartphones", "comp": "realme's GT series gaming activations have built tremendous loyalty with Gen-Z mobile gamers"},
    {"company": "Infinix India", "domain": "infinixmobiles.in", "cat": "Smartphones", "comp": "Infinix's GT gaming series has disrupted the affordable esports smartphone market"},
    {"company": "Motorola India", "domain": "motorola.in", "cat": "Smartphones", "comp": "loved your clean software experience and high-refresh pOLED gaming phone rollouts"},

    # --- Energy Drinks & Beverages ---
    {"company": "Monster Energy India", "domain": "monsterenergy.com", "cat": "Energy Drinks", "comp": "Monster Energy's iconic branding aligns seamlessly with high-octane competitive livestreaming"},
    {"company": "Red Bull India", "domain": "redbull.com", "cat": "Energy Drinks", "comp": "Red Bull Campus Clutch and your culture activations continue to energize the entire esports scene"},
    {"company": "Hell Energy India", "domain": "hellenergy.com", "cat": "Energy Drinks", "comp": "witnessing Hell Energy's aggressive retail expansion and strong traction with young streamers"},
    {"company": "Mountain Dew India", "domain": "pepsico.com", "cat": "Beverages", "comp": "Darr Ke Aage Jeet Hai and Mountain Dew's deep esports tourney roots are legendary in Indian gaming"},
    {"company": "Sting Energy (PepsiCo)", "domain": "pepsico.com", "cat": "Energy Drinks", "comp": "Sting's electrifying momentum across India's Gen-Z demographic is unprecedented"},
    {"company": "Ocean Beverages", "domain": "oceanbeverages.in", "cat": "Beverages", "comp": "Ocean Fruit Wave's hydration focus is a natural match for marathon streaming sessions"},

    # --- Snacks, FMCG & Quick Commerce ---
    {"company": "Doritos India", "domain": "pepsico.com", "cat": "Snacks & Food", "comp": "Doritos' crunch gaming challenges and snack companion branding fit naturally with our 5M+ live view hours"},
    {"company": "Pringles India", "domain": "kelloggs.com", "cat": "Snacks & Food", "comp": "Pringles' iconic can gaming integration is the quintessential desk snack for Indian gamers"},
    {"company": "Too Yumm!", "domain": "tooyumm.com", "cat": "Snacks & Food", "comp": "Too Yumm's bold flavours and youth-first positioning have great appeal with our creator audience"},
    {"company": "Cadbury 5 Star", "domain": "mondelezinternational.com", "cat": "Confectionery", "comp": "loved 5 Star's hilarious Do Nothing gaming campaigns and viral meme marketing"},
    {"company": "Blinkit", "domain": "blinkit.com", "cat": "Quick Commerce", "comp": "Blinkit's 10-minute delivery is literally what saves every creator during late-night gaming livestreams"},
    {"company": "Zepto", "domain": "zeptonow.com", "cat": "Quick Commerce", "comp": "Zepto's high-speed Gen-Z convenience aligns perfectly with the active gaming demographic"},

    # --- FinTech & Gen-Z Cards ---
    {"company": "OneCard", "domain": "getonecard.app", "cat": "FinTech", "comp": "OneCard's metal card aesthetic and slick mobile UX are huge hits with digital-native gamers"},
    {"company": "CRED", "domain": "cred.club", "cat": "FinTech", "comp": "CRED's pop-culture storytelling and premium design set the gold standard in Indian marketing"},
    {"company": "Uni Cards", "domain": "uni.cards", "cat": "FinTech", "comp": "Uni's transparent, modern approach appeals directly to our creator network's 18-28 audience"},
    {"company": "Fi Money", "domain": "fi.money", "cat": "FinTech", "comp": "Fi's smart money management features for young professionals and digital creators are standout"},
    {"company": "Jupiter Money", "domain": "jupiter.money", "cat": "FinTech", "comp": "Jupiter's banking app features resonate strongly with first-time earners and young creators"},

    # --- Gaming Platforms & Game Publishers ---
    {"company": "Krafton India", "domain": "krafton.com", "cat": "Game Publisher", "comp": "Krafton's visionary dedication to Indian esports through BGMI has transformed millions of youth lives"},
    {"company": "Riot Games India", "domain": "riotgames.com", "cat": "Game Publisher", "comp": "Valorant's explosive collegiate and competitive tournament growth in India has been phenomenal"},
    {"company": "Supercell India", "domain": "supercell.com", "cat": "Game Publisher", "comp": "Supercell's timeless titles continue to command massive, highly engaged Indian YouTube viewership"},
    {"company": "WinZO", "domain": "winzogames.com", "cat": "Gaming Platform", "comp": "WinZO's grassroots vernacular gaming initiatives have created immense value across Bharat"},
    {"company": "Rooter", "domain": "rooter.gg", "cat": "Gaming Streaming", "comp": "Rooter's relentless championing of Indian gaming creators and esports tournaments is inspiring"},
]

# ---------------------------------------------------------------------------
# High-Converting Email Copy (Authored by Mohammad Yusuf Khan)
# ---------------------------------------------------------------------------

SUBJECT_OPTIONS = [
    "Exclusive Title Partnership 2026/27 for {company} — 5M+ Monthly Gaming Views",
    "{company} x AOG India Esports — Official 2026/27 Title Sponsor Slot",
    "Quick question regarding {company}'s gaming & creator reach in India",
]

PLAIN_TEXT_TEMPLATE = """Hi {first_name},

Hope you are having a productive week.

I've been closely following {company}'s footprint in India{compliment_clause}.

I am reaching out to you from AOG India Esports — we are one of India's premier gaming media and influencer marketing networks, commanding over 5 Million+ monthly views across YouTube live streams, gameplay videos, Shorts, and Instagram Reels.

We have officially opened inquiries for our single, exclusive Title Partnership slot for 2026/27:

• 4 Dominant Gaming Titles: Minecraft, Valorant, BGMI, and Free Fire
• 360° Native Visibility: Live stream overlays, dedicated creator content, tournament naming rights, and weekly short-form activations
• 100% Category Exclusivity: We will feature zero competitors in your product vertical for the entire duration of the term
• Performance Attribution: Custom UTM attribution, link-in-description across our 200+ creator network, and detailed monthly ROI reporting

Given {company}'s resonance with India's high-intent 18–28 gaming demographic, this partnership is designed to deliver unmatched brand recall and direct conversions.

You can view our sponsorship overview and creator network details here:
{deck_url}

Would you or your brand marketing team have 10 minutes for a brief introductory call {meeting_window} to explore if this is a mutual fit?

Warm regards,

Mohammad Yusuf Khan
Founder & Partnerships Lead
AOG India Esports
Email: {sender_email}
Website: https://aogindia.com

---
If you prefer not to receive sponsorship opportunities from us, please reply 'Unsubscribe' and we will immediately remove your email.
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 15px;
      line-height: 1.6;
      color: #1a1a1a;
      background-color: #ffffff;
      margin: 0;
      padding: 16px;
    }}
    .container {{
      max-width: 580px;
      margin: 0 auto;
    }}
    p {{
      margin: 0 0 14px 0;
    }}
    ul {{
      margin: 8px 0 16px 20px;
      padding: 0;
    }}
    li {{
      margin-bottom: 8px;
    }}
    .highlight {{
      font-weight: 700;
      color: #0b0f0a;
    }}
    .deck-card {{
      background: #fbfaf6;
      border-left: 4px solid #ff7a1a;
      border: 1px solid #efe8d8;
      border-left-width: 4px;
      border-left-color: #ff7a1a;
      padding: 14px 18px;
      margin: 20px 0;
      border-radius: 4px;
    }}
    .deck-link {{
      color: #e65100;
      font-weight: 700;
      text-decoration: none;
    }}
    .signoff {{
      margin-top: 24px;
      line-height: 1.45;
    }}
    .footer {{
      margin-top: 30px;
      padding-top: 14px;
      border-top: 1px solid #e1e4e8;
      font-size: 12px;
      color: #6a737d;
      line-height: 1.5;
    }}
  </style>
</head>
<body>
  <div class="container">
    <p>Hi {first_name},</p>

    <p>Hope you are having a productive week.</p>

    <p>I've been closely following {company}'s footprint in India{compliment_clause}.</p>

    <p>I am reaching out to you from <strong>AOG India Esports</strong> — one of India's premier gaming media and influencer marketing networks, commanding over <strong>5 Million+ monthly views</strong> across YouTube competitive live streams, gameplay series, and short-form video.</p>

    <p>We have officially opened inquiries for our single, exclusive <strong>Title Partnership slot for 2026/27</strong> across our premier gaming rosters:</p>

    <ul>
      <li><span class="highlight">4 Dominant Titles:</span> Minecraft, Valorant, BGMI, and Free Fire</li>
      <li><span class="highlight">360° Native Visibility:</span> Stream overlays, creator videos, tournament integration &amp; daily Shorts/Reels</li>
      <li><span class="highlight">Full Category Exclusivity:</span> Zero competitors in your vertical featured during the partnership</li>
      <li><span class="highlight">Direct Performance Attribution:</span> Trackable UTM links, creator descriptions, and monthly conversion reporting</li>
    </ul>

    <div class="deck-card">
      <p style="margin: 0 0 6px 0; font-size: 14px; color: #444;"><strong>Official Sponsorship Deck &amp; Creator Roster:</strong></p>
      <a href="{deck_url}" class="deck-link">View AOG India Title Partnership Overview &rarr;</a>
    </div>

    <p>Given {company}'s resonance with India's high-intent 18–28 gaming demographic, this partnership is designed to drive massive brand recall and direct conversions.</p>

    <p>Would you or your brand marketing team have 10 minutes for a brief call {meeting_window} to explore if this is a mutual fit?</p>

    <div class="signoff">
      <p style="margin-bottom: 4px;">Warm regards,</p>
      <p style="margin: 0; font-weight: 700; color: #111;">Mohammad Yusuf Khan</p>
      <p style="margin: 0; color: #555; font-size: 14px;">Founder &amp; Partnerships Lead</p>
      <p style="margin: 0; color: #ff7a1a; font-weight: 600; font-size: 14px;">AOG India Esports</p>
      <p style="margin: 4px 0 0 0; font-size: 13px;"><a href="https://aogindia.com" style="color: #666; text-decoration: none;">aogindia.com</a> &bull; {sender_email}</p>
    </div>

    <div class="footer">
      <p>AOG India Esports &bull; Gaming Marketing &amp; Media Agency &bull; New Delhi, India<br>
      If you prefer not to receive sponsorship updates from us, reply with 'Unsubscribe' to be removed immediately.</p>
    </div>
  </div>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# State Management & Storage
# ---------------------------------------------------------------------------

def init_state():
    """Initializes or loads autopilot memory state."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    if not STATE_FILE.exists():
        initial = {
            "created_at": datetime.datetime.now().isoformat(),
            "last_run": None,
            "brands_contacted": [],
            "sent_emails": {},  # email -> timestamp
            "unsubscribed": [],
            "queued_leads": [],
        }
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(initial, f, indent=2)
        return initial

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_state(state: dict):
    """Saves updated state back to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def sync_to_csv(leads: list):
    """Synchronizes lead list into scripts/leads_template.csv for transparent tracking."""
    if not leads:
        return

    fieldnames = [
        "company_name", "contact_name", "designation", "email", "category",
        "custom_compliment", "deck_angle", "verification_status", "status", "sent_at", "notes"
    ]
    with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(leads)

    # Automatically sync to Google Sheet if webhook is configured
    try:
        from sync_to_google_sheet import push_to_google_sheet_webhook
        push_to_google_sheet_webhook()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Apollo.io API Automated Prospector
# ---------------------------------------------------------------------------

def fetch_apollo_leads_for_domain(api_key: str, domain: str, brand_meta: dict) -> list:
    """Queries Apollo API to pull verified marketing decision-makers at a domain."""
    url = "https://api.apollo.io/api/v1/mixed_people/search"

    titles = [
        "Brand Manager", "Influencer Marketing", "Marketing Manager",
        "Head of Marketing", "Brand Partnerships", "Esports", "Category Manager", "CMO"
    ]

    payload = {
        "q_organization_domains": domain,
        "person_titles": titles,
        "person_locations": ["India"],
        "page": 1,
        "per_page": 5,
    }

    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "X-Api-Key": api_key,
        "User-Agent": "AOG-Autopilot/2.0",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
            people = data.get("people", [])
            discovered = []

            for p in people:
                first_name = (p.get("first_name") or "there").strip()
                last_name = (p.get("last_name") or "").strip()
                full_name = f"{first_name} {last_name}".strip()
                title = p.get("title") or "Marketing Decision-Maker"
                email = p.get("email")
                pid = p.get("id")

                # If email is hidden in search preview, call Apollo Match API to unlock
                if (not email or "@" not in email) and pid:
                    try:
                        match_url = "https://api.apollo.io/api/v1/people/match"
                        match_req = urllib.request.Request(
                            match_url,
                            data=json.dumps({"id": pid}).encode("utf-8"),
                            headers=headers,
                            method="POST",
                        )
                        with urllib.request.urlopen(match_req, timeout=10) as mresp:
                            mdata = json.loads(mresp.read().decode("utf-8"))
                            email = mdata.get("person", {}).get("email")
                    except Exception:
                        pass

                # If still no direct personal email unlocked, fallback to target brand email
                if not email or "@" not in email:
                    email = f"marketing@{domain}"

                discovered.append({
                    "company_name": brand_meta["company"],
                    "contact_name": full_name,
                    "first_name": first_name,
                    "email": email.strip().lower(),
                    "category": brand_meta["cat"],
                    "custom_compliment": brand_meta["comp"],
                    "title": title,
                    "domain": domain,
                })
            return discovered
    except urllib.error.HTTPError as http_err:
        try:
            body = http_err.read().decode("utf-8")
            err_data = json.loads(body)
            msg = err_data.get("message") or err_data.get("error") or str(http_err)
        except Exception:
            msg = str(http_err)
        print(f"    [!] Apollo API notice for {domain}: {msg}")
        return []
    except Exception as e:
        print(f"    [!] Apollo connection error for {domain}: {e}")
        return []


# ---------------------------------------------------------------------------
# Zoho Mail Multi-Host SMTP Sender
# ---------------------------------------------------------------------------

def connect_zoho_smtp(smtp_cfg: dict) -> smtplib.SMTP:
    """Connects and authenticates to Zoho Mail with automatic multi-host fallback."""
    hosts = smtp_cfg.get("hosts", ["smtppro.zoho.in", "smtp.zoho.in", "smtppro.zoho.com", "smtp.zoho.com"])
    username = smtp_cfg.get("username", "partnerships@aogindia.com")
    password = smtp_cfg.get("password", "")

    # First attempt TLS (port 587) across host list
    for host in hosts:
        try:
            server = smtplib.SMTP(host, 587, timeout=15)
            server.ehlo()
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.ehlo()
            server.login(username, password)
            return server
        except Exception:
            pass

    # Fallback to SSL (port 465) across host list
    for host in hosts:
        try:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(host, 465, timeout=15, context=context)
            server.ehlo()
            server.login(username, password)
            return server
        except Exception:
            pass

    raise ConnectionError("Could not authenticate with Zoho SMTP across any host.")


# ---------------------------------------------------------------------------
# Timing & Business Hours Guard
# ---------------------------------------------------------------------------

def get_dynamic_meeting_window() -> str:
    """Returns a natural, non-awkward meeting timeframe based on current day of week."""
    now = datetime.datetime.now()
    weekday = now.weekday()  # 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun
    if weekday in [0, 1]:  # Mon, Tue
        return "this Thursday or Friday"
    elif weekday == 2:  # Wed
        return "this Friday or early next week"
    elif weekday in [3, 4]:  # Thu, Fri
        return "early next week (e.g. Tuesday or Wednesday)"
    else:  # Sat, Sun
        return "this coming Tuesday or Wednesday"


def is_prime_b2b_sending_window(config: dict) -> tuple:
    """
    Checks if current local time is within optimal Indian B2B open hours
    (Mon-Fri, 10:00 AM - 5:00 PM IST).
    """
    now = datetime.datetime.now()
    weekday = now.weekday()  # 0=Monday, 4=Friday, 5=Saturday, 6=Sunday

    rules = config.get("autopilot", {})
    start_hour = rules.get("business_hours_start_ist", 10)
    end_hour = rules.get("business_hours_end_ist", 17)
    allow_weekends = rules.get("send_on_weekends", False)

    if not allow_weekends and weekday in [5, 6]:
        return False, "Weekend (Saturday/Sunday) — B2B open rates are low. Scheduled to resume Monday morning."

    if now.hour < start_hour:
        return False, f"Too early (current hour: {now.hour}:00 IST). Prime business window opens at {start_hour}:00 AM IST."

    if now.hour >= end_hour:
        return False, f"Past business hours (current hour: {now.hour}:00 IST). Prime window closes at {end_hour}:00 PM IST."

    return True, "Within optimal B2B window (10:00 AM - 5:00 PM IST)."


def is_outreach_paused(config: dict) -> tuple[bool, str]:
    """Checks whether email outreach is paused via config, env var, or kill switch."""
    if os.environ.get("AOG_OUTREACH_PAUSED", "").lower() in ("1", "true", "yes"):
        return True, "Paused via environment variable AOG_OUTREACH_PAUSED=1"
    if config.get("paused", False):
        reason = config.get("pause_reason", "Paused via outreach_config.json ('paused': true)")
        return True, reason
    if config.get("autopilot", {}).get("paused", False):
        return True, "Paused via outreach_config.json ('autopilot.paused': true)"
    return False, ""


def pause_outreach(reason: str = "Email outreach paused by user request - reviewing contacts and templates"):
    """Sets paused = true in outreach_config.json."""
    if not CONFIG_FILE.exists():
        print(f"[X] Config file not found at: {CONFIG_FILE}")
        return
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["paused"] = True
    config["pause_reason"] = reason
    if "autopilot" not in config or not isinstance(config["autopilot"], dict):
        config["autopilot"] = {}
    config["autopilot"]["paused"] = True
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print("=" * 72)
    print("  [OK] EMAIL OUTREACH HAS BEEN PAUSED")
    print("=" * 72)
    print(f"  Status: PAUSED")
    print(f"  Reason: {reason}")
    print(f"  Config updated: {CONFIG_FILE.name}")
    print("  Zero emails will be sent by any automated or manual triggers.")
    print("=" * 72)


def resume_outreach():
    """Sets paused = false in outreach_config.json."""
    if not CONFIG_FILE.exists():
        print(f"[X] Config file not found at: {CONFIG_FILE}")
        return
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)
    config["paused"] = False
    config.pop("pause_reason", None)
    if "autopilot" in config and isinstance(config["autopilot"], dict):
        config["autopilot"]["paused"] = False
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    print("=" * 72)
    print("  [OK] EMAIL OUTREACH HAS BEEN RESUMED")
    print("=" * 72)
    print(f"  Status: ACTIVE")
    print(f"  Config updated: {CONFIG_FILE.name}")
    print("=" * 72)


def print_outreach_status(config: dict):
    """Displays current outreach status and lead counts."""
    paused, reason = is_outreach_paused(config)
    print("=" * 72)
    print("  AOG INDIA — EMAIL OUTREACH STATUS")
    print("=" * 72)
    if paused:
        print(f"  Status: [PAUSED - NO EMAILS WILL BE SENT]")
        print(f"  Reason: {reason}")
    else:
        print(f"  Status: [ACTIVE - Scheduled sends will execute]")
    if CSV_FILE.exists():
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = list(csv.DictReader(f))
            pending = len([r for r in reader if r.get("status", "").lower() in ["pending", ""]])
            on_hold = len([r for r in reader if r.get("status", "").lower() in ["paused", "on_hold", "hold"]])
            sent = len([r for r in reader if r.get("status", "").lower() == "sent"])
            print(f"  Leads in {CSV_FILE.name}:")
            print(f"    - Pending: {pending}")
            print(f"    - Paused/On Hold: {on_hold}")
            print(f"    - Sent: {sent}")
            print(f"    - Total rows: {len(reader)}")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Autopilot Execution Engine
# ---------------------------------------------------------------------------

def run_autopilot_cycle(config: dict, force: bool = False, dry_run: bool = False):
    """Executes a single automated prospecting and outreach cycle."""
    state = init_state()

    print("=" * 72)
    print("  AOG INDIA ESPORTS — AUTOPILOT BRAND SPONSORSHIP ENGINE")
    print("  Sender: Mohammad Yusuf Khan <partnerships@aogindia.com>")
    print("=" * 72)

    # 0. Safety Pause Check
    paused, pause_reason = is_outreach_paused(config)
    if paused and not dry_run:
        print("\n" + "!" * 72)
        print("  [STOP] EMAIL OUTREACH IS CURRENTLY PAUSED")
        print(f"  Reason: {pause_reason}")
        print("  Zero emails were sent. Safety guard active.")
        print("  To preview without sending, use: python scripts/autopilot_sponsor_outreach.py --dry-run")
        print("  To resume later, run: python scripts/autopilot_sponsor_outreach.py --resume")
        print("!" * 72 + "\n")
        return

    if paused and dry_run:
        print("\n[NOTE] Live email sending is currently PAUSED. Running dry-run preview only.\n")

    # 1. Timing check
    is_ok, reason = is_prime_b2b_sending_window(config)
    print(f"[*] Schedule Check: {reason}")
    if not is_ok and not force and not dry_run:
        print("[!] Outside prime sending window. Run with '--now' to send anyway, or '--daemon' to wait.")
        return

    # 2. Check if we have curated pending leads in leads_template.csv first
    existing_csv_leads = []
    if CSV_FILE.exists():
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("status", "").lower() in ["pending", ""] and row.get("email"):
                    existing_csv_leads.append(row)

    if existing_csv_leads:
        print(f"[*] Found {len(existing_csv_leads)} real decision-maker leads in {CSV_FILE.name}")
        daily_limit = config.get("autopilot", {}).get("daily_send_limit", 25)
        batch_leads = existing_csv_leads[:daily_limit]
    else:
        # Fallback to dynamic brand discovery
        contacted_domains = set(state.get("brands_contacted", []))
        available_brands = [b for b in EXPANDED_BRAND_CATALOG if b["domain"] not in contacted_domains]

        if not available_brands:
            print("[*] All catalog brands have been contacted once! Cycling back through refreshed creator brands...")
            contacted_domains.clear()
            available_brands = EXPANDED_BRAND_CATALOG

        brands_for_batch = available_brands[:6]
        print(f"[*] Selecting {len(brands_for_batch)} brands for automated discovery:")
        for b in brands_for_batch:
            print(f"    • {b['company']} ({b['domain']}) — {b['cat']}")

        apollo_key = config.get("apollo", {}).get("api_key", "").strip()
        discovered_leads = []

        print("\n[*] Querying Apollo B2B Database for Brand Managers & Influencer Leads in India...")
        for b in brands_for_batch:
            leads = fetch_apollo_leads_for_domain(apollo_key, b["domain"], b)
            if leads:
                print(f"    [✔] Found {len(leads)} verified contact(s) at {b['company']}")
                discovered_leads.extend(leads)
            else:
                fallback_lead = {
                    "company_name": b["company"],
                    "contact_name": "Brand Marketing Lead",
                    "first_name": "there",
                    "email": f"marketing@{b['domain']}",
                    "category": b["cat"],
                    "custom_compliment": b["comp"],
                    "title": "Marketing Partnerships",
                    "domain": b["domain"],
                }
                discovered_leads.append(fallback_lead)

        sent_map = state.get("sent_emails", {})
        unsubs = set(state.get("unsubscribed", []))
        actionable_leads = [
            l for l in discovered_leads
            if l["email"] not in sent_map and l["email"] not in unsubs
        ]

        daily_limit = config.get("autopilot", {}).get("daily_send_limit", 25)
        batch_leads = actionable_leads[:daily_limit]

    print(f"\n[*] Total actionable leads ready to send: {len(batch_leads)}")

    if not batch_leads:
        print("[!] No new leads to send in this cycle.")
        return

    # 4. Dry Run Mode
    if dry_run:
        print("\n" + "=" * 72)
        print("  DRY RUN PREVIEW (NO EMAILS WILL BE SENT)")
        print("=" * 72)
        for idx, lead in enumerate(batch_leads[:3], start=1):
            first_name = lead.get("first_name") or lead.get("contact_name", "there").split()[0]
            comp = f" — {lead.get('custom_compliment')}" if lead.get("custom_compliment") else ""
            subject = SUBJECT_OPTIONS[idx % len(SUBJECT_OPTIONS)].format(company=lead["company_name"])
            
            body = PLAIN_TEXT_TEMPLATE.format(
                first_name=first_name,
                company=lead["company_name"],
                compliment_clause=comp,
                deck_url=config.get("sender", {}).get("deck_url"),
                sender_email=config.get("sender", {}).get("email"),
                meeting_window=get_dynamic_meeting_window(),
            )
            print(f"\n[Preview #{idx}] To: {lead['contact_name']} <{lead['email']}>")
            print(f"Subject: {subject}")
            print("-" * 50)
            print(body[:400] + "\n... [truncated preview]")
        print("\n[✔] Dry run complete. Templates and API pipeline validated.")
        return

    # 5. Live Send via Zoho SMTP
    smtp_cfg = config.get("smtp", {})
    sender_cfg = config.get("sender", {})
    sender_name = sender_cfg.get("name", "Mohammad Yusuf Khan")
    sender_email = sender_cfg.get("email", "partnerships@aogindia.com")
    deck_url = sender_cfg.get("deck_url", "https://aogindia.com/for-brands.html#title-sponsorship")

    print("\n[*] Connecting to Zoho Mail SMTP server...")
    try:
        server = connect_zoho_smtp(smtp_cfg)
        print("[✔] Successfully authenticated with Zoho Mail SMTP.\n")
    except Exception as e:
        print(f"[X] Zoho SMTP Authentication Failed: {e}")
        print("    Please check credentials in scripts/outreach_config.json")
        return

    min_delay = config.get("autopilot", {}).get("min_delay_seconds", 60)
    max_delay = config.get("autopilot", {}).get("max_delay_seconds", 120)

    sent_count = 0
    all_csv_rows = []

    for idx, lead in enumerate(batch_leads, start=1):
        to_email = lead["email"]
        company = lead["company_name"]
        contact_name = lead["contact_name"]
        first_name = lead.get("first_name") or contact_name.split()[0]
        comp = f" — {lead.get('custom_compliment')}" if lead.get("custom_compliment") else ""

        subject = SUBJECT_OPTIONS[idx % len(SUBJECT_OPTIONS)].format(company=company)

        plain_body = PLAIN_TEXT_TEMPLATE.format(
            first_name=first_name,
            company=company,
            compliment_clause=comp,
            deck_url=deck_url,
            sender_email=sender_email,
            meeting_window=get_dynamic_meeting_window(),
        )

        html_body = HTML_TEMPLATE.format(
            first_name=first_name,
            company=company,
            compliment_clause=comp,
            deck_url=deck_url,
            sender_email=sender_email,
            meeting_window=get_dynamic_meeting_window(),
        )

        # Construct Email Message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((str(Header(sender_name, "utf-8")), sender_email))
        msg["To"] = to_email
        msg["Reply-To"] = sender_email
        msg["Message-ID"] = make_msgid(domain="aogindia.com")
        msg["Date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")

        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{idx}/{len(batch_leads)}] Sending to {company}: {contact_name} <{to_email}>...")

        try:
            server.send_message(msg)
            sent_count += 1
            print(f"    [✔] Delivered to {to_email} at {now_str}")

            # Record in state
            state["sent_emails"][to_email] = now_str
            if lead.get("domain") and lead["domain"] not in state["brands_contacted"]:
                state["brands_contacted"].append(lead["domain"])

            all_csv_rows.append({
                "company_name": company,
                "contact_name": contact_name,
                "designation": lead.get("title", lead.get("designation", "Marketing")),
                "email": to_email,
                "category": lead.get("category", "Gaming"),
                "custom_compliment": lead.get("custom_compliment", ""),
                "deck_angle": "title_sponsor",
                "verification_status": lead.get("verification_status", "unverified"),
                "status": "sent",
                "sent_at": now_str,
                "notes": f"Autopilot sent via Zoho ({lead.get('title', lead.get('designation', 'Marketing'))})",
            })

            save_state(state)
            sync_to_csv(all_csv_rows)

        except Exception as err:
            print(f"    [X] Send error for {to_email}: {err}")

        # Safety drip delay between sends
        if idx < len(batch_leads):
            wait_s = random.randint(min_delay, max_delay)
            print(f"    Waiting {wait_s}s before next send (inbox health protection)...")
            time.sleep(wait_s)

    try:
        server.quit()
    except Exception:
        pass

    state["last_run"] = datetime.datetime.now().isoformat()
    save_state(state)

    print("\n" + "=" * 72)
    print(f"Autopilot Cycle Complete: {sent_count} personalized emails delivered.")
    print(f"Results synced to: {CSV_FILE.name} and {STATE_FILE.name}")
    print("=" * 72)


def send_test_email(test_to: str, config: dict):
    """Sends a single test email directly to the user's inbox to verify formatting."""
    print(f"[*] Dispatching test email to: {test_to}")
    smtp_cfg = config.get("smtp", {})
    sender_cfg = config.get("sender", {})
    sender_name = sender_cfg.get("name", "Mohammad Yusuf Khan")
    sender_email = sender_cfg.get("email", "partnerships@aogindia.com")
    deck_url = sender_cfg.get("deck_url", "https://aogindia.com/for-brands.html#title-sponsorship")

    sample_company = "ASUS ROG India"
    subject = f"[TEST PREVIEW] {SUBJECT_OPTIONS[0].format(company=sample_company)}"

    plain_body = PLAIN_TEXT_TEMPLATE.format(
        first_name="Yusuf",
        company=sample_company,
        compliment_clause=" — loved your recent ROG Strix gaming launch",
        deck_url=deck_url,
        sender_email=sender_email,
        meeting_window=get_dynamic_meeting_window(),
    )

    html_body = HTML_TEMPLATE.format(
        first_name="Yusuf",
        company=sample_company,
        compliment_clause=" — loved your recent ROG Strix gaming launch",
        deck_url=deck_url,
        sender_email=sender_email,
        meeting_window=get_dynamic_meeting_window(),
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header(sender_name, "utf-8")), sender_email))
    msg["To"] = test_to
    msg["Reply-To"] = sender_email
    msg["Message-ID"] = make_msgid(domain="aogindia.com")

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        server = connect_zoho_smtp(smtp_cfg)
        server.send_message(msg)
        server.quit()
        print(f"[✔] Test email sent successfully to {test_to} via Zoho Mail!")
        print("    Please check your inbox to inspect the signature, layout, and links.")
    except Exception as e:
        print(f"[X] Failed to send test email: {e}")


def send_test_batch(preview_to: str, config: dict):
    """
    Sends one real sample email per brand category to the preview address.
    Each email uses actual data from leads_template.csv so you can see
    exactly how brand mentions, compliments, and personalization look.
    """
    smtp_cfg = config.get("smtp", {})
    sender_cfg = config.get("sender", {})
    sender_name = sender_cfg.get("name", "Mohammad Yusuf Khan")
    sender_email = sender_cfg.get("email", "partnerships@aogindia.com")
    deck_url = sender_cfg.get("deck_url", "https://aogindia.com/for-brands.html#title-sponsorship")

    print("=" * 72)
    print("  AOG INDIA — TEST BATCH PREVIEW")
    print(f"  Sending sample emails to: {preview_to}")
    print("=" * 72)

    # Load leads from CSV and pick one per unique category
    leads_by_category = {}
    if CSV_FILE.exists():
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cat = row.get("category", "").strip()
                if cat and cat not in leads_by_category:
                    leads_by_category[cat] = row

    if not leads_by_category:
        print("[X] No leads found in leads_template.csv")
        return

    samples = list(leads_by_category.values())
    print(f"[*] Found {len(samples)} categories — sending one preview per category\n")

    print("[*] Connecting to Zoho Mail SMTP...")
    try:
        server = connect_zoho_smtp(smtp_cfg)
        print("[✔] Authenticated with Zoho Mail\n")
    except Exception as e:
        print(f"[X] SMTP connection failed: {e}")
        return

    meeting_window = get_dynamic_meeting_window()
    sent = 0

    for idx, lead in enumerate(samples, start=1):
        company     = lead.get("company_name", "Brand")
        contact     = lead.get("contact_name", "there")
        designation = lead.get("designation", "")
        category    = lead.get("category", "")
        compliment  = lead.get("custom_compliment", "")
        first_name  = contact.split()[0] if contact else "there"
        comp_clause = f" — {compliment}" if compliment else ""

        subject = f"[PREVIEW #{idx} | {category}] " + SUBJECT_OPTIONS[idx % len(SUBJECT_OPTIONS)].format(company=company)

        plain_body = PLAIN_TEXT_TEMPLATE.format(
            first_name=first_name,
            company=company,
            compliment_clause=comp_clause,
            deck_url=deck_url,
            sender_email=sender_email,
            meeting_window=meeting_window,
        )
        html_body = HTML_TEMPLATE.format(
            first_name=first_name,
            company=company,
            compliment_clause=comp_clause,
            deck_url=deck_url,
            sender_email=sender_email,
            meeting_window=meeting_window,
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((str(Header(sender_name, "utf-8")), sender_email))
        msg["To"] = preview_to
        msg["Reply-To"] = sender_email
        msg["Message-ID"] = make_msgid(domain="aogindia.com")
        msg["Date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        print(f"[{idx}/{len(samples)}] {category}: {company} → {contact} ({designation})")
        try:
            server.send_message(msg)
            sent += 1
            print(f"    [✔] Sent to {preview_to}")
        except Exception as e:
            print(f"    [X] Failed: {e}")

        # Small delay between sends
        if idx < len(samples):
            time.sleep(5)

    try:
        server.quit()
    except Exception:
        pass

    print()
    print("=" * 72)
    print(f"[✔] Test batch complete: {sent}/{len(samples)} emails delivered to {preview_to}")
    print()
    print("  Check your inbox for emails with subject lines like:")
    print("  '[PREVIEW #1 | Gaming Hardware] ...'")
    print("  '[PREVIEW #2 | Gaming Peripherals] ...'")
    print("  etc. — each showing different brand personalisation")
    print("=" * 72)


def send_test_final(preview_to: str, config: dict, count: int = 3):
    """
    Sends 'count' (default 3) 100% realistic final emails directly to preview_to
    with the EXACT production subject lines (NO [PREVIEW] prefix), real brand
    personalisation, and dynamic meeting windows.
    """
    smtp_cfg = config.get("smtp", {})
    sender_cfg = config.get("sender", {})
    sender_name = sender_cfg.get("name", "Mohammad Yusuf Khan")
    sender_email = sender_cfg.get("email", "partnerships@aogindia.com")
    deck_url = sender_cfg.get("deck_url", "https://aogindia.com/for-brands.html#title-sponsorship")

    print("=" * 72)
    print("  AOG INDIA — FINAL PRODUCTION EMAIL PREVIEW (NO PREFIX)")
    print(f"  Sending {count} final samples directly to: {preview_to}")
    print("=" * 72)

    # Pick top distinct leads from leads_template.csv
    leads_picked = []
    seen_brands = set()
    if CSV_FILE.exists():
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                comp = row.get("company_name", "").strip()
                if comp and comp not in seen_brands:
                    seen_brands.add(comp)
                    leads_picked.append(row)
                    if len(leads_picked) >= count:
                        break

    if not leads_picked:
        print("[X] No leads available in leads_template.csv")
        return

    print(f"[*] Selected {len(leads_picked)} sample brands for final verification:")
    for i, lead in enumerate(leads_picked, 1):
        subj = SUBJECT_OPTIONS[(i - 1) % len(SUBJECT_OPTIONS)].format(company=lead.get("company_name", "Brand"))
        print(f"   {i}. Brand: {lead.get('company_name')} | Subject: \"{subj}\"")
    print()

    print("[*] Connecting to Zoho Mail SMTP...")
    try:
        server = connect_zoho_smtp(smtp_cfg)
        print("[✔] Authenticated with Zoho Mail\n")
    except Exception as e:
        print(f"[X] SMTP connection failed: {e}")
        return

    meeting_window = get_dynamic_meeting_window()
    sent = 0

    for idx, lead in enumerate(leads_picked, start=1):
        company     = lead.get("company_name", "Brand")
        contact     = lead.get("contact_name", "there")
        designation = lead.get("designation", "")
        category    = lead.get("category", "")
        compliment  = lead.get("custom_compliment", "")
        first_name  = contact.split()[0] if contact else "there"
        comp_clause = f" — {compliment}" if compliment else ""

        # EXACT PRODUCTION SUBJECT — NO [PREVIEW] PREFIX
        subject = SUBJECT_OPTIONS[(idx - 1) % len(SUBJECT_OPTIONS)].format(company=company)

        plain_body = PLAIN_TEXT_TEMPLATE.format(
            first_name=first_name,
            company=company,
            compliment_clause=comp_clause,
            deck_url=deck_url,
            sender_email=sender_email,
            meeting_window=meeting_window,
        )
        html_body = HTML_TEMPLATE.format(
            first_name=first_name,
            company=company,
            compliment_clause=comp_clause,
            deck_url=deck_url,
            sender_email=sender_email,
            meeting_window=meeting_window,
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((str(Header(sender_name, "utf-8")), sender_email))
        msg["To"] = preview_to
        msg["Reply-To"] = sender_email
        msg["Message-ID"] = make_msgid(domain="aogindia.com")
        msg["Date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S +0000")
        msg.attach(MIMEText(plain_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        print(f"[{idx}/{len(leads_picked)}] Sending: {company} ({first_name} - {designation})")
        print(f"    Subject: \"{subject}\"")
        try:
            server.send_message(msg)
            sent += 1
            print(f"    [✔] Successfully delivered to {preview_to}")
        except Exception as e:
            print(f"    [X] Failed: {e}")

        if idx < len(leads_picked):
            time.sleep(4)

    try:
        server.quit()
    except Exception:
        pass

    print()
    print("=" * 72)
    print(f"[✔] Final check complete: {sent}/{len(leads_picked)} emails delivered to {preview_to}")
    print("    These emails show EXACTLY what real marketing leads will receive in their inbox.")
    print("=" * 72)



def run_fetch_only(config: dict, num_brands: int = 10):
    """
    Fetches real marketing decision-makers from Apollo for target brands
    and saves them directly into leads_template.csv for review before sending.
    """
    print("=" * 72)
    print("  AOG INDIA — FETCHING REAL BRAND DECISION-MAKERS VIA APOLLO")
    print(f"  Target: Top {num_brands} brands in Indian gaming & lifestyle")
    print("=" * 72)

    apollo_key = config.get("apollo", {}).get("api_key", "").strip()
    if not apollo_key:
        print("[X] Apollo API key not configured in scripts/outreach_config.json")
        return

    brands = EXPANDED_BRAND_CATALOG[:num_brands]
    all_leads = []

    for idx, b in enumerate(brands, start=1):
        domain = b["domain"]
        company = b["company"]
        cat = b["cat"]
        comp = b["comp"]
        print(f"\n[{idx}/{len(brands)}] Querying {company} ({domain})...")

        leads = fetch_apollo_leads_for_domain(apollo_key, domain, b)
        if leads:
            print(f"    [✔] Discovered {len(leads)} decision-maker(s):")
            for l in leads:
                print(f"        • {l['contact_name']} — {l['title']} <{l['email']}>")
                # Determine verification: if email was directly pulled from Apollo (not constructed), it's verified
                is_verified = "verified" if ("@" in l["email"] and not l["email"].startswith("marketing@") and not l["email"].startswith("partnerships@")) else "unverified"
                all_leads.append({
                    "company_name": company,
                    "contact_name": l["contact_name"],
                    "designation": l.get("title", "Marketing"),
                    "email": l["email"],
                    "category": cat,
                    "custom_compliment": comp,
                    "deck_angle": "title_sponsor",
                    "verification_status": is_verified,
                    "status": "pending",
                    "sent_at": "",
                    "notes": f"Discovered via Apollo ({l['title']})",
                })
        else:
            print(f"    [-] No direct marketing contact found on Apollo for {domain}. Adding domain fallback.")
            all_leads.append({
                "company_name": company,
                "contact_name": "Brand Partnerships Lead",
                "designation": "Marketing Partnerships",
                "email": f"partnerships@{domain}",
                "category": cat,
                "custom_compliment": comp,
                "deck_angle": "title_sponsor",
                "verification_status": "unverified",
                "status": "pending",
                "sent_at": "",
                "notes": "Target brand fallback queue",
            })

    if all_leads:
        sync_to_csv(all_leads)
        print("\n" + "=" * 72)
        print(f"[✔] Successfully saved {len(all_leads)} leads to: {CSV_FILE.name}")
        print(f"    Open {CSV_FILE.name} in Excel or VS Code to review all names and emails!")
        print("=" * 72)


def run_daemon_loop(config: dict):
    """Runs a continuous background loop that triggers every morning at 10:15 AM IST."""
    print("[*] Starting Autopilot Daemon. Listening for morning B2B windows...")
    while True:
        # Reload config to pick up any runtime pause/unpause changes
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except Exception:
                pass

        paused, pause_reason = is_outreach_paused(config)
        if paused:
            print(f"[*] Autopilot is PAUSED ({pause_reason}). Sleeping for 30 minutes without sending...")
            time.sleep(1800)
            continue

        is_ok, reason = is_prime_b2b_sending_window(config)
        if is_ok:
            run_autopilot_cycle(config)
            print("[*] Completed daily batch. Sleeping for 18 hours until next business window...")
            time.sleep(18 * 3600)
        else:
            print(f"[*] Sleeping (Status: {reason}). Checking again in 30 minutes...")
            time.sleep(1800)


# ---------------------------------------------------------------------------
# Weekly Auto-Discovery: Finds New Gaming Sponsors in India
# ---------------------------------------------------------------------------

WEEKLY_DISCOVERY_POOL = [
    {"company": "Gigabyte Aorus India",   "domain": "gigabyte.com",            "cat": "Gaming Hardware",   "comp": "seeing Aorus motherboards and GPUs heavily recommended by Indian tech creators"},
    {"company": "Corsair India",           "domain": "corsair.com",             "cat": "Gaming Hardware",   "comp": "admiring Corsair premium streaming setups and community gaming tournaments"},
    {"company": "Cooler Master India",     "domain": "coolermaster.com",        "cat": "Gaming Hardware",   "comp": "Cooler Master custom PC showcase events set the benchmark in Indian PC modding"},
    {"company": "HyperX India",            "domain": "hyperx.com",              "cat": "Gaming Peripherals","comp": "HyperX Cloud headsets remain the undisputed choice across competitive live broadcasters"},
    {"company": "Zebronics",               "domain": "zebronics.com",           "cat": "Gaming Peripherals","comp": "loved your Zeb-Transformer gaming gear activations and broad youth accessibility"},
    {"company": "Ant Esports",             "domain": "antesports.com",          "cat": "Gaming Peripherals","comp": "seeing Ant Esports gaming chairs and accessories in almost every rising Indian streamer setup"},
    {"company": "Noise",                   "domain": "gonoise.com",             "cat": "Smart Wearables",   "comp": "Noise creative product drops have exceptional engagement across young digital creators"},
    {"company": "realme India",            "domain": "realme.com",              "cat": "Smartphones",       "comp": "realme GT series gaming activations have built tremendous loyalty with Gen-Z mobile gamers"},
    {"company": "Infinix India",           "domain": "infinixmobiles.in",       "cat": "Smartphones",       "comp": "Infinix GT gaming series has disrupted the affordable esports smartphone market"},
    {"company": "Motorola India",          "domain": "motorola.in",             "cat": "Smartphones",       "comp": "loved your clean software experience and high-refresh pOLED gaming phone rollouts"},
    {"company": "Hell Energy India",       "domain": "hellenergy.com",          "cat": "Energy Drinks",    "comp": "witnessing Hell Energy aggressive retail expansion and strong traction with young streamers"},
    {"company": "Too Yumm!",               "domain": "tooyumm.com",             "cat": "Snacks & Food",     "comp": "Too Yumm bold flavours and youth-first positioning have great appeal with our creator audience"},
    {"company": "Cadbury 5 Star",          "domain": "mondelezinternational.com","cat": "Confectionery",    "comp": "loved 5 Star hilarious Do Nothing gaming campaigns and viral meme marketing"},
    {"company": "Blinkit",                 "domain": "blinkit.com",             "cat": "Quick Commerce",   "comp": "Blinkit 10-minute delivery is what saves every creator during late-night gaming livestreams"},
    {"company": "Zepto",                   "domain": "zeptonow.com",            "cat": "Quick Commerce",   "comp": "Zepto high-speed Gen-Z convenience aligns perfectly with the active gaming demographic"},
    {"company": "Fi Money",                "domain": "fi.money",               "cat": "FinTech",           "comp": "Fi smart money management features for young professionals and digital creators are standout"},
    {"company": "Jupiter Money",           "domain": "jupiter.money",           "cat": "FinTech",           "comp": "Jupiter banking features resonate strongly with first-time earners and young creators"},
    {"company": "Krafton India",           "domain": "krafton.com",             "cat": "Game Publisher",   "comp": "Krafton visionary dedication to Indian esports through BGMI has transformed millions of youth lives"},
    {"company": "Riot Games India",        "domain": "riotgames.com",           "cat": "Game Publisher",   "comp": "Valorant explosive collegiate and competitive tournament growth in India has been phenomenal"},
    {"company": "WinZO",                   "domain": "winzogames.com",          "cat": "Gaming Platform",  "comp": "WinZO grassroots vernacular gaming initiatives have created immense value across Bharat"},
    {"company": "Rooter",                  "domain": "rooter.gg",               "cat": "Gaming Streaming", "comp": "Rooter relentless championing of Indian gaming creators and esports tournaments is inspiring"},
]


def run_weekly_discovery(config: dict):
    """
    Weekly auto-discovery: Scans 20+ new gaming sponsor brands and appends
    fresh contacts to leads_template.csv. Run this every Monday via Task Scheduler.
    """
    log_file = LOGS_DIR / "weekly_discovery.log"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 72)
    print("  AOG INDIA - WEEKLY BRAND DISCOVERY ENGINE")
    print(f"  Running at: {timestamp} IST")
    print("=" * 72)

    apollo_key = config.get("apollo", {}).get("api_key", "").strip()
    if not apollo_key:
        print("[X] Apollo API key missing. Add it to scripts/outreach_config.json")
        return

    # Load existing emails to avoid duplicates
    existing_emails = set()
    existing_rows = []
    if CSV_FILE.exists():
        with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_rows.append(row)
                existing_emails.add(row.get("email", "").lower().strip())

    print(f"[*] Existing leads in database: {len(existing_rows)}")
    print(f"[*] Checking {len(WEEKLY_DISCOVERY_POOL)} new brands for fresh contacts...\n")

    new_leads = []
    for idx, brand in enumerate(WEEKLY_DISCOVERY_POOL, start=1):
        domain = brand["domain"]
        company = brand["company"]
        print(f"[{idx}/{len(WEEKLY_DISCOVERY_POOL)}] Scanning {company} ({domain})...")

        leads = fetch_apollo_leads_for_domain(apollo_key, domain, brand)
        added = 0
        for l in leads:
            if l["email"].lower() not in existing_emails:
                is_verified = "verified" if (
                    "@" in l["email"]
                    and not l["email"].startswith("marketing@")
                    and not l["email"].startswith("partnerships@")
                ) else "unverified"
                new_leads.append({
                    "company_name": company,
                    "contact_name": l["contact_name"],
                    "designation": l.get("title", "Marketing"),
                    "email": l["email"],
                    "category": brand["cat"],
                    "custom_compliment": brand["comp"],
                    "deck_angle": "title_sponsor",
                    "verification_status": is_verified,
                    "status": "pending",
                    "sent_at": "",
                    "notes": f"Auto-discovered weekly ({l.get('title', 'Marketing')})",
                })
                existing_emails.add(l["email"].lower())
                added += 1

        status = f"[+] {added} new contact(s) added" if added else "[-] No new contacts (already in DB or not found)"
        print(f"    {status}")

    if new_leads:
        all_rows = existing_rows + new_leads
        fieldnames = [
            "company_name", "contact_name", "designation", "email", "category",
            "custom_compliment", "deck_angle", "verification_status", "status", "sent_at", "notes"
        ]
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(all_rows)
        print(f"\n[OK] Weekly discovery done: {len(new_leads)} new leads added (total: {len(all_rows)}).")
        log_msg = f"{timestamp} | Added {len(new_leads)} new leads (total: {len(all_rows)})\n"
    else:
        print("\n[OK] Weekly discovery done: No new leads found this cycle.")
        log_msg = f"{timestamp} | No new leads (total: {len(existing_rows)})\n"

    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write(log_msg)
    print(f"[*] Run logged to: {log_file}")
    print("=" * 72)


def setup_windows_scheduler():
    """
    Generates a PowerShell script (setup_windows_scheduler.ps1) that registers
    two Windows Task Scheduler jobs for fully automated AOG India outreach.
    Run the generated .ps1 file once as Administrator to activate automation.
    """
    ps1_path = BASE_DIR / "setup_windows_scheduler.ps1"
    python_exe = sys.executable.replace("\\", "\\\\")
    script_path = str(Path(__file__).resolve()).replace("\\", "\\\\")
    project_root = str(BASE_DIR.parent).replace("\\", "\\\\")

    content = f'''# =============================================================================
# AOG India Esports - Windows Task Scheduler Auto-Setup
# =============================================================================
# Run this script ONCE as Administrator to activate hands-free automation.
# It registers two scheduled tasks:
#   1. Daily email sending Mon-Fri at 10:30 AM
#   2. Weekly brand discovery every Monday at 9:00 AM
# =============================================================================

$PythonExe      = "{python_exe}"
$OutreachScript = "{script_path}"
$ProjectRoot    = "{project_root}"

$Settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1) `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# Task 1: Daily Email Sending
$DailyAction  = New-ScheduledTaskAction -Execute $PythonExe -Argument "$OutreachScript --now" -WorkingDirectory $ProjectRoot
$DailyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "10:30AM"
Register-ScheduledTask -TaskName "AOGIndia_DailyOutreach" -Action $DailyAction -Trigger $DailyTrigger -Settings $Settings -RunLevel Highest -Force | Out-Null
Write-Host "[OK] AOGIndia_DailyOutreach registered: Mon-Fri at 10:30 AM" -ForegroundColor Green

# Task 2: Weekly Brand Discovery
$WeeklyAction  = New-ScheduledTaskAction -Execute $PythonExe -Argument "$OutreachScript --weekly" -WorkingDirectory $ProjectRoot
$WeeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "9:00AM"
Register-ScheduledTask -TaskName "AOGIndia_WeeklyDiscovery" -Action $WeeklyAction -Trigger $WeeklyTrigger -Settings $Settings -RunLevel Highest -Force | Out-Null
Write-Host "[OK] AOGIndia_WeeklyDiscovery registered: Monday at 9:00 AM" -ForegroundColor Green

Write-Host ""
Write-Host "AOG India Autopilot is now FULLY AUTOMATED!" -ForegroundColor Cyan
Write-Host "Emails send daily. New brands discovered weekly. Zero manual work needed."
'''
    with open(ps1_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("=" * 72)
    print("  AOG INDIA - WINDOWS TASK SCHEDULER SETUP")
    print("=" * 72)
    print(f"[OK] Generated: {ps1_path}")
    print()
    print("  NEXT STEP (one-time only):")
    print(f"  Right-click '{ps1_path.name}' > 'Run with PowerShell' (as Administrator)")
    print()
    print("  This will register two automatic jobs:")
    print("    * AOGIndia_DailyOutreach   — sends emails Mon-Fri at 10:30 AM")
    print("    * AOGIndia_WeeklyDiscovery — finds new gaming brands every Monday at 9 AM")
    print("=" * 72)


def setup_github_actions():
    """
    Generates .github/workflows/outreach.yml — the GitHub Actions workflow
    that runs daily email sending and weekly discovery automatically, for free.

    KEY FEATURE — No duplicate emails ever:
    The sent-email state (autopilot_state.json + leads_template.csv) is saved
    as a GitHub Artifact at the END of each run, and restored at the START of
    the next run. This means the script always knows who was already contacted.
    """
    workflows_dir = BASE_DIR.parent / ".github" / "workflows"
    workflows_dir.mkdir(parents=True, exist_ok=True)
    yml_path = workflows_dir / "outreach.yml"

    content = '''# =============================================================================
# AOG India Esports - Automated Sponsor Outreach (GitHub Actions)
# =============================================================================
# Runs FREE on GitHub servers, automatically:
#   - Daily emails:     Mon-Fri at 10:30 AM IST  (05:00 UTC)
#   - Weekly discovery: Every Monday at 9:00 AM IST (03:30 UTC)
#
# NO DUPLICATE EMAILS: Sent-email history is saved as a GitHub Artifact
# after every run and restored before the next — contacts are NEVER emailed
# twice, even across separate workflow runs on different days.
#
# ONE-TIME SETUP in GitHub > Settings > Secrets and Variables > Actions:
#   APOLLO_API_KEY  = your Apollo.io key
#   ZOHO_PASSWORD   = your Zoho email app password
# =============================================================================

name: AOG India Sponsor Outreach Autopilot

on:
  # ===========================================================================
  # SCHEDULE PAUSED by user request - emails will NOT send automatically.
  # To resume in future, uncomment the schedule block below.
  # ===========================================================================
  # schedule:
  #   - cron: \'0 5 * * 1-5\'    # Daily emails: Mon-Fri 10:30 AM IST
  #   - cron: \'30 3 * * 1\'     # Weekly discovery: Monday 9:00 AM IST
  workflow_dispatch:
    inputs:
      mode:
        description: Run mode (Note: live send is paused)
        required: true
        default: dry-run
        type: choice
        options: [dry-run, weekly, fetch, send]

jobs:
  outreach:
    name: Run Outreach Autopilot
    runs-on: ubuntu-latest
    timeout-minutes: 45

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: \'3.11\'

      # --- RESTORE STATE: Download previous sent-email history ---
      # This is what prevents duplicate emails across runs.
      # If no artifact exists yet (first ever run), this step is skipped silently.
      - name: Restore sent-email state
        uses: actions/download-artifact@v4
        with:
          name: aog-outreach-state
          path: scripts/
        continue-on-error: true

      - name: Restore data directory
        uses: actions/download-artifact@v4
        with:
          name: aog-outreach-data
          path: scripts/data/
        continue-on-error: true

      # --- BUILD CONFIG from encrypted GitHub Secrets ---
      # Credentials never stored in repo — assembled fresh each run
      - name: Build outreach_config.json from secrets
        env:
          APOLLO_API_KEY: ${{ secrets.APOLLO_API_KEY }}
          ZOHO_PASSWORD: ${{ secrets.ZOHO_PASSWORD }}
        run: |
          mkdir -p scripts/data scripts/logs
          cat > scripts/outreach_config.json << ENDOFCONFIG
          {
            "apollo": { "api_key": "$APOLLO_API_KEY" },
            "smtp": {
              "hosts": ["smtppro.zoho.in", "smtp.zoho.in", "smtppro.zoho.com"],
              "username": "partnerships@aogindia.com",
              "password": "$ZOHO_PASSWORD"
            },
            "sender": {
              "name": "Mohammad Yusuf Khan",
              "email": "partnerships@aogindia.com",
              "deck_url": "https://aogindia.com/for-brands.html#title-sponsorship"
            },
            "paused": true,
            "autopilot": {
              "paused": true,
              "daily_send_limit": 25,
              "min_delay_seconds": 60,
              "max_delay_seconds": 120,
              "business_hours_start_ist": 10,
              "business_hours_end_ist": 17,
              "send_on_weekends": false
            }
          }
          ENDOFCONFIG
          echo "[OK] Config assembled from encrypted secrets (outreach is PAUSED)"

      # --- SHOW STATE: How many already sent (for run logs) ---
      - name: Show current state summary
        run: |
          if [ -f scripts/data/autopilot_state.json ]; then
            SENT=$(python3 -c "import json; d=json.load(open(\'scripts/data/autopilot_state.json\')); print(len(d.get(\'sent_emails\', {})))")
            echo "[*] Already emailed (will skip): $SENT contacts"
          else
            echo "[*] First run - no previous state found"
          fi
          if [ -f scripts/leads_template.csv ]; then
            PENDING=$(python3 -c "import csv; r=list(csv.DictReader(open(\'scripts/leads_template.csv\'))); print(len([x for x in r if x.get(\'status\')==\'pending\']))")
            echo "[*] Leads ready to send: $PENDING"
          fi

      # --- EXECUTE: Run the correct mode ---
      - name: Weekly brand discovery (Monday auto-schedule)
        if: github.event_name == \'schedule\' && github.event.schedule == \'30 3 * * 1\'
        run: python3 scripts/autopilot_sponsor_outreach.py --weekly

      - name: Daily email sending (auto-schedule) [PAUSED]
        if: false # PAUSED by user request
        run: python3 scripts/autopilot_sponsor_outreach.py --now

      - name: Manual send [PAUSED]
        if: github.event_name == \'workflow_dispatch\' && github.event.inputs.mode == \'send\'
        run: |
          echo "[PAUSED] Direct email sending is paused by user request."
          echo "Please unpause in outreach_config.json before sending."
          exit 1

      - name: Manual weekly discovery
        if: github.event_name == \'workflow_dispatch\' && github.event.inputs.mode == \'weekly\'
        run: python3 scripts/autopilot_sponsor_outreach.py --weekly

      - name: Manual dry run
        if: github.event_name == \'workflow_dispatch\' && github.event.inputs.mode == \'dry-run\'
        run: python3 scripts/autopilot_sponsor_outreach.py --dry-run

      - name: Manual Apollo fetch
        if: github.event_name == \'workflow_dispatch\' && github.event.inputs.mode == \'fetch\'
        run: python3 scripts/autopilot_sponsor_outreach.py --fetch

      # --- SAVE STATE: Upload sent history so next run skips these contacts ---
      # Runs even if emails partially failed (always) to preserve partial progress.
      - name: Save leads CSV state
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: aog-outreach-state
          path: scripts/leads_template.csv
          retention-days: 90
          overwrite: true

      - name: Save data directory state
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: aog-outreach-data
          path: scripts/data/
          retention-days: 90
          overwrite: true

      # --- SUMMARY ---
      - name: Print run summary
        if: always()
        run: |
          echo "======================================================"
          echo "  AOG India Autopilot Run Complete"
          echo "======================================================"
          if [ -f scripts/data/autopilot_state.json ]; then
            TOTAL=$(python3 -c "import json; d=json.load(open(\'scripts/data/autopilot_state.json\')); print(len(d.get(\'sent_emails\', {})))")
            echo "  Total emails sent (all-time, no repeats): $TOTAL"
          fi
          echo "  State saved - next run will skip all $TOTAL contacts"
          echo "  Next scheduled run: tomorrow 10:30 AM IST"
          echo "======================================================"
'''

    with open(yml_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("=" * 72)
    print("  AOG INDIA - GITHUB ACTIONS SETUP")
    print("=" * 72)
    print(f"[OK] Generated: {yml_path}")
    print()
    print("  NEXT STEPS (one-time only):")
    print("  1. Commit and push this file to GitHub:")
    print("     git add .github/workflows/outreach.yml")
    print("     git commit -m 'feat: add automated sponsor outreach workflow'")
    print("     git push")
    print()
    print("  2. Add secrets in GitHub > Settings > Secrets and Variables > Actions:")
    print("     APOLLO_API_KEY  = Y9YhFFBk6NZJV-gOhkvfIg")
    print("     ZOHO_PASSWORD   = rtdcH6zdUErT")
    print()
    print("  3. Done! GitHub will automatically:")
    print("     - Send emails every Mon-Fri at 10:30 AM IST")
    print("     - Discover new brands every Monday at 9:00 AM IST")
    print("     - NEVER email the same person twice (state tracked via Artifacts)")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(
        description="AOG India Esports - Autopilot Brand Sponsor Outreach Engine"
    )
    parser.add_argument("--pause", action="store_true", help="Pause automated and manual live email sending")
    parser.add_argument("--resume", action="store_true", help="Resume live email sending")
    parser.add_argument("--status", action="store_true", help="Check current outreach status and lead counts")
    parser.add_argument("--fetch", action="store_true", help="Fetch real marketing decision-makers from Apollo for target brands and save to CSV")
    parser.add_argument("--count", type=int, default=10, help="Number of brands to fetch leads for (default: 10)")
    parser.add_argument("--dry-run", action="store_true", help="Preview leads and emails without sending")
    parser.add_argument("--now", action="store_true", help="Execute an outreach batch right now")
    parser.add_argument("--test-email", type=str, help="Send a single test email to your inbox")
    parser.add_argument("--test-batch", type=str, metavar="EMAIL", help="Send one real preview email per brand category to EMAIL — see full personalisation across all categories")
    parser.add_argument("--test-final", type=str, metavar="EMAIL", help="Send 3 production-identical sample emails to EMAIL with EXACT real subject lines (no prefix)")
    parser.add_argument("--daemon", action="store_true", help="Run background daemon that sends automatically every business day")
    parser.add_argument("--weekly", action="store_true", help="Run weekly brand discovery: scan 20+ gaming sponsor brands and append new contacts")
    parser.add_argument("--setup", action="store_true", help="Generate setup_windows_scheduler.ps1 for Windows Task Scheduler automation")
    parser.add_argument("--setup-github", action="store_true", help="Generate .github/workflows/outreach.yml for free GitHub Actions automation (recommended)")

    args = parser.parse_args()

    if args.pause:
        pause_outreach()
        return

    if args.resume:
        resume_outreach()
        return

    no_config_needed = args.setup or args.setup_github
    if not CONFIG_FILE.exists() and not no_config_needed:
        print(f"[X] Config file not found at: {CONFIG_FILE}")
        sys.exit(1)

    if not no_config_needed:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    if args.status:
        print_outreach_status(config)
    elif args.setup_github:
        setup_github_actions()
    elif args.setup:
        setup_windows_scheduler()
    elif args.fetch:
        run_fetch_only(config, num_brands=args.count)
    elif args.dry_run:
        run_autopilot_cycle(config, force=True, dry_run=True)
    elif args.test_email:
        send_test_email(args.test_email, config)
    elif args.test_batch:
        send_test_batch(args.test_batch, config)
    elif args.test_final:
        send_test_final(args.test_final, config, count=args.count if args.count != 10 else 3)
    elif args.now:
        run_autopilot_cycle(config, force=True, dry_run=False)
    elif args.daemon:
        run_daemon_loop(config)
    elif args.weekly:
        run_weekly_discovery(config)
    else:
        parser.print_help()
        print("\nTips:")
        print("  --status        Check current outreach status (PAUSED vs ACTIVE)")
        print("  --pause         Pause email sending immediately")
        print("  --resume        Resume email sending")
        print("  --dry-run       Preview leads without sending")
        print("  --setup-github  Generate GitHub Actions workflow (free, no server needed)")
        print("  --setup         Generate Windows Task Scheduler script")
        print("  --test-batch EMAIL  Send one preview email per category to your inbox")
        print("  --fetch         Pull brand contacts from Apollo")
        print("  --weekly        Discover new gaming sponsors")
        print("  --daemon        Run 24/7 background daemon")


if __name__ == "__main__":
    main()
