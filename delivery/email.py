"""
delivery/email.py — Builds and sends the HTML email report.
"""

import smtplib
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime


def format_research(research: str) -> str:
    """Convert markdown research to clean HTML."""
    if not research:
        return ""
    text = research.strip()
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'^## (.*?)$', r'<br><strong style="color:#111827;font-size:13px;">\1</strong><br>', text, flags=re.MULTILINE)
    text = re.sub(r'^### (.*?)$', r'<br><strong style="color:#374151;font-size:12px;">\1</strong><br>', text, flags=re.MULTILINE)
    text = re.sub(r'^- (.*?)$', r'• \1<br>', text, flags=re.MULTILINE)
    text = text.replace('\n\n', '<br>')
    text = text.replace('\n', ' ')
    return f'<div style="font-size:12px;color:#374151;line-height:1.6;">{text}</div>'


def build_email_html(jobs: list, trends: dict, config: dict) -> str:
    """Build the HTML content for the email report."""
    
    now = datetime.now().strftime("%A %d %B %Y")
    total_found = len(jobs)
    
    def score_colour(score):
        if score >= 8:
            return "#22c55e"
        elif score >= 6:
            return "#f59e0b"
        else:
            return "#94a3b8"

    job_cards = ""
    for i, job in enumerate(jobs):
        score = job.get("score", 0)
        research = job.get("research_summary", "")
        
        research_html = format_research(research) if research else f'<p style="font-size:12px;color:#6b7280;">{job.get("score_reason", "")}</p>'

        job_cards += f"""
        <div style='background:#fff;border:1px solid #e5e7eb;border-radius:8px;
                    padding:20px;margin-bottom:16px;'>
            <div style='display:flex;align-items:center;gap:12px;margin-bottom:12px;'>
                <span style='background:{score_colour(score)};color:#fff;
                            font-weight:700;font-size:18px;padding:6px 14px;
                            border-radius:6px;'>
                    {score}/10
                </span>
                <div>
                    <div style='font-size:16px;font-weight:600;color:#111827;'>
                        {job.get('title', 'Unknown Role')}
                    </div>
                    <div style='font-size:14px;color:#6b7280;'>
                        {job.get('company', 'Unknown Company')} · 
                        {job.get('location', 'Location unknown')} · 
                        via {job.get('source', 'Unknown')}
                    </div>
                </div>
            </div>
            
            <div style='background:#f9fafb;border-radius:6px;padding:12px;margin-bottom:12px;'>
                {research_html}
            </div>
            
            {f"<div style='font-size:12px;color:#ef4444;margin-bottom:8px;'>⚠ {job.get('red_flags')}</div>" if job.get('red_flags') and job.get('red_flags') != 'none' else ""}
            
            {f"<div style='font-size:13px;color:#6b7280;margin-bottom:8px;'>💰 {job.get('salary_raw')}</div>" if job.get('salary_raw') else ""}
            
            <a href='{job.get('url', '#')}' 
               style='display:inline-block;background:#1d4ed8;color:#fff;
                      padding:8px 16px;border-radius:6px;text-decoration:none;
                      font-size:13px;font-weight:500;'>
                View & Apply →
            </a>
        </div>
        """

    highlights_html = ""
    if trends.get("highlights"):
        highlights_html = "<ul style='margin:8px 0;padding-left:20px;'>"
        for bullet in trends["highlights"]:
            highlights_html += f"<li style='font-size:14px;color:#374151;margin-bottom:4px;'>{bullet}</li>"
        highlights_html += "</ul>"

    expansion_html = ""
    if trends.get("expansion_suggestions"):
        roles = ", ".join(trends["expansion_suggestions"])
        expansion_html = f'<p style="font-size:13px;color:#6b7280;margin-top:8px;">💡 <strong>Consider also watching:</strong> {roles}</p>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style='font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
                 background:#f3f4f6;margin:0;padding:20px;'>
        
        <div style='max-width:680px;margin:0 auto;'>
            
            <div style='background:#1d4ed8;border-radius:8px;padding:24px;margin-bottom:16px;'>
                <h1 style='color:#fff;margin:0;font-size:22px;'>📡 Career Radar</h1>
                <p style='color:#bfdbfe;margin:4px 0 0;font-size:14px;'>
                    {now} · {total_found} roles found above threshold
                </p>
            </div>
            
            <div style='background:#fff;border:1px solid #e5e7eb;border-radius:8px;
                        padding:20px;margin-bottom:16px;'>
                <h2 style='margin:0 0 12px;font-size:16px;color:#111827;'>📊 Market Intelligence</h2>
                <p style='font-size:14px;color:#374151;margin:0 0 8px;'>
                    <strong>{trends.get('market_health', 'Analysing market...')}</strong>
                </p>
                {highlights_html}
                {expansion_html}
            </div>
            
            <h2 style='font-size:16px;color:#111827;margin:0 0 12px;'>
                🎯 Roles Ranked by Fit ({total_found} above threshold)
            </h2>
            
            {job_cards if job_cards else "<p style='color:#6b7280;'>No new roles found this run.</p>"}
            
            <div style='text-align:center;padding:16px;'>
                <p style='font-size:12px;color:#9ca3af;margin:0;'>
                    Career Radar · Powered by Claude · 
                    <a href='https://github.com/AndreMalmberg91/career-radar' style='color:#9ca3af;'>GitHub</a>
                </p>
            </div>
            
        </div>
    </body>
    </html>
    """
    
    return html


def send_email(jobs: list, trends: dict, config: dict):
    """Send the job report email via Gmail SMTP."""
    
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    recipient = os.getenv("RECIPIENT_EMAIL")
    
    if not all([gmail_user, gmail_password, recipient]):
        print("  Email credentials not set — skipping email send.")
        return
    
    print(f"  Sending email to {recipient}...")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"{config.get('email', {}).get('subject', 'Career Radar')} — {len(jobs)} roles"
    msg["From"] = f"{config.get('email', {}).get('from_name', 'Career Radar')} <{gmail_user}>"
    msg["To"] = recipient
    
    html_content = build_email_html(jobs, trends, config)
    msg.attach(MIMEText(html_content, "html"))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, gmail_password)
            server.sendmail(gmail_user, recipient, msg.as_string())
        print("  Email sent successfully!")
    except Exception as e:
        print(f"  Email failed: {e}")