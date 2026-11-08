# Review-first Naukri application workflow

## User settings
- Candidate: 2026 B.Tech Artificial Intelligence & Data Science graduate; fresher, 0 years professional experience.
- Search platform: Naukri only.
- Locations: Hyderabad, Telangana and Remote India.
- Target: all relevant fresher, graduate, trainee, internship and 0–1 year listings; exclude roles requiring more than one year unless freshers are explicitly accepted.
- Mode: review before submission.

## Daily discovery
The scheduled Naukri search looks at the previous 48 hours first and expands to seven days only when needed. It returns all relevant matches, deduplicated by job URL and employer/title/location. Each result includes the original listing URL, posted date when available, location, work mode, experience, salary when disclosed, match score, matched/missing skills, eligibility and verification notes.

## Application preparation
1. Search returns Naukri job links only; it does not log in or interact with a Naukri account.
2. The agent compares job requirements with verified profile skills and applies the existing entry-level eligibility rules.
3. A candidate can be prepared for review. The agent generates a cover-letter draft and records a PENDING_USER_REVIEW application state.
4. The user checks the actual listing, the resume, every answer and the cover-letter draft.
5. The user opens the original Naukri listing and submits the application manually.

## Safety gates
- Search and batch preparation never submit applications.
- The /api/jobs/{job_id}/apply compatibility endpoint now only prepares a review.
- The /api/jobs/{job_id}/submit endpoint rejects requests unless that individual job includes review_approved=true.
- The built-in provider is a safe stub. No Naukri API integration is configured, and the app must not automate login, CAPTCHA, OTP, 2FA, or anti-bot controls.
- Unknown application questions remain manual-review items.
- Never invent work experience, education, marks, skills, certifications, salary history or answers.
- Never pay recruitment, registration, interview or placement fees.

## Local setup
1. Keep secrets in .env; never commit API keys.
2. Configure TAVILY_API_KEY if using the app's Naukri web-search adapter. It queries publicly indexed Naukri job pages and is not an official Naukri API.
3. Run uvicorn app.main:app --reload and open http://127.0.0.1:8000.
4. Upload the current PDF resume, verify extracted details, then search with Naukri only and Hyderabad OR Remote India.
5. Review every job and generated application material before applying manually.

## Known limitations
Publicly indexed search results may be incomplete, stale or missing exact location/experience details. Open the original listing to verify that the job is active and that freshers are eligible. CAPTCHA, OTP, login-only pages and inaccessible listings require the user to handle them directly.
