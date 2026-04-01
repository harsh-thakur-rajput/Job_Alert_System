# Smart Job Alert System

Smart Job Alert System is a Python project that collects jobs from multiple sources, filters low-quality/scam-like postings, ranks the best matches, stores unique jobs in SQLite, and sends smart alerts to Telegram or Email.

Built for freshers and early-career developers who want fewer junk alerts and more relevant roles.

## Features

- Multi-source job collection (pluggable source architecture)
- Structured extraction: title, company, location, salary, URL, description
- Smart filtering:
  - include/exclude keywords
  - experience range checks (for fresher/junior targeting)
  - optional location filtering
- Scam/suspicious job detection rules:
  - payment keywords
  - domain checks
  - low-quality description heuristics
- SQLite storage with duplicate prevention (URL hash based)
- Ranking system (keyword + recency + salary signals)
- Feedback loop (`liked` / `disliked`) for preference learning over time
- Alerts:
  - Telegram (recommended)
  - Email (SMTP)
- Scheduler support (run every N hours)

## Current Sources

Enabled-by-default stable sources in this repo:

- Remotive API
- LinkedIn jobs guest endpoint
- Internshala scraper

Additional implemented sources (can be enabled in config, may be blocked by anti-bot rules):

- Indeed scraper
- Naukri scraper
- Foundit scraper
- Generic RSS source

## Tech Stack

- Python 3.11+
- Requests + BeautifulSoup
- SQLite
- APScheduler
- YAML config

## Project Structure

```text
smart_job_alert/
  cli.py                 # CLI entrypoint
  orchestrator.py        # Full pipeline: fetch -> filter -> rank -> store -> alert
  config.py              # Config schema + loader + default config writer
  db.py                  # SQLite schema and storage helpers
  filters.py             # User filters (keywords/experience/location)
  scam.py                # Scam detection heuristics
  ranking.py             # Ranking logic
  alerts.py              # Telegram + Email delivery
  scheduler.py           # Periodic job runner
  sources/               # Source connectors (Remotive, LinkedIn, Internshala, etc.)
```

## Setup

### 1) Clone and enter the project

```bash
git clone <your-repo-url>
cd Job_Alert_project
```

### 2) Create virtual environment

Windows (PowerShell):

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Create starter config

```bash
python -m smart_job_alert init-config
```

This creates `config.yaml` in the project root.

## Configuration

Main file: `config.yaml`

Important sections:

- `filters`: role keywords, exclude terms, experience cap, locations
- `sources`: enable/disable job sources and customize query/location
- `ranking`: alert score threshold and max jobs per alert
- `telegram`: bot token + chat ID
- `email`: SMTP settings
- `scheduler`: interval hours

### Telegram Setup

```yaml
telegram:
  enabled: true
  bot_token: "YOUR_BOT_TOKEN"
  chat_id: "YOUR_CHAT_ID"
```

## Usage

### Run one cycle

```bash
python -m smart_job_alert run-once --config config.yaml
```

### Run scheduler (every 8 hours by default)

```bash
python -m smart_job_alert run-scheduler --config config.yaml
```

### Provide feedback for learning

```bash
python -m smart_job_alert feedback --config config.yaml --url "<job-url>" --liked
python -m smart_job_alert feedback --config config.yaml --url "<job-url>" --disliked
```

## Where To See Results

- Terminal output after each run (fetched/filtered/inserted/alerted counts)
- Telegram chat (if enabled)
- SQLite database file: `jobs.db`

Example quick DB check:

```bash
python -c "import sqlite3; c=sqlite3.connect('jobs.db'); c.row_factory=sqlite3.Row; rows=c.execute('select title, company, location, score, url from jobs where is_scam=0 order by created_at desc limit 20').fetchall(); [print(f'{i+1}. {r[\"title\"]} | {r[\"company\"]} | {r[\"location\"]} | score={r[\"score\"]:.2f}\n   {r[\"url\"]}') for i,r in enumerate(rows)]"
```

## Notes and Limitations

- Some job sites aggressively block scraping with 403/CAPTCHA; this project handles many failures gracefully and continues with available sources.
- Selectors for HTML scrapers may need updates when site markup changes.
- Prefer official APIs or permitted feeds whenever available.

## Security Tips

- Do not commit secrets (`bot_token`, SMTP passwords) to public repos.
- Use environment variables or private config files for production use.

## Roadmap

- Better dedupe beyond URL hash (content similarity)
- More robust anti-spam ranking signals
- Lightweight dashboard/GUI
- Cloud deployment templates (Render/Railway/AWS)
- Automated tests for each source parser

## License

Choose a license before publishing (MIT is a common default for personal projects).

