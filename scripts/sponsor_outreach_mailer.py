#!/usr/bin/env python3
"""
=============================================================================
AOG India Esports — Brand Sponsor Automated Outreach Engine
=============================================================================
Automated, deliverability-optimized email outreach tool for contacting brand
decision-makers regarding AOG India's 2026 Title Sponsorship.

Features:
- Standard-library only (Zero external pip dependencies).
- Dual MIME (Multipart/Alternative: Plain text + Clean HTML) for maximum inbox delivery.
- Smart rate-limiting & randomized jitter (prevents spam flagging).
- In-place CSV lead status tracking & history logging.
- Safety modes:
    * --dry-run: Previews generated emails in terminal without sending.
    * --test-email: Sends a single sample email to your personal inbox.
    * --send: Processes pending leads from CSV.

Usage:
    1. Copy 'scripts/outreach_config.example.json' to 'scripts/outreach_config.json'
       and fill in your SMTP credentials.
    2. Add prospects to 'scripts/leads_template.csv'.
    3. Test render:
       python scripts/sponsor_outreach_mailer.py --dry-run
    4. Send a test email to yourself:
       python scripts/sponsor_outreach_mailer.py --test-email you@yourdomain.com
    5. Run outreach batch:
       python scripts/sponsor_outreach_mailer.py --send
=============================================================================
"""

import argparse
import csv
import datetime
import json
import os
import random
import re
import smtplib
import ssl
import sys
import time
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, make_msgid
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = BASE_DIR / "outreach_config.json"
DEFAULT_EXAMPLE_CONFIG_PATH = BASE_DIR / "outreach_config.example.json"
DEFAULT_LEADS_PATH = BASE_DIR / "leads_template.csv"
LOGS_DIR = BASE_DIR / "logs"


# ---------------------------------------------------------------------------
# High-Converting Email Templates for Title Sponsorship
# ---------------------------------------------------------------------------

SUBJECT_TEMPLATES = [
    "Exclusive Title Partnership opportunity for {company_name} — 5M+ Monthly Gaming Views",
    "{company_name} x AOG India — 2026 Official Title Sponsorship Slot",
    "Quick question regarding {company_name}'s gaming & Gen-Z reach in India",
]

PLAIN_TEXT_TEMPLATE = """Hi {contact_first_name},

Hope you're having a great week.

I've been following {company_name}'s footprint in India{compliment_clause}. 

I am reaching out from AOG India — we are one of India's fastest-growing gaming media & creator networks, generating over 5 Million+ monthly views across YouTube, live streams, and short-form content.

We are currently opening our single, exclusive Title Partnership slot for 2026 across our premier gaming ecosystems:
- 4 Core Titles: Minecraft, Valorant, BGMI, and Free Fire
- 360° Native Placement: Live stream overlays, tournament integration, dedicated YouTube videos & Shorts/Reels
- 100% Category Exclusivity: We will not partner with any competitor in your vertical during the term
- Direct Attribution: Custom UTM tracking, link-in-description on 200+ creator channels, and monthly performance reporting

Given {company_name}'s alignment with India's 18–28 gaming demographic, we believe this would drive massive brand recall and direct conversions.

You can view our live sponsorship overview here:
{deck_url}

Would you or your brand marketing team be open to a quick 10-minute discovery call this Thursday or Friday to explore if this is a fit?

Best regards,

{sender_name}
Brand Outreach | AOG India Esports
Email: {sender_email}
Website: https://aogindia.com

---
If you'd prefer not to hear from us regarding sponsorships, please reply 'Unsubscribe' and we will immediately remove your address.
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
      color: #222222;
      background-color: #ffffff;
      margin: 0;
      padding: 16px;
    }}
    .container {{
      max-width: 600px;
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
      font-weight: 600;
      color: #0d1117;
    }}
    .cta-box {{
      background: #f8f9fa;
      border-left: 4px solid #ff7a1a;
      padding: 14px 18px;
      margin: 18px 0;
      border-radius: 4px;
    }}
    .cta-link {{
      color: #e65100;
      font-weight: 600;
      text-decoration: none;
    }}
    .footer {{
      margin-top: 28px;
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
    <p>Hi {contact_first_name},</p>

    <p>Hope you're having a great week.</p>

    <p>I've been following {company_name}'s footprint in India{compliment_clause}.</p>

    <p>I am reaching out from <strong>AOG India</strong> — one of India's fastest-growing gaming media and creator networks, generating over <strong>5 Million+ monthly views</strong> across YouTube, competitive live streams, and short-form video.</p>

    <p>We have just opened our <strong>1 Exclusive Title Partnership Slot for 2026</strong> across our premier gaming rosters:</p>

    <ul>
      <li><span class="highlight">4 Top Game Titles:</span> Minecraft, Valorant, BGMI, and Free Fire</li>
      <li><span class="highlight">360° Placement:</span> Live stream integrations, dedicated creator content, tournament overlays, Shorts &amp; Reels</li>
      <li><span class="highlight">Full Category Exclusivity:</span> Zero competitors in your vertical featured during the partnership</li>
      <li><span class="highlight">Performance Attribution:</span> Custom UTMs, direct click-throughs, and monthly campaign metrics</li>
    </ul>

    <div class="cta-box">
      <p style="margin: 0 0 6px 0;"><strong>Explore the Sponsorship Overview:</strong></p>
      <a href="{deck_url}" class="cta-link">View AOG India Title Partnership Deck &rarr;</a>
    </div>

    <p>Given {company_name}'s resonance with India's high-intent 18–28 gaming demographic, we would love to explore whether this aligns with your Q2/Q3 brand marketing goals.</p>

    <p>Would you or your brand marketing team have 10 minutes for a brief call this Thursday or Friday?</p>

    <p style="margin-top: 20px;">
      Best regards,<br>
      <strong>{sender_name}</strong><br>
      Brand Outreach | AOG India Esports<br>
      <a href="https://aogindia.com" style="color: #666; text-decoration: none;">aogindia.com</a>
    </p>

    <div class="footer">
      <p>AOG India Esports &bull; Gaming Marketing &amp; Media Agency &bull; partnerships@aogindia.com<br>
      If you would prefer not to receive sponsorship opportunities from us, simply reply with "Unsubscribe" to be instantly removed.</p>
    </div>
  </div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    """Loads configuration from JSON file. Falls back with helpful guidance."""
    target_path = config_path if config_path.exists() else DEFAULT_CONFIG_PATH
    if not target_path.exists():
        if DEFAULT_EXAMPLE_CONFIG_PATH.exists():
            print(f"[!] Warning: Config file '{target_path.name}' not found.")
            print(f"    Please copy '{DEFAULT_EXAMPLE_CONFIG_PATH.name}' to '{DEFAULT_CONFIG_PATH.name}'")
            print("    and insert your Gmail / Google Workspace SMTP App Password.\n")
        raise FileNotFoundError(f"Configuration file not found at: {target_path}")

    with open(target_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Validate essential fields
    smtp = config.get("smtp", {})
    if smtp.get("password") == "YOUR_GMAIL_OR_WORKSPACE_APP_PASSWORD":
        print("[!] NOTICE: Config has placeholder password 'YOUR_GMAIL_OR_WORKSPACE_APP_PASSWORD'.")
        print("    Please set an actual 16-character Google App Password in 'outreach_config.json'.")

    return config


def extract_first_name(full_name: str) -> str:
    """Extracts first name or friendly name for casual greeting."""
    if not full_name or not full_name.strip():
        return "there"
    cleaned = full_name.strip().split()[0]
    return cleaned.capitalize()


def build_email_content(lead: dict, config: dict, subject_index: int = 0) -> tuple:
    """Compiles customized subject, plain text, and HTML body for a single lead."""
    smtp_cfg = config.get("smtp", {})
    rules_cfg = config.get("sending_rules", {})

    contact_name = lead.get("contact_name", "").strip()
    contact_first_name = extract_first_name(contact_name)
    company_name = lead.get("company_name", "your brand").strip()
    custom_comp = lead.get("custom_compliment", "").strip()

    if custom_comp:
        compliment_clause = f" — {custom_comp}"
    else:
        compliment_clause = ""

    deck_url = rules_cfg.get(
        "company_deck_url", "https://aogindia.com/for-brands.html#title-sponsorship"
    )
    sender_name = smtp_cfg.get("from_name", "Aarti Chauhan | AOG India")
    sender_email = smtp_cfg.get("from_email", "partnerships@aogindia.com")

    # Pick subject template
    subject_tmpl = SUBJECT_TEMPLATES[subject_index % len(SUBJECT_TEMPLATES)]
    subject = subject_tmpl.format(company_name=company_name)

    context = {
        "contact_first_name": contact_first_name,
        "company_name": company_name,
        "compliment_clause": compliment_clause,
        "deck_url": deck_url,
        "sender_name": sender_name,
        "sender_email": sender_email,
    }

    plain_body = PLAIN_TEXT_TEMPLATE.format(**context)
    html_body = HTML_TEMPLATE.format(**context)

    return subject, plain_body, html_body


def create_mime_message(
    sender_name: str,
    sender_email: str,
    recipient_email: str,
    subject: str,
    plain_body: str,
    html_body: str,
    reply_to: str = None,
) -> MIMEMultipart:
    """Constructs a standard multipart/alternative email with headers."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = formataddr((str(Header(sender_name, "utf-8")), sender_email))
    msg["To"] = recipient_email
    msg["Message-ID"] = make_msgid(domain="aogindia.com")
    msg["Date"] = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    if reply_to:
        msg["Reply-To"] = reply_to

    # Attach plain text first, then HTML as alternative
    part1 = MIMEText(plain_body, "plain", "utf-8")
    part2 = MIMEText(html_body, "html", "utf-8")
    msg.attach(part1)
    msg.attach(part2)

    return msg


def load_leads(csv_path: Path) -> list:
    """Loads leads from CSV into list of dicts."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Leads CSV not found at: {csv_path}")

    leads = []
    with open(csv_path, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(dict(row))
    return leads


def save_leads(csv_path: Path, leads: list):
    """Saves updated leads list back to CSV preserving headers."""
    if not leads:
        return

    fieldnames = list(leads[0].keys())
    with open(csv_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(leads)


def append_log(log_entry: dict):
    """Appends an event to logs/outreach_history.jsonl."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / "outreach_history.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")


# ---------------------------------------------------------------------------
# Sending Routines
# ---------------------------------------------------------------------------

def connect_smtp(smtp_cfg: dict) -> smtplib.SMTP:
    """Establishes an authenticated, TLS-encrypted SMTP connection."""
    host = smtp_cfg.get("host", "smtp.gmail.com")
    port = smtp_cfg.get("port", 587)
    use_tls = smtp_cfg.get("use_tls", True)
    username = smtp_cfg.get("username", "")
    password = smtp_cfg.get("password", "")

    if not username or not password:
        raise ValueError("SMTP username or password is not configured.")

    server = smtplib.SMTP(host, port, timeout=25)
    server.ehlo()

    if use_tls:
        context = ssl.create_default_context()
        server.starttls(context=context)
        server.ehlo()

    server.login(username, password)
    return server


def run_dry_run(leads: list, config: dict, limit: int = None):
    """Simulates outreach run by printing personalized emails without sending."""
    print("=" * 70)
    print("  AOG INDIA — DRY RUN SIMULATION (NO EMAILS SENT)")
    print("=" * 70)

    pending_leads = [
        lead for lead in leads if lead.get("status", "").lower() != "sent"
    ]
    if limit:
        pending_leads = pending_leads[:limit]

    print(f"Total leads: {len(leads)} | Pending for outreach: {len(pending_leads)}\n")

    for idx, lead in enumerate(pending_leads, start=1):
        subject, plain_body, _ = build_email_content(lead, config, subject_index=idx - 1)
        print(f"--- [Lead #{idx}: {lead.get('company_name')} ({lead.get('email')})] ---")
        print(f"Subject : {subject}")
        print(f"Recipient: {lead.get('contact_name')} <{lead.get('email')}>")
        print("Message Body Preview:")
        print("-" * 50)
        print(plain_body[:550] + ("\n... [truncated for preview]" if len(plain_body) > 550 else ""))
        print("=" * 70 + "\n")

    print("[✔] Dry-run complete. All templates rendered successfully.")
    print("    To send real emails, run with '--send' after updating credentials.")


def send_test_email(test_recipient: str, leads: list, config: dict):
    """Sends a single test email using the first lead's context to a test address."""
    print(f"[*] Preparing test email to: {test_recipient}")
    sample_lead = leads[0] if leads else {
        "company_name": "Sample Gaming Brand",
        "contact_name": "Team Lead",
        "email": test_recipient,
        "custom_compliment": "admiring your top-tier gaming peripherals",
    }

    subject, plain_body, html_body = build_email_content(sample_lead, config)
    subject = f"[TEST OUTREACH] {subject}"

    smtp_cfg = config.get("smtp", {})
    sender_name = smtp_cfg.get("from_name", "Aarti Chauhan | AOG India")
    sender_email = smtp_cfg.get("from_email", "partnerships@aogindia.com")
    reply_to = smtp_cfg.get("reply_to", sender_email)

    msg = create_mime_message(
        sender_name, sender_email, test_recipient, subject, plain_body, html_body, reply_to
    )

    print("[*] Connecting to SMTP server...")
    try:
        server = connect_smtp(smtp_cfg)
        server.send_message(msg)
        server.quit()
        print(f"[✔] Successfully sent test email to: {test_recipient}")
        print("    Check your inbox and spam folder to confirm delivery and formatting.")
    except Exception as e:
        print(f"[X] Failed to send test email: {e}")
        sys.exit(1)


def run_live_outreach(leads_path: Path, leads: list, config: dict, limit: int = None):
    """Executes live outreach batch with safety throttling and state tracking."""
    if config.get("paused", False) or os.environ.get("AOG_OUTREACH_PAUSED", "").lower() in ("1", "true", "yes"):
        print("\n" + "!" * 70)
        print("  [STOP] EMAIL OUTREACH IS CURRENTLY PAUSED BY USER REQUEST")
        print("  Reason: Reviewing lead sheet & email appropriateness.")
        print("  Zero emails were sent. Safety guard active.")
        print("  To resume, set 'paused': false in scripts/outreach_config.json")
        print("!" * 70 + "\n")
        return

    smtp_cfg = config.get("smtp", {})
    rules_cfg = config.get("sending_rules", {})

    min_delay = rules_cfg.get("min_delay_seconds", 35)
    max_delay = rules_cfg.get("max_delay_seconds", 75)
    max_batch = rules_cfg.get("max_emails_per_session", 30)

    if limit:
        max_batch = min(max_batch, limit)

    pending_leads = [
        (idx, lead) for idx, lead in enumerate(leads)
        if lead.get("status", "").lower() in ["pending", ""]
    ]

    if not pending_leads:
        print("[!] No pending leads found in CSV. (Leads marked 'paused', 'sent', or 'skip' are skipped).")
        return

    batch_to_send = pending_leads[:max_batch]

    print("=" * 70)
    print(f"  AOG INDIA — STARTING LIVE OUTREACH BATCH ({len(batch_to_send)} EMAILS)")
    print(f"  Safety delay between sends: {min_delay}s to {max_delay}s")
    print("=" * 70)

    confirm = input("Are you ready to send real emails to brand prospects? (yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("[*] Outreach cancelled by user.")
        return

    try:
        server = connect_smtp(smtp_cfg)
        print("[✔] SMTP authentication successful.\n")
    except Exception as e:
        print(f"[X] Failed to authenticate with SMTP server: {e}")
        return

    sender_name = smtp_cfg.get("from_name", "Aarti Chauhan | AOG India")
    sender_email = smtp_cfg.get("from_email", "partnerships@aogindia.com")
    reply_to = smtp_cfg.get("reply_to", sender_email)

    sent_count = 0
    fail_count = 0

    for i, (original_idx, lead) in enumerate(batch_to_send, start=1):
        brand = lead.get("company_name", "Unknown")
        to_email = lead.get("email", "").strip()

        if not to_email or "@" not in to_email:
            print(f"[{i}/{len(batch_to_send)}] Skipping invalid email for {brand}: '{to_email}'")
            leads[original_idx]["status"] = "invalid_email"
            continue

        subject, plain_body, html_body = build_email_content(lead, config, subject_index=i)
        msg = create_mime_message(
            sender_name, sender_email, to_email, subject, plain_body, html_body, reply_to
        )

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{i}/{len(batch_to_send)}] Sending to {brand} <{to_email}>...")

        try:
            server.send_message(msg)
            sent_count += 1
            leads[original_idx]["status"] = "sent"
            leads[original_idx]["sent_at"] = now_str
            print(f"    [✔] Delivered to {to_email} at {now_str}")

            append_log({
                "timestamp": now_str,
                "company_name": brand,
                "email": to_email,
                "status": "success",
                "subject": subject,
            })

            # Save state immediately after each send to prevent re-sending on crash
            save_leads(leads_path, leads)

        except Exception as err:
            fail_count += 1
            leads[original_idx]["status"] = "failed"
            leads[original_idx]["notes"] = f"Error: {err}"
            print(f"    [X] Error sending to {to_email}: {err}")
            save_leads(leads_path, leads)

        # Throttling delay between sends (unless last item)
        if i < len(batch_to_send):
            delay = random.randint(min_delay, max_delay)
            print(f"    Waiting {delay} seconds before next email (deliverability guard)...")
            time.sleep(delay)

    try:
        server.quit()
    except Exception:
        pass

    print("\n" + "=" * 70)
    print(f"Batch completed: {sent_count} sent successfully, {fail_count} failed.")
    print(f"Updated CSV saved to: {leads_path}")
    print("=" * 70)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AOG India Esports — Automated Brand Sponsor Outreach Mailer"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="Path to JSON config file (default: scripts/outreach_config.json)",
    )
    parser.add_argument(
        "--leads",
        type=Path,
        default=DEFAULT_LEADS_PATH,
        help="Path to CSV leads file (default: scripts/leads_template.csv)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate run and print personalized email outputs without sending",
    )
    parser.add_argument(
        "--test-email",
        type=str,
        help="Send a single test email to your own address to verify formatting & inbox placement",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Send real emails to pending leads in the CSV",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of emails to process in this session",
    )

    args = parser.parse_args()

    # If no mode flag provided, show help
    if not (args.dry_run or args.test_email or args.send):
        parser.print_help()
        print("\n[!] Please specify a mode: --dry-run, --test-email <address>, or --send")
        sys.exit(0)

    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError as e:
        print(f"[X] {e}")
        sys.exit(1)

    # Load leads
    try:
        leads = load_leads(args.leads)
    except FileNotFoundError as e:
        print(f"[X] {e}")
        sys.exit(1)

    # Execute requested mode
    if args.dry_run:
        run_dry_run(leads, config, limit=args.limit)
    elif args.test_email:
        send_test_email(args.test_email, leads, config)
    elif args.send:
        run_live_outreach(args.leads, leads, config, limit=args.limit)


if __name__ == "__main__":
    main()
