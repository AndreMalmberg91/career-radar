"""
main.py — The orchestrator for Career Radar.

This is the entry point that runs the full pipeline:
1. Load config and environment variables
2. Initialise the database
3. Scrape all job boards
4. Filter and deduplicate
5. Score with Haiku
6. Deep research top roles with Sonnet
7. Calculate market trends
8. Send email report
9. Save results to database

Run manually:   python main.py
Run with email: python main.py --send-email
Test mode:      python main.py --test
"""

import argparse
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import yaml

# Load environment variables from .env file
load_dotenv()

# Import all modules
from database.storage import init_database, save_run, save_job
from scrapers.seek import scrape_seek
from scrapers.indeed import scrape_indeed
from scrapers.wellfound import scrape_wellfound
from scrapers.greenhouse import scrape_greenhouse
from scrapers.lever import scrape_lever
from scrapers.vc_boards import scrape_vc_boards
from agent.filter import filter_jobs
from agent.scorer import score_jobs
from agent.researcher import research_top_jobs
from agent.trends import calculate_trends
from delivery.email import send_email, build_email_html


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def run_scrapers(config: dict, test_mode: bool = False) -> list:
    """Run all scrapers and return combined raw job list."""
    all_jobs = []

    if test_mode:
        print("  TEST MODE — using mock data instead of scraping")
        # Return a small set of test jobs
        return [
            {
                "title": "Senior Customer Success Manager",
                "company": "Test Company A",
                "location": "Sydney NSW",
                "url": "https://example.com/job1",
                "salary_raw": "$130,000 - $160,000",
                "salary_min": 130000,
                "salary_max": 160000,
                "source": "Test",
                "is_remote": False
            },
            {
                "title": "Enterprise Customer Success Manager",
                "company": "Test Startup B",
                "location": "Remote - Australia",
                "url": "https://example.com/job2",
                "salary_raw": "$150,000 - $180,000",
                "salary_min": 150000,
                "salary_max": 180000,
                "source": "Test",
                "is_remote": True
            },
            {
                "title": "Account Manager",
                "company": "Test Scaleup C",
                "location": "Sydney CBD",
                "url": "https://example.com/job3",
                "salary_raw": None,
                "salary_min": None,
                "salary_max": None,
                "source": "Test",
                "is_remote": False
            },
        ]

    scrapers = [
        ("Seek", scrape_seek),
        ("Indeed", scrape_indeed),
        ("Wellfound", scrape_wellfound),
        ("Greenhouse", scrape_greenhouse),
        ("Lever", scrape_lever),
        ("VC Boards", scrape_vc_boards),
    ]

    for name, scraper_fn in scrapers:
        print(f"\n  Running {name} scraper...")
        try:
            jobs = scraper_fn(config)
            all_jobs.extend(jobs)
            print(f"  {name}: {len(jobs)} jobs found")
        except Exception as e:
            print(f"  {name} scraper failed: {e}")
            continue

    return all_jobs


def main():
    """Main entry point — runs the full Career Radar pipeline."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Career Radar — AI Job Market Intelligence")
    parser.add_argument("--send-email", action="store_true", help="Send email report")
    parser.add_argument("--test", action="store_true", help="Run in test mode with mock data")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Career Radar — {datetime.now().strftime('%A %d %B %Y %H:%M')}")
    print(f"{'='*60}\n")

    # Load config
    print("Loading config...")
    config = load_config(args.config)
    db_path = config.get("database", {}).get("path", "database/jobs.db")

    # Initialise database
    print("Initialising database...")
    init_database(db_path)

    # Step 1 — Scrape all sources
    print("\n[1/6] Scraping job boards...")
    raw_jobs = run_scrapers(config, test_mode=args.test)
    print(f"\n  Total raw jobs scraped: {len(raw_jobs)}")

    # Step 2 — Filter and deduplicate
    print("\n[2/6] Filtering and deduplicating...")
    filtered_jobs = filter_jobs(raw_jobs, config, db_path)

    if not filtered_jobs:
        print("\n  No new relevant jobs found this run.")
        if args.send_email:
            # Send empty report so you know it ran
            trends = calculate_trends(db_path, [], config)
            send_email([], trends, config)
        return

    # Step 3 — Score with Haiku
    print(f"\n[3/6] Scoring {len(filtered_jobs)} jobs with Claude Haiku...")
    scored_jobs = score_jobs(filtered_jobs, config)

    if not scored_jobs:
        print("\n  No jobs met the minimum score threshold.")
        return

    # Step 4 — Deep research top roles with Sonnet
    print(f"\n[4/6] Deep researching top roles with Claude Sonnet...")
    researched_jobs = research_top_jobs(scored_jobs, config)

    # Step 5 — Calculate trends
    print(f"\n[5/6] Calculating market trends...")
    trends = calculate_trends(db_path, researched_jobs, config)

    # Step 6 — Save to database
    print(f"\n[6/6] Saving results to database...")
    run_id = save_run(db_path, {
        "run_date": datetime.now().strftime("%Y-%m-%d"),
        "total_found": len(raw_jobs),
        "total_scored": len(scored_jobs),
        "total_above_threshold": len(researched_jobs),
        "sources_used": ["Seek", "Indeed", "Wellfound", "Greenhouse", "Lever", "VC Boards"]
    })

    for job in researched_jobs:
        save_job(db_path, job, run_id)

    print(f"  Saved {len(researched_jobs)} jobs to database (run #{run_id})")

    # Print summary to terminal
    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"  Raw jobs scraped:     {len(raw_jobs)}")
    print(f"  After filtering:      {len(filtered_jobs)}")
    print(f"  Above score threshold: {len(researched_jobs)}")
    print(f"\n  TOP ROLES:")
    for i, job in enumerate(researched_jobs[:5]):
        print(f"  #{i+1} [{job.get('score')}/10] {job.get('company')} — {job.get('title')}")

    print(f"\n  Market: {trends.get('market_health', '')}")

    # Send email if requested
    if args.send_email:
        print(f"\n  Sending email report...")
        send_email(researched_jobs, trends, config)
    else:
        print(f"\n  Run with --send-email to receive the report in your inbox.")
        print(f"  Run with --test to test without scraping.")

    # Save HTML report locally for preview
    html = build_email_html(researched_jobs, trends, config)
    report_path = f"reports/report-{datetime.now().strftime('%Y-%m-%d')}.html"
    os.makedirs("reports", exist_ok=True)
    with open(report_path, "w") as f:
        f.write(html)
    print(f"\n  HTML report saved to: {report_path}")
    print(f"  Open it in your browser to preview the email.\n")


if __name__ == "__main__":
    main()