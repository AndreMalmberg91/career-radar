"""
database/storage.py — SQLite database for storing job listings and run history.

This is the memory of the agent. Every job found, every run completed,
and all the data needed for trend analysis lives here.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path


def get_connection(db_path: str) -> sqlite3.Connection:
    """Create and return a database connection."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Returns rows as dicts
    return conn


def init_database(db_path: str):
    """Create all tables if they don't exist yet."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # Table for individual job listings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT,
            source TEXT,
            url TEXT,
            salary_min INTEGER,
            salary_max INTEGER,
            salary_raw TEXT,
            score INTEGER,
            research_summary TEXT,
            date_found TEXT NOT NULL,
            run_id INTEGER,
            is_remote INTEGER DEFAULT 0,
            UNIQUE(company, title, date_found)
        )
    """)

    # Table for each run of the agent
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            total_found INTEGER DEFAULT 0,
            total_scored INTEGER DEFAULT 0,
            total_above_threshold INTEGER DEFAULT 0,
            sources_used TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_run(db_path: str, run_data: dict) -> int:
    """Save a run record and return its ID."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO runs (run_date, total_found, total_scored, 
                         total_above_threshold, sources_used)
        VALUES (?, ?, ?, ?, ?)
    """, (
        run_data.get("run_date", datetime.now().isoformat()),
        run_data.get("total_found", 0),
        run_data.get("total_scored", 0),
        run_data.get("total_above_threshold", 0),
        json.dumps(run_data.get("sources_used", []))
    ))

    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def save_job(db_path: str, job: dict, run_id: int):
    """Save a job listing. Ignores duplicates from the same day."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO jobs 
            (title, company, location, source, url, salary_min, salary_max,
             salary_raw, score, research_summary, date_found, run_id, is_remote)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("title"),
            job.get("company"),
            job.get("location"),
            job.get("source"),
            job.get("url"),
            job.get("salary_min"),
            job.get("salary_max"),
            job.get("salary_raw"),
            job.get("score"),
            job.get("research_summary"),
            datetime.now().strftime("%Y-%m-%d"),
            run_id,
            1 if job.get("is_remote") else 0
        ))
        conn.commit()
    finally:
        conn.close()


def get_jobs_since(db_path: str, days: int) -> list:
    """Get all jobs found in the last N days for trend analysis."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT * FROM jobs WHERE date_found >= ?
        ORDER BY date_found DESC
    """, (since_date,))

    jobs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jobs


def get_runs_since(db_path: str, days: int) -> list:
    """Get all runs in the last N days for trend analysis."""
    conn = get_connection(db_path)
    cursor = conn.cursor()

    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT * FROM runs WHERE run_date >= ?
        ORDER BY run_date DESC
    """, (since_date,))

    runs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return runs


def get_seen_jobs(db_path: str, days: int = 3) -> set:
    """
    Get set of (company, title) tuples seen recently.
    Used to avoid showing the same job twice in consecutive runs.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()

    since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT company, title FROM jobs WHERE date_found >= ?
    """, (since_date,))

    seen = {(row["company"].lower(), row["title"].lower()) 
            for row in cursor.fetchall()}
    conn.close()
    return seen