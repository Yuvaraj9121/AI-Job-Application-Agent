# AI Job Application Agent — Search → Match → Apply

A FastAPI application that lets you upload a PDF resume, search jobs, match the job against verified resume skills, and prepare an application candidate automatically.

## Core rule

- **2 or more verified resume skills matched → APPLICATION_CANDIDATE**
- **0–1 matched skills → REJECTED**
- Senior/lead/principal or clearly high-experience roles are rejected by the configured entry-level eligibility rule.
- The system does not invent qualifications or experience.
- Duplicate applications are blocked by the application state layer.

## Run on Windows

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

Open:

- http://127.0.0.1:8000 — user interface
- http://127.0.0.1:8000/docs — API documentation

## User workflow

1. Upload a **text-based PDF resume**.
2. The app extracts contact information and recognizable skills.
3. Enter a role/keyword and optional location.
4. Click **Search & Match with AI**.
5. Jobs are fetched from configured real public/API feeds. When `TAVILY_API_KEY` is configured, the app also performs live API-backed web search for current job pages from LinkedIn, Naukri, Indeed, Greenhouse, Lever, Workday, and other indexed sources. There are no fallback demo jobs.
6. Each job is matched against the verified resume skills.
7. Only jobs with **2+ matched skills** receive the **Apply with AI** button.
8. Apply with AI prepares the application, including a cover letter based on the current uploaded profile.
9. Actual external submission occurs only through an authorized provider integration. The included provider is deliberately a safe stub; it does not log into LinkedIn/Naukri/Indeed or bypass CAPTCHA, OTP, 2FA, authentication, anti-bot systems, or rate limits.

## Real external submission

To make a real platform submit applications automatically, an authorized API/provider must be implemented in `app/providers.py` and configured with that provider's documented credentials and permissions. The UI is already structured so that the provider response can be surfaced after **Apply with AI**.

## Tests

```powershell
pytest
```

The included test suite covers the matching rule, application logic, API routes, resume parsing, and search matching.


## User workflow

Open `http://127.0.0.1:8000/` (not `/docs`) for the application UI. The UI supports:

1. Upload a text-based PDF resume.
2. Extract verified profile information and skills.
3. Search jobs by role/keyword and optional location.
4. Apply the configured rule: **2+ matched verified skills = APPLICATION_CANDIDATE; 0–1 = REJECTED**.
5. Click **Apply with AI** to run eligibility/duplicate checks and prepare the application and cover letter.
6. The optional **Automatically prepare eligible applications** switch prepares every candidate returned by the search.

The project does not bypass CAPTCHA, OTP, 2FA, anti-bot controls, authentication, or rate limits. Actual external submission requires an authorized provider integration; when one is not configured, the UI provides the official application URL and the prepared application materials instead of pretending a submission occurred.
## Real job search

The application searches permitted public/API feeds and can additionally use a live API-backed web-search provider. It never fabricates a job listing.

Configured sources:
- LinkedIn (Tavily web search)
- Naukri (Tavily web search)
- Indeed (Tavily web search)
- Greenhouse (Tavily web search)
- Lever (Tavily web search)
- Workday (Tavily web search)
- Company Careers websites (Tavily web search)
- Remotive
- Arbeitnow
- Jobicy
- Remote OK

The search layer normalizes listings into one schema, removes duplicates, filters by location, and records which sources succeeded or failed.

The application does **not** scrape around authentication, CAPTCHA, OTP, anti-bot controls, or rate limits. LinkedIn/Naukri adapters should only be connected through authorized APIs or integrations when credentials/access are legitimately available.

### Ollama

Run Ollama locally and make sure `llama3.2:3b` is installed:

```powershell
ollama run llama3.2:3b
```

The job feeds provide the job data. Ollama analyzes each returned job against the verified resume skills. The Python decision layer enforces the minimum of 2 matched verified skills.

### Real-source behavior

There are no fake/demo jobs in the production search path. If all configured feeds are unavailable or return no matching jobs, the API returns an empty job list and a source-status message instead of fabricating listings.



### Enable live web search

1. Create a Tavily API key from the provider's official dashboard.
2. Put it in `.env` (never commit it):

```text
TAVILY_API_KEY=your_key_here
```

3. Restart FastAPI.
4. Search for a role such as `Python Developer` with `Hyderabad` as the location.

The web-search adapter returns the actual result URL supplied by the search provider. It does not invent LinkedIn/Naukri application URLs.

### Applying

`Apply with AI` performs eligibility, duplicate, and application-preparation checks and then opens the real `source_url` in a new browser tab when one is available. The project deliberately does not bypass login, CAPTCHA, OTP, 2FA, anti-bot controls, or access restrictions, and it never reports a submission as successful unless an authorized provider actually confirms it. The final external submission remains a user-controlled action unless a legitimate provider API is configured.


### Source-specific web search

When `TAVILY_API_KEY` is configured, the UI can target a specific source or search all sources. LinkedIn, Naukri, Indeed, Greenhouse, Lever, Workday, and Company Careers are queried separately so the returned `source` remains identifiable. The user's requested location is included in each query; it is not hardcoded to Hyderabad.

The web-search layer uses the search provider's actual result URLs. It does not manufacture job URLs or bypass authentication, CAPTCHA, OTP, 2FA, anti-bot controls, or rate limits. Company Careers means publicly indexed employer career pages that the search provider can discover; it is not an exhaustive crawl of every employer website.
