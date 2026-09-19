# 🚀 Automated 100% Free SEO Keyword Discovery System

This directory contains `auto_seo.py`, an autonomous SEO optimization script designed for **AOG India Esports**. It dynamically fetches real-time search queries used by brands and agencies searching for gaming marketing agencies, BGMI creator campaigns, and esports influencers in India, updates meta tags and schema markup, updates XML sitemaps, and automatically purges Cloudflare CDN caches.

---

## 🛠️ How It Works

1. **Live Keyword Discovery**:
   - Querying live search data from **Google Autocomplete (India)** for terms like `gaming marketing agency india`, `bgmi creator agency`, `gaming influencer agency`, `gaming product seeding india`, etc.
   - Filters out irrelevant/harmful terms (e.g. *apk, mod, hack, cheap, free, download, cracked*).

2. **Automated On-Page SEO Updates**:
   - Updates `<meta name="keywords">` across `index.html`, `for-brands.html`, and `for-agencies.html`.
   - Injects fresh keyword entities into JSON-LD `knowsAbout` structured data.
   - Refreshes `<lastmod>` timestamps in `sitemap.xml` to notify search engine crawlers (Googlebot) of fresh content.

3. **Cloudflare CDN Cache Purge**:
   - Automatically issues a POST request to Cloudflare's API to purge cache for HTML pages and sitemaps so live users immediately see updated meta tags without waiting for edge cache expiration.

4. **GitHub Actions Automation**:
   - Scheduled via GitHub Actions (`.github/workflows/weekly_seo.yml`) to execute **every Monday at 00:00 UTC**.
   - Commits changes back to the main branch automatically (`[skip ci]`).

---

## ⚡ Enabling Automatic Cloudflare CDN Cache Purging

To allow the automated GitHub workflow to automatically clear Cloudflare cache after updating SEO tags:

### Step 1: Get Cloudflare Zone ID & API Token
1. Log in to your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Select your domain (`aogindia.com` or custom domain).
3. On the right sidebar of the **Overview** tab, copy your **Zone ID**.
4. Scroll down to API and click **Get your API Token** (or go to **My Profile > API Tokens**).
5. Click **Create Token** -> select the **Cache Purge** template (or custom token with `Zone.Cache Purge` permissions).
6. Copy the generated **API Token**.

### Step 2: Add Secrets to GitHub Repository
1. Open your GitHub Repository: `https://github.com/m-y-k/aogindia`
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**:
   - **Name**: `CLOUDFLARE_ZONE_ID`
   - **Value**: *(Paste your Zone ID)*
4. Click **New repository secret**:
   - **Name**: `CLOUDFLARE_API_TOKEN`
   - **Value**: *(Paste your API Token)*

---

## 🧪 Testing Locally

You can manually execute the script anytime on your PC:

```bash
python scripts/auto_seo.py
```

To test with Cloudflare cache purge locally:
```bash
set CLOUDFLARE_ZONE_ID=your_zone_id
set CLOUDFLARE_API_TOKEN=your_api_token
python scripts/auto_seo.py
```
