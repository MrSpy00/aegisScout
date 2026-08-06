# aegisScout — Business Discovery, OSINT Intelligence & Sales Outreach Platform

[![English README](https://img.shields.io/badge/Language-English-blue.svg)](README.md)
[![Türkçe README](https://img.shields.io/badge/Dil-Türkçe-red.svg)](README.tr.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-brightgreen.svg)](https://www.python.org/)

**aegisScout** is a modern, **self-hosted**, 100% private and local business discovery, deep OSINT enrichment, AI copywriting, and multi-channel outreach automation platform built specifically for web agencies, freelancers, software houses, and digital marketing professionals.

---

## 🖼️ Application Desktop Screenshots

Real application screenshots from the desktop dashboard (all sample data shown is placeholder):

### 📊 Dashboard & Discovery Radar
![Dashboard](assets/screenshot_dashboard.png)

### 📋 Leads Manager
![Leads Manager](assets/screenshot_leads.png)

### 🎯 Campaigns Manager
![Campaigns Manager](assets/screenshot_campaigns.png)

### ⚙️ Settings & Configuration Panel
![Settings Panel](assets/screenshot_settings.png)

---

## ✨ Detailed Feature Architecture

### 1. Business Discovery Engine & Zero-Key OSINT Framework

- **Geocoding & Location Intelligence:**
  - **OpenStreetMap (OSM) & Overpass API:** Unlimited sector and location business discovery without requiring external API keys.
  - **Komoot Photon API (`photon.komoot.io`):** Performs real-time address geocoding and coordinate resolution with zero key requirement.
  - **BigDataCloud & Country.is:** Provides client-side reverse geocoding and IP-based geolocation detection.
  - **Google Places API & SerpApi Local 3-Pack:** Optional integration for Google Maps and Local 3-Pack data; automatically falls back to free web scrapers when API keys are absent.

- **Zero-Key Deep OSINT Services:**
  - **ICANN RDAP (`rdap.org`):** Fetches domain registration age, registrar details, and WHOIS information.
  - **Cloudflare DNS-over-HTTPS (`1.1.1.1`):** Analyzes target MX infrastructure (Google Workspace, Microsoft 365, cPanel, ProtonMail) and audits SPF/DMARC security configurations.
  - **Shodan InternetDB (`internetdb.shodan.io`):** Detects open ports, known CVE vulnerabilities, and server tags without an API key.
  - **crt.sh Certificate Mining:** Extracts target subdomains from public SSL/TLS Certificate Transparency logs.
  - **Mozilla Observatory & Wayback Machine:** Queries web security compliance scores and historical site archives.
  - **IP-API & Ipify:** Identifies server IP address, hosting provider, ISP, and geographical datacenter location.

- **Visual Enrichment:**
  - **Google Favicon API & Unavatar:** Fetches 128x128 corporate logos and multi-platform social media avatars automatically.
  - **UI-Avatars, Microlink & Thum.io:** Generates dynamic colored initials, OpenGraph summaries, and real-time mobile/desktop site preview cards.

---

### 2. Multi-Channel Contact Discovery & Waterfall Enrichment

- **Waterfall Email Discovery Cascade:**
  1. **Website Scraping:** Deep-crawls target web pages to locate contact emails, phone numbers, and contact forms.
  2. **Search Engine Query:** Executes fallback search queries via Google and DuckDuckGo for public contact listings.
  3. **Social Bio Scraping:** Extracts contact details directly from Instagram, Facebook, and LinkedIn bios.
  4. **Smart Early Exit:** If a valid email is found at any stage, subsequent steps are skipped to conserve network bandwidth and API credits.

- **Deep Social Touchpoint Mining:**
  - Automatically identifies and matches social profiles across 15+ networks: Instagram, Facebook, LinkedIn, Twitter/X, TikTok, Telegram, YouTube, GitHub, Medium, Substack, Behance, Dribbble, Snapchat, Spotify, and Twitch.

- **Phone & Breach Intelligence:**
  - **Offline Phone Validation:** Uses `phonenumbers` for offline carrier, country code, and format validation; generates direct WhatsApp (`wa.me`) and Telegram (`t.me`) action links.
  - **Breach Audit:** Queries HIBP Pwned Passwords and XposedOrNot APIs to check whether corporate emails have appeared in public data breaches.

---

### 3. Local Email Verification & Deliverability Engine

- **4-Stage Local Validation Pipeline:**
  1. **Regex Syntax Check:** Validates email format against standard RFC specifications.
  2. **Disposable Domain Filtering:** Blocks 30+ known disposable and temporary email providers (extendable via `data/disposable_domains.txt`).
  3. **DNS MX Record Resolution:** Verifies active mail exchange server records for the domain.
  4. **Socket-Level SMTP Handshake Simulation:** Simulates `HELO`, `MAIL FROM`, and `RCPT TO` commands to verify mailbox existence without sending actual emails.
- **100% Free & Zero-API:** Operates entirely locally using native Python sockets and dnspython.

---

### 4. Multimodal Screen Audit & Design Intelligence

- **Playwright Automated Capture:** Takes desktop screenshots of target websites using headless Chromium and stores them locally.
- **Gemini Vision AI Analysis:** Analyzes web screenshots using multimodal vision AI to detect mobile responsiveness flaws, color contrast issues, typography hierarchy errors, and missing Call-to-Action (CTA) elements.
- **Local Heuristic Scoring:** When Vision API is unconfigured, computes a **100-point Website Quality Score** based on page load performance, broken link rates, and meta tag completeness.
- **Outreach Hook Generation:** Crafts high-converting, personalized conversation starters based on specific visual and technical issues discovered during the audit.

---

### 5. Multi-Agent AI Copywriter & Local RAG Knowledge Base

- **3-Agent AI Workflow:**
  - **Inspector:** Analyzes technical gaps, design flaws, and business opportunities.
  - **Copywriter:** Generates customized value propositions and outreach email drafts tailored to the target lead.
  - **Editor:** Strips generic AI jargon, robotic salutations, and unverified data to produce natural, human-sounding outreach messages.

- **Local RAG (Retrieval-Augmented Generation) Knowledge Base:**
  - Scans and indexes local `.txt`, `.md`, and `.pdf` files inside `data/knowledge_base/` containing portfolio items and case studies.
  - **Dual Engine Search:** Features offline TF-IDF Cosine Similarity and optional semantic vector embeddings via Ollama or Gemini API.

- **Product Ideation Engine:**
  - Generates 2-3 tailored digital product ideas, pitch hooks, and objection handlers customized for each target business profile.

---

### 6. Multi-LLM Router Architecture & Rate Limiting

- **Supported AI Providers:**
  - **OpenRouter API** (Access dozens of commercial and open-source models seamlessly)
  - **Google Gemini API** (High-speed analysis via Gemini 2.5 Flash)
  - **Groq API** (Ultra-low latency generation via Llama-3.3-70b)
  - **Mistral AI API** (Enterprise reasoning via Mistral Large)
  - **DeepSeek API** (Cost-effective deep reasoning)
  - **OpenAI API** (GPT-4o & GPT-4o mini)
  - **Anthropic Claude API** (Claude 3.5 Haiku)
  - **Ollama** (Fully offline, private, and free local LLM support)

- **Failover Routing & Key Rotation:**
  - Rotates multiple comma-separated API keys automatically. Automatically redirects requests to a secondary fallback provider if the primary service experiences outages or rate limits.

---

### 7. Outreach Engine & Multi-Channel Automation

- **Mode A (Assisted Outreach — Default & 100% Safe):**
  - Copies personalized AI drafts to your system clipboard and opens the lead's Instagram DM or WhatsApp Web profile in your default browser with a single click.
- **Mode B (Direct Automation — Optional):**
  - Logs into Instagram via simulated API (`instagrapi`) and sends direct messages directly from the database within configured daily rate limits.
- **WhatsApp Web & LinkedIn Automation:**
  - Employs Playwright persistent context browser profiles to automate messaging via WhatsApp Web and send connection requests ("Connect") with personalized notes on LinkedIn.

---

### 8. SMTP Pool, Multi-Stage Sequences & P2P Warmup Engine

- **SMTP Pool & Hourly Rate Control:**
  - Balances sending load across multiple configured SMTP accounts with strict limits (default: max 5 emails/hour per account). All credentials are encrypted with AES-256 Fernet.
- **Multi-Stage Cold Email Sequences:**
  - Runs automated sequence chains: Initial Email -> Follow-up 1 (after 3 days) -> Follow-up 2 (after 7 days). Follow-up sequence is automatically halted when an inbound reply is detected.
- **P2P Email Warmup Engine:**
  - Simulates natural email exchanges between configured accounts. Automatically monitors IMAP Spam/Junk folders, rescues landed emails to the Inbox, marks them as read, and improves overall domain deliverability.

---

### 9. Async Task Queue & Cron Scheduler

- **Async Task Queue:** Manages background execution (scraping, auditing, sending) via a single event loop transitioning through `pending -> running -> completed / failed` states with pause/cancel controls.
- **Cron Scheduler:** Periodically executes scheduled discovery routines, automated follow-up sequences, and inbox audits at specified time intervals.

---

### 10. Modern Desktop GUI & SQLite WAL Engine

- **PyWebView Dark Mode Dashboard:** Sleek, responsive desktop application. When launched without CLI arguments, console terminal windows are hidden automatically.
- **9-Language Complete i18n:** Built-in internationalization supporting English, Turkish, German, Spanish, French, Arabic (with automatic RTL layout), Chinese, Russian, and Hindi.
- **SQLite WAL Mode & Connection Pool:** Implements `PRAGMA journal_mode=WAL;` and SingletonPool / NullPool engine configurations to prevent database deadlocks and read/write latency.

---

## 🔒 Security, Privacy & Hardening

- **100% Local Data Storage:** All leads, credentials, settings, and conversation logs remain exclusively inside your local SQLite database (`data/aegisScout.db`).
- **Secrets Boundary:** API keys and passwords are never exposed to the JavaScript PyWebView bridge. Settings forms save keys directly to `.env`.
- **AES-256 Fernet Encryption:** Session tokens, passwords, and sensitive credentials are encrypted using AES-256 Fernet tokens prior to database persistence.

---

## 🛠️ Installation & Setup

### 1. Requirements
- **Python 3.11** or higher
- `uv` package manager (recommended for fast installation)

### 2. Installation Commands

```bash
# Clone repository and enter directory
git clone https://github.com/MrSpy00/aegisScout.git
cd aegisScout

# Basic Installation (Mode A - Assisted Outreach)
uv sync

# Install with Desktop GUI Dashboard
uv sync --extra gui

# Install with Full Automation (Mode B)
uv sync --extra mod-b

# Install with Developer & Testing Dependencies
uv sync --extra dev
```

> **Alternative Pip Install:** `pip install -e .`

### 3. Environment Configuration
1. Create a local `.env` file:
   ```bash
   copy .env.example .env
   ```
2. Fill in your API keys in `.env`.
3. Create your `config.toml`:
   ```bash
   copy config\config.example.toml config\config.toml
   ```

---

## 💻 Usage Guide (CLI & GUI)

### Launching Desktop Application
To launch the desktop GUI, double-click the executable or run main without arguments:
```bash
python src/aegisScout/main.py
# Or compiled executable:
dist/aegisScout.exe
```

### Essential CLI Commands

```bash
# 1. Discover Businesses
aegisScout discover --sector "barber" --location "London, UK" --radius 5

# 2. Campaign Management
aegisScout campaign create --name "London Salons" --sector "barber" --location "London"
aegisScout campaign list
aegisScout campaign assign --campaign-id 1 --auto-filter

# 3. Lead Research & AI Analysis
aegisScout research --lead-id 1
aegisScout research --lead-id 1 --force

# 4. Review & Outreach
aegisScout review
aegisScout send --lead-id 1

# 5. Waterfall Email Enrichment
aegisScout waterfall --lead-id 1

# 6. Web Visual Audit (Multimodal Audit)
aegisScout audit --lead-id 1

# 7. Email Verification (Local SMTP Handshake)
aegisScout verify "user@example.com"

# 8. P2P Email Warmup
aegisScout warmup

# 9. Background Task Management
aegisScout tasks list
aegisScout tasks cancel <task_id>

# 10. Data Export
aegisScout export --output data/exports/leads.csv
```

---

## ⚖️ Terms of Use & Legal Compliance

- **Instagram ToS Warning:** Using Mode B (Full Automation) may violate Meta/Instagram Terms of Service. Account safety requires observing daily rate limits (max 15-20 DMs/day) and utilizing secondary accounts.
- **Regulatory Compliance (GDPR, CAN-SPAM, KVKK):** The user is responsible for ensuring compliance with applicable data privacy and anti-spam legislation when harvesting public business details and initiating direct cold communication.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
