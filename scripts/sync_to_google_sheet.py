#!/usr/bin/env python3
"""
=============================================================================
AOG India Esports — Google Sheet Synchronizer
=============================================================================
Syncs sponsor leads directly to Yusuf's Google Spreadsheet:
"aog_title_sponsor_brand_outreach_list_by_py_script"
Link: https://docs.google.com/spreadsheets/d/10sTTE7wII1sC90_MUyPskaNo6aBDQ2wlNv4YDT-TA-s/edit?pli=1&gid=1842660684#gid=1842660684

Two sync methods:
1. Automatic Webhook:
   Sends data directly to the Google Apps Script Web App attached to the sheet.
2. Instant Clipboard Sync:
   Copies all leads in TSV format directly into your Windows clipboard.
   Open the sheet, click cell A1, and press Ctrl+V.

Usage:
    # 1. Instant copy to Windows clipboard for 1-click paste into Google Sheet:
    python scripts/sync_to_google_sheet.py --copy

    # 2. Push directly to Google Sheet Webhook:
    python scripts/sync_to_google_sheet.py --push

    # 3. Print the Apps Script setup code:
    python scripts/sync_to_google_sheet.py --setup-code
=============================================================================
"""

import argparse
import csv
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "leads_template.csv"
CONFIG_FILE = BASE_DIR / "outreach_config.json"

APPS_SCRIPT_CODE = '''// =====================================================================
// AOG India - Unified Webhook Handler
// 1. Python Sponsor Outreach List   -> GID 1842660684 (Outreach Tab - Replaced sync)
// 2. Creator Rates & Roster Form    -> 'aogindia_creator_rates' (Appended)
// 3. Website Contact Leads          -> 'aogindia_form_leads' (Appended)
// =====================================================================

function doPost(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var d = {};
  if (e.postData && e.postData.contents) {
    var body = e.postData.contents;
    try {
      d = JSON.parse(body);
    } catch (err) {
      var params = body.split('&');
      for (var i = 0; i < params.length; i++) {
        var kv = params[i].split('=');
        d[decodeURIComponent(kv[0])] = decodeURIComponent((kv[1] || '').replace(/\\+/g, ' '));
      }
    }
  }
  for (var k in e.parameter) { d[k] = e.parameter[k]; }

  // -------------------------------------------------------------------
  // BRANCH 1: SPONSOR OUTREACH LEADS (From Python Script -> GID 1842660684)
  // -------------------------------------------------------------------
  if (d.type === 'sponsor_outreach' || d.action === 'sponsor_outreach' || d.outreach_leads) {
    var outreachSheet = null;
    var allSheets = ss.getSheets();
    for (var s = 0; s < allSheets.length; s++) {
      if (allSheets[s].getSheetId() == 1842660684) {
        outreachSheet = allSheets[s];
        break;
      }
    }
    if (!outreachSheet) {
      outreachSheet = ss.getSheetByName('aog_title_sponsor_brand_outreach_list_by_py_script') || ss.getActiveSheet();
    }

    if (d.mode === 'replace' || d.replace === true) {
      outreachSheet.clear();
      if (d.headers && d.headers.length > 0) {
        outreachSheet.appendRow(d.headers);
        var headerRange = outreachSheet.getRange(1, 1, 1, d.headers.length);
        headerRange.setFontWeight('bold');
        headerRange.setBackground('#182032');
        headerRange.setFontColor('#38bdf8');
      }
      if (d.rows && d.rows.length > 0) {
        outreachSheet.getRange(2, 1, d.rows.length, d.headers.length).setValues(d.rows);
      }
    } else if (d.rows && d.rows.length > 0) {
      for (var r = 0; r < d.rows.length; r++) {
        outreachSheet.appendRow(d.rows[r]);
      }
    }

    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok', type: 'sponsor_outreach', count: (d.rows ? d.rows.length : 0) }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // -------------------------------------------------------------------
  // BRANCH 2: CREATOR RATES & ROSTER FORM (-> Dedicated Tab 'aogindia_creator_rates')
  // New creator submissions append after the last line!
  // -------------------------------------------------------------------
  if (d.user_type === 'creator' || d.creator_category || d.rate_livestream || d.rate_shorts || d.rate_longform_integrated) {
    var creatorSheet = ss.getSheetByName('aogindia_creator_rates');
    if (!creatorSheet) {
      creatorSheet = ss.insertSheet('aogindia_creator_rates');
    }
    var creatorHeaders = [
      'Timestamp',
      'Channel / Creator Name',
      'Full Name',
      'Email',
      'Channel / Social Link',
      'Category',
      'Primary Niche / Game',
      'Content Formats Produced',
      'Live-Stream Rate (INR)',
      'Shorts / Reel Rate (INR)',
      'Long-form Integrated Rate (INR)',
      'Long-form Dedicated Rate (INR)',
      'Subscriber / Follower Count',
      'Average Views',
      'Inquiry Type',
      'Message / Pitch',
      'Status'
    ];
    if (creatorSheet.getLastRow() === 0) {
      creatorSheet.appendRow(creatorHeaders);
      var hRange = creatorSheet.getRange(1, 1, 1, creatorHeaders.length);
      hRange.setFontWeight('bold');
      hRange.setBackground('#0d100c');
      hRange.setFontColor('#ff7a1a');
    }

    creatorSheet.appendRow([
      new Date(),
      d.channel_name || '',
      d.name || '',
      d.email || '',
      d.channel_link || '',
      d.creator_category || '',
      d.creator_niche || '',
      d.creator_content_types || '',
      d.rate_livestream || 'N/A',
      d.rate_shorts || 'N/A',
      d.rate_longform_integrated || 'N/A',
      d.rate_longform_dedicated || 'N/A',
      d.creator_subs || '',
      d.creator_avg_views || '',
      d.creator_query_type || '',
      d.message || '',
      'New Creator'
    ]);

    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok', type: 'creator_rates' }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  // -------------------------------------------------------------------
  // BRANCH 3: WEBSITE CONTACT FORMS (Brands / Agencies / General Inquiries)
  // Appends after the last line!
  // -------------------------------------------------------------------
  var sheet = ss.getSheetByName('aogindia_form_leads') || ss.getSheets()[0];
  var headers = ['Timestamp','Source Page','Full Name','Email','Profile / Lead Type','Company / Brand Name','Company Website','Brand Inquiry Type','Budget Range','Channel / Creator Name','Creator Inquiry Type','Channel / Social Link','Follower / Sub Count','Agency Name','Agency Type','Discovery Source','Discovery Other','Message','Status','Assigned To','Follow-up Date','Notes'];
  if (sheet.getLastRow() === 0) sheet.appendRow(headers);

  sheet.appendRow([
    new Date(),
    d.from_url || d.subject || '',
    d.name || '', d.email || '', d.user_type || '',
    d.company_name || '', d.company_website || '',
    d.brand_query_type || '', d.brand_budget || '',
    d.channel_name || '', d.creator_query_type || '',
    d.channel_link || '', d.creator_subs || '',
    d.agency_name || '', d.agency_type || '',
    d.discovery || '', d.discovery_other || '',
    d.message || '',
    'New', '', '', ''
  ]);
  return ContentService.createTextOutput(JSON.stringify({status:'ok'})).setMimeType(ContentService.MimeType.JSON);
}

// -------------------------------------------------------------------
// PULL LEADS: Allows python script to read live entries from Google Sheet
// -------------------------------------------------------------------
function doGet(e) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var outreachSheet = null;
  var allSheets = ss.getSheets();
  for (var s = 0; s < allSheets.length; s++) {
    if (allSheets[s].getSheetId() == 1842660684) {
      outreachSheet = allSheets[s];
      break;
    }
  }
  if (!outreachSheet) {
    outreachSheet = ss.getSheetByName('aog_title_sponsor_brand_outreach_list_by_py_script') || ss.getActiveSheet();
  }

  var data = outreachSheet.getDataRange().getValues();
  if (data.length <= 1) {
    return ContentService
      .createTextOutput(JSON.stringify({ status: 'ok', count: 0, headers: [], rows: [] }))
      .setMimeType(ContentService.MimeType.JSON);
  }

  var headers = data[0];
  var rows = data.slice(1);
  return ContentService
    .createTextOutput(JSON.stringify({ status: 'ok', count: rows.length, headers: headers, rows: rows }))
    .setMimeType(ContentService.MimeType.JSON);
}
'''


def load_leads_from_csv():
    if not CSV_FILE.exists():
        print(f"[X] CSV file not found at: {CSV_FILE}")
        return [], []
    with open(CSV_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if not rows:
        return [], []
    headers = rows[0]
    data_rows = rows[1:]
    return headers, data_rows


def copy_to_windows_clipboard():
    headers, rows = load_leads_from_csv()
    if not headers:
        print("[!] No leads found to copy.")
        return

    # Convert to Tab-Separated Values (TSV) which pastes perfectly into Google Sheets
    tsv_lines = ["\t".join(headers)]
    for r in rows:
        # Clean newlines / tabs within cells
        clean_row = [c.replace("\t", " ").replace("\r", "").replace("\n", " ") for c in r]
        tsv_lines.append("\t".join(clean_row))

    tsv_data = "\r\n".join(tsv_lines)

    # Copy to Windows clipboard via clip.exe or PowerShell
    copied = False
    try:
        proc = subprocess.Popen(["clip.exe"], stdin=subprocess.PIPE, shell=False)
        proc.communicate(input=tsv_data.encode("utf-16le"))
        copied = True
    except Exception:
        try:
            ps_cmd = "$input | Set-Clipboard"
            proc = subprocess.Popen(["powershell", "-Command", ps_cmd], stdin=subprocess.PIPE, shell=False)
            proc.communicate(input=tsv_data.encode("utf-8"))
            copied = True
        except Exception as e:
            print(f"[!] Could not copy directly via subprocess: {e}")

    if copied:
        print("=" * 72)
        print("  [✔] ALL LEADS COPIED TO WINDOWS CLIPBOARD!")
        print("=" * 72)
        print(f"  Rows copied: {len(rows)} leads + 1 header row")
        print()
        print("  👉 NEXT STEP:")
        print("  1. Open your Google Sheet:")
        print("     https://docs.google.com/spreadsheets/d/10sTTE7wII1sC90_MUyPskaNo6aBDQ2wlNv4YDT-TA-s/edit?pli=1&gid=1842660684#gid=1842660684")
        print("  2. Click cell A1")
        print("  3. Press Ctrl + V to paste everything cleanly into the sheet!")
        print("=" * 72)
    else:
        print("[!] Failed to copy to clipboard. You can import scripts/leads_template.csv via File > Import in Google Sheets.")


def push_to_google_sheet_webhook(webhook_url: str = None):
    headers, rows = load_leads_from_csv()
    if not headers:
        print("[!] No leads found in CSV.")
        return

    if not webhook_url and CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            webhook_url = cfg.get("google_sheet", {}).get("webhook_url", "").strip()

    if not webhook_url:
        print("=" * 72)
        print("  [!] GOOGLE SHEET WEBHOOK NOT YET CONFIGURED")
        print("=" * 72)
        print("  To enable 100% automated sync to your Google Sheet:")
        print("  1. Open your spreadsheet:")
        print("     https://docs.google.com/spreadsheets/d/10sTTE7wII1sC90_MUyPskaNo6aBDQ2wlNv4YDT-TA-s/edit?pli=1&gid=1842660684#gid=1842660684")
        print("  2. In the top menu, click: Extensions > Apps Script")
        print("  3. Run: python scripts/sync_to_google_sheet.py --setup-code")
        print("     Paste that code into Apps Script, click 'Deploy' > 'New Deployment' > 'Web App'")
        print("     (Who has access: Anyone)")
        print("  4. Copy the Web App URL and run:")
        print("     python scripts/sync_to_google_sheet.py --set-webhook YOUR_WEBHOOK_URL")
        print()
        print("  👉 IN THE MEANTIME, use instant 1-click clipboard paste:")
        print("     python scripts/sync_to_google_sheet.py --copy")
        print("=" * 72)
        return

    payload = {
        "type": "sponsor_outreach",
        "mode": "replace",
        "headers": headers,
        "rows": rows,
    }

    print(f"[*] Pushing {len(rows)} leads to Google Sheet Webhook...")
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data_bytes,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            resp_body = resp.read().decode("utf-8")
            print("[✔] Successfully synchronized leads to your Google Sheet!")
            print(f"    Server response: {resp_body[:200]}")
    except Exception as e:
        print(f"[X] Webhook delivery failed: {e}")


def set_webhook_url(url: str):
    if not CONFIG_FILE.exists():
        print(f"[X] Config not found: {CONFIG_FILE}")
        return
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if "google_sheet" not in cfg or not isinstance(cfg["google_sheet"], dict):
        cfg["google_sheet"] = {}
    cfg["google_sheet"]["name"] = "aog_title_sponsor_brand_outreach_list_by_py_script"
    cfg["google_sheet"]["sheet_url"] = "https://docs.google.com/spreadsheets/d/10sTTE7wII1sC90_MUyPskaNo6aBDQ2wlNv4YDT-TA-s/edit?pli=1&gid=1842660684#gid=1842660684"
    cfg["google_sheet"]["webhook_url"] = url.strip()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    print("=" * 72)
    print(f"[OK] Google Sheet Webhook saved to {CONFIG_FILE.name}")
    print("=" * 72)
    # Test push immediately
    push_to_google_sheet_webhook(url.strip())


def pull_leads_from_google_sheet():
    """
    Pulls live leads directly from Yusuf's Google Sheet and updates scripts/leads_template.csv.
    Enables managing and adding leads in Google Sheets as your primary command center.
    """
    print("[*] Pulling latest leads from Google Sheet...")
    cfg = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)

    webhook_url = cfg.get("google_sheet", {}).get("webhook_url", "").strip()
    sheet_id = cfg.get("google_sheet", {}).get("spreadsheet_id", "10sTTE7wII1sC90_MUyPskaNo6aBDQ2wlNv4YDT-TA-s")
    gid = cfg.get("google_sheet", {}).get("gid", "1842660684")

    headers, rows = [], []

    # Method 1: Webhook doGet
    if webhook_url:
        try:
            req = urllib.request.Request(webhook_url, headers={"User-Agent": "AOGIndia-Outreach/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("status") == "ok" and data.get("rows"):
                    headers = data.get("headers", [])
                    rows = data.get("rows", [])
                    print(f"[✔] Fetched {len(rows)} leads via Google Apps Script Webhook.")
        except Exception:
            pass

    # Method 2: Direct CSV Export URL
    if not rows and sheet_id:
        try:
            export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
            req = urllib.request.Request(export_url, headers={"User-Agent": "AOGIndia-Outreach/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                csv_text = resp.read().decode("utf-8-sig")
                reader = csv.reader(csv_text.splitlines())
                parsed = list(reader)
                if len(parsed) > 1:
                    headers = parsed[0]
                    rows = parsed[1:]
                    print(f"[✔] Fetched {len(rows)} leads via Google Sheets Export URL.")
        except Exception as e:
            print(f"[!] Could not pull directly via CSV export: {e}")

    if headers and rows:
        # Write back to local CSV
        with open(CSV_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        print(f"[✔] Successfully synchronized {len(rows)} leads into {CSV_FILE.name}")
        return headers, rows
    else:
        print("[!] Using local leads_template.csv (remote Google Sheet was empty or offline).")
        return load_leads_from_csv()


def main():
    parser = argparse.ArgumentParser(description="Sync AOG India sponsor leads to Google Sheets")
    parser.add_argument("--copy", action="store_true", help="Copy all leads into Windows clipboard as TSV for instant Ctrl+V into Google Sheets")
    parser.add_argument("--push", action="store_true", help="Push leads directly to Google Sheet Webhook URL")
    parser.add_argument("--pull", action="store_true", help="Pull latest leads from Google Sheet down into scripts/leads_template.csv")
    parser.add_argument("--set-webhook", type=str, metavar="URL", help="Save Apps Script Webhook URL in outreach_config.json and push")
    parser.add_argument("--setup-code", action="store_true", help="Print the 20-line Apps Script code to paste into Google Sheet")

    args = parser.parse_args()

    if args.copy:
        copy_to_windows_clipboard()
    elif args.pull:
        pull_leads_from_google_sheet()
    elif args.set_webhook:
        set_webhook_url(args.set_webhook)
    elif args.push:
        push_to_google_sheet_webhook()
    elif args.setup_code:
        print("=" * 72)
        print("  GOOGLE APPS SCRIPT CODE TO PASTE INTO YOUR SPREADSHEET")
        print("=" * 72)
        print(APPS_SCRIPT_CODE)
        print("=" * 72)
    else:
        # Default behavior: run copy to clipboard so user immediately gets the data
        copy_to_windows_clipboard()


if __name__ == "__main__":
    main()
