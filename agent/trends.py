"""
agent/trends.py — Analyses job market trends from historical data.

Compares current run against the last 14 days to surface:
- Volume changes (more or fewer roles being posted)
- Salary trends (are advertised salaries going up or down)
- New companies entering the market
- Role title shifts (what titles are growing/shrinking)
- Market health signals
- Suggestions for expanding your search
"""

from datetime import datetime, timedelta
from database.storage import get_jobs_since, get_runs_since
from collections import Counter


def calculate_trends(db_path: str, current_jobs: list, config: dict) -> dict:
    """
    Calculate market trends by comparing current jobs against history.
    Returns a trends dict used in the email report.
    """
    window_days = config.get("database", {}).get("trend_window_days", 14)
    
    # Get historical data
    historical_jobs = get_jobs_since(db_path, window_days)
    historical_runs = get_runs_since(db_path, window_days)
    
    trends = {
        "has_history": len(historical_jobs) > 0,
        "window_days": window_days,
        "current_count": len(current_jobs),
        "historical_count": len(historical_jobs),
        "volume_change": None,
        "salary_trend": None,
        "new_companies": [],
        "title_shifts": [],
        "market_health": "",
        "expansion_suggestions": [],
        "highlights": []
    }
    
    if not historical_jobs:
        trends["market_health"] = "Not enough history yet — trends will appear after a few runs."
        return trends
    
    # --- Volume trend ---
    # Compare current run size against average run size
    if historical_runs:
        avg_per_run = len(historical_jobs) / max(len(historical_runs), 1)
        if avg_per_run > 0:
            change_pct = ((len(current_jobs) - avg_per_run) / avg_per_run) * 100
            trends["volume_change"] = round(change_pct, 1)
    
    # --- New companies ---
    historical_companies = {j["company"].lower() for j in historical_jobs}
    current_companies = {j["company"].lower() for j in current_jobs}
    new_companies = current_companies - historical_companies
    trends["new_companies"] = list(new_companies)[:5]  # Top 5
    
    # --- Title shifts ---
    historical_titles = Counter(
        _normalise_title(j["title"]) for j in historical_jobs
    )
    current_titles = Counter(
        _normalise_title(j["title"]) for j in current_jobs
    )
    
    title_changes = []
    all_titles = set(historical_titles.keys()) | set(current_titles.keys())
    for title in all_titles:
        hist_count = historical_titles.get(title, 0)
        curr_count = current_titles.get(title, 0)
        if hist_count > 0 and curr_count > hist_count:
            pct = ((curr_count - hist_count) / hist_count) * 100
            title_changes.append(f"{title} roles up {round(pct)}%")
        elif hist_count > 0 and curr_count < hist_count:
            pct = ((hist_count - curr_count) / hist_count) * 100
            title_changes.append(f"{title} roles down {round(pct)}%")
    
    trends["title_shifts"] = title_changes[:3]
    
    # --- Salary trend ---
    historical_salaries = [
        j["salary_max"] for j in historical_jobs 
        if j.get("salary_max") and j["salary_max"] > 0
    ]
    current_salaries = [
        j.get("salary_max") for j in current_jobs 
        if j.get("salary_max") and j.get("salary_max", 0) > 0
    ]
    
    if historical_salaries and current_salaries:
        hist_avg = sum(historical_salaries) / len(historical_salaries)
        curr_avg = sum(current_salaries) / len(current_salaries)
        salary_change = ((curr_avg - hist_avg) / hist_avg) * 100
        trends["salary_trend"] = round(salary_change, 1)
    
    # --- Market health ---
    trends["market_health"] = _assess_market_health(trends)
    
    # --- Expansion suggestions ---
    trends["expansion_suggestions"] = _suggest_expansions(
        historical_titles, current_titles
    )
    
    # --- Highlight bullets ---
    trends["highlights"] = _build_highlights(trends)
    
    return trends


def _normalise_title(title: str) -> str:
    """Normalise job titles for comparison."""
    title = title.lower()
    if "enterprise" in title:
        return "Enterprise CSM"
    if "senior" in title or "sr." in title:
        return "Senior CSM"
    if "founding" in title:
        return "Founding CSM"
    if "lead" in title:
        return "CS Lead"
    if "account manager" in title:
        return "Account Manager"
    if "customer success" in title:
        return "CSM"
    return "Other"


def _assess_market_health(trends: dict) -> str:
    """Generate a market health summary string."""
    volume_change = trends.get("volume_change")
    
    if volume_change is None:
        return "Market activity looks normal."
    elif volume_change > 30:
        return f"Hiring is accelerating — {volume_change}% more roles than usual. Good time to be active."
    elif volume_change > 10:
        return f"Hiring is slightly up ({volume_change}%). Market is healthy."
    elif volume_change < -30:
        return f"Posting volume is down {abs(volume_change)}% — possible market slowdown or seasonal dip."
    elif volume_change < -10:
        return f"Slightly fewer postings than usual ({volume_change}%). Consider broadening search."
    else:
        return "Market volume is steady — consistent with recent weeks."


def _suggest_expansions(historical_titles: Counter, current_titles: Counter) -> list:
    """Suggest adjacent roles worth watching."""
    suggestions = [
        "Revenue Operations Manager",
        "CS Operations Manager", 
        "Head of Customer Success",
        "Partnership Manager",
        "Solutions Engineer"
    ]
    # Return a static list for now — can be made dynamic later
    return suggestions[:3]


def _build_highlights(trends: dict) -> list:
    """Build the bullet point highlights for the email."""
    bullets = []
    
    # Volume
    if trends["volume_change"] is not None:
        direction = "up" if trends["volume_change"] > 0 else "down"
        bullets.append(
            f"Job volume is {direction} {abs(trends['volume_change'])}% vs the last {trends['window_days']} days"
        )
    
    # Salary
    if trends["salary_trend"] is not None:
        direction = "increased" if trends["salary_trend"] > 0 else "decreased"
        bullets.append(
            f"Advertised salaries have {direction} {abs(trends['salary_trend'])}% on average"
        )
    
    # New companies
    if trends["new_companies"]:
        companies = ", ".join(trends["new_companies"][:3])
        bullets.append(f"New companies posting this week: {companies}")
    
    # Title shifts
    bullets.extend(trends["title_shifts"][:2])
    
    return bullets