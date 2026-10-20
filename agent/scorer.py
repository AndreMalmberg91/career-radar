import anthropic
import json
import time
import os


def score_job(client, job):
    prompt = f"""Score this job 1-10 for André, a senior CSM/Account Manager with 7+ years SaaS experience targeting AUD $160K+ base salary.

Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Salary: {job.get('salary_raw', 'Not listed')}

Scoring guide:
- 9-10: AI-native company (Harvey, Anthropic, OpenAI, Cohere type) OR founding APAC CSM/AM role OR Series B-D SaaS expanding to APAC (US or European) OR banner brand (Salesforce, Atlassian, Canva, HubSpot) with strong comp signals
- 7-8: Established tech/SaaS company, senior CSM or Account Manager role, APAC or regional scope, growth signals present
- 5-6: Decent tech/SaaS company, standard CSM or AM role, limited growth signals
- 4: Legitimate SaaS company but mature/slow growth OR clearly below $130K base
- 3: Traditional enterprise or non-SaaS but right title
- 1-2: Wrong industry, wrong comp, clearly not a fit

Rules:
- Account Manager AND Customer Success titles score equally — never penalise AM titles
- No salary listed = neutral, never a penalty. Most Australian companies don't list salary
- Only penalise salary if it is explicitly listed AND clearly below $130K AUD base salary (ignore OTE, bonus or total package figures)
- Harvey is a top-tier AI legal company — score 9 minimum
- Askable, Rokt, HiBob, Workato, Dialpad, Canva, Atlassian, SafetyCulture — score 7+ minimum
- Any role requiring onsite/hybrid work outside Sydney (Brisbane, Perth, Melbourne, Adelaide etc) should score maximum 3 — André is Sydney-based and cannot relocate
- Remote roles anywhere in Australia or APAC are fine and should not be penalised for location

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