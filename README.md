# 📡 Career Radar

An AI-powered job market intelligence agent that finds, scores and ranks roles across 10+ job boards — delivered to your inbox automatically with market trend analysis. Fully configurable for any role, location or industry.

## What it does

Career Radar runs every Monday, Wednesday and Friday at 7am and:

1. **Scrapes** 10+ job boards (Seek, Indeed, Wellfound, Greenhouse, Lever, 7 VC portfolio boards)
2. **Filters** by your target job titles and locations
3. **Scores** every role 1-10 using Claude Haiku (fast and cheap)
4. **Deep researches** top roles using Claude Sonnet — funding, growth, comp in AUD, career risk verdict
5. **Analyses trends** — volume changes, salary movements, new companies hiring
6. **Emails** you a ranked report, highest scoring roles first

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/career-radar.git
cd career-radar
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your environment

```bash
cp .env.example .env
```

Edit `.env` with your own values:

- `ANTHROPIC_API_KEY` — get from [console.anthropic.com](https://console.anthropic.com)
- `GMAIL_USER` — your Gmail address
- `GMAIL_APP_PASSWORD` — a Gmail app password (not your regular password)
- `RECIPIENT_EMAIL` — where to send the report

**How to get a Gmail app password:**
1. Go to [myaccount.google.com](https://myaccount.google.com)
2. Security → 2-Step Verification → App passwords
3. Create a new app password for "Mail"
4. Copy the 16-character password into your `.env`

### 4. Configure your search

Edit `config.yaml` to set your job titles, locations and minimum score threshold.

### 5. Test it locally

```bash
# Test with mock data (no API calls)
python main.py --test

# Run for real (scrapes live, uses API)
python main.py

# Run and send email
python main.py --send-email
```

The HTML report is saved to `reports/` so you can preview it in your browser.

## Deploy to GitHub Actions (runs automatically)

### 1. Push to GitHub

```bash
git add .
git commit -m "Initial setup"
git push
```

### 2. Add your secrets to GitHub

Go to your repo → Settings → Secrets and variables → Actions → New repository secret

Add these four secrets:
- `ANTHROPIC_API_KEY`
- `GMAIL_USER`
- `GMAIL_APP_PASSWORD`
- `RECIPIENT_EMAIL`

### 3. Enable Actions

Go to the Actions tab in your repo and enable workflows. The agent will now run automatically every Monday, Wednesday and Friday at 7am Sydney time.

You can also trigger it manually from the Actions tab at any time.

## Cost

Approximately **$2-5 AUD per month** in Anthropic API credits.

- Claude Haiku scores all roles (~$0.001 per role)
- Claude Sonnet deep researches top 5 roles only (~$0.15 per run)
- GitHub Actions runs free (well within the free tier)
- Gmail SMTP is free

## Customising for your own search

Edit `config.yaml`:

```yaml
job_titles:
  - "Your Target Role"
  - "Another Role"

locations:
  onsite:
    - "Melbourne"  # Change to your city
  remote:
    - "Australia"

min_score: 5  # Raise to 6 or 7 for stricter filtering
```

Add companies to `scrapers/greenhouse.py` and `scrapers/lever.py` as you discover them using those ATS platforms.

## Built with

- [Anthropic Claude](https://anthropic.com) — Haiku for scoring, Sonnet for research
- [GitHub Actions](https://github.com/features/actions) — free automated scheduling
- Python, BeautifulSoup, SQLite, Gmail SMTP

## License

MIT — fork it, adapt it, use it for your own job search.