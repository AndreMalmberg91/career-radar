import anthropic
import time
import os


def research_job(client, job):
    prompt = f"""Brief company assessment for a job seeker. 100 words max.

Company: {job.get('company')}
Role: {job.get('title')}
Location: {job.get('location')}

Format:
STAGE: [funding stage]
GROWTH: [growing/stable/declining]
VERDICT: [Worth it/Caution/Avoid] - [why]
SALARY: [estimated AUD base]
JOIN: [one reason]
AVOID: [one reason]"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        job["research_summary"] = response.content[0].text.strip()
    except Exception as e:
        print(f"    Research failed for {job.get('company')}: {e}")
        job["research_summary"] = None
    return job


def research_top_jobs(jobs, config):
    if not jobs:
        return []
    print(f"  Researching {len(jobs)} jobs with Haiku...")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    for i, job in enumerate(jobs):
        print(f"    {i+1}/{len(jobs)}: {job.get('company')} - {job.get('title')}")
        job = research_job(client, job)
        time.sleep(0.2)
    print(f"  Research complete.")
    return jobs