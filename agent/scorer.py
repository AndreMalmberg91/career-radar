    prompt = f"""Score this job 1-10 for André, a senior CSM/Account Manager with 7+ years SaaS experience targeting AUD $160K+ base.

Title: {job.get('title')}
Company: {job.get('company')}
Location: {job.get('location')}
Salary: {job.get('salary_raw', 'Not listed')}

Scoring guide:
- 9-10: AI-native company OR founding APAC CSM/AM role OR Series B-D US SaaS expanding to APAC OR banner brand (Salesforce, Atlassian, Canva, HubSpot) with $160K+ base
- 7-8: Established tech/SaaS, senior CSM or Account Manager role, $140K+ likely, APAC or regional scope
- 5-6: Decent tech/SaaS company, standard CSM or AM role, comp unclear or $130-140K range
- 4: Legitimate SaaS company but mature/slow growth OR salary $120-130K OR not a banner brand
- 3: Traditional enterprise or non-SaaS but right title and $130K+
- 1-2: Wrong industry, wrong comp, clearly not a fit

Rules:
- Account Manager AND Customer Success titles score equally — never penalise AM titles
- If salary listed $160K+ AUD, add 1 to score
- If salary listed $130K+ AUD, minimum score is 4
- No salary listed reduces score by 1 only for unknown companies
- Perth/Brisbane location (not remote) reduces score by 1

Return ONLY this JSON:
{{"score": 7, "reason": "one sentence", "company_stage": "startup", "red_flags": "none"}}"""