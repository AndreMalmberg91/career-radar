import anthropic
import json
import time
import os


def score_job(client, job):
    prompt = f"""Score this job 1-10 for Andre, a senior CSM/Account Manager with 7+ years SaaS experience targeting AUD $160K+ base.

Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Salary: {job.get('salary_raw', 'Not listed')}

Scoring guide:
- 9-10: AI-native company OR founding APAC CSM/AM role OR Series B-D US SaaS expanding to APAC OR banner brand with $160K+ base
- 7-8: Established tech/SaaS, senior CSM or Account Manager role, $140K+ likely, APAC or regional scope
- 5-6: Decent tech/SaaS company, standard CSM or AM role, comp unclear or $130-140K range
- 4: Legitimate SaaS company but mature/slow growth OR salary $120-130K OR not a banner brand
- 3: Traditional enterprise or non-SaaS but right title and $130K+
- 1-2: Wrong industry, wrong comp, clearly not a fit

Rules:
- Account Manager AND Customer Success titles score equally
- If salary listed $160K+ AUD, add 1 to score
- If salary listed $130K+ AUD, minimum score is 4
- No salary listed reduces score by 1 only for unknown companies
- Perth/Brisbane location (not remote) reduces score by 1

Return ONLY this JSON:
{{"score": 7, "reason": "one sentence", "company_stage": "startup", "red_flags": "none"}}"""

    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        result = json.loads(text[start:end])
        job["score"] = int(result.get("score", 5))
        job["score_reason"] = result.get("reason", "")
        job["company_stage"] = result.get("company_stage", "unknown")
        job["red_flags"] = result.get("red_flags", "none")
    except Exception as e:
        print(f"    Scoring failed for {job.get('company')}: {e}")
        job["score"] = 5
        job["score_reason"] = "Could not score automatically"
        job["company_stage"] = "unknown"
        job["red_flags"] = "none"
    return job


def score_jobs(jobs, config):
    if not jobs:
        return []
    print(f"  Scoring {len(jobs)} jobs with Haiku...")
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    min_score = config.get("min_score", 5)
    scored_jobs = []
    for i, job in enumerate(jobs):
        print(f"    Scoring {i+1}/{len(jobs)}: {job.get('company')} - {job.get('title')}")
        job = score_job(client, job)
        if job["score"] >= min_score:
            scored_jobs.append(job)
        time.sleep(0.3)
    scored_jobs.sort(key=lambda x: x["score"], reverse=True)
    print(f"  {len(scored_jobs)} jobs scored {min_score}+ (out of {len(jobs)})")
    return scored_jobs