"""
Real job-search providers.

The application does not scrape job-board pages or bypass authentication,
CAPTCHA, OTP, rate limits, or anti-bot controls. It consumes permitted
public/API job feeds and normalizes them into one schema.

Providers:
- Remotive public API
- Arbeitnow public job-board API
- Jobicy public remote-jobs API
- Remote OK public API

A provider can fail independently. Results from the providers that respond
are combined, normalized, filtered, and de-duplicated. Demo/fake jobs are
intentionally not used by the real search path.
"""

from __future__ import annotations

import hashlib
import html
import re
from typing import Any

import httpx

from .skills import normalize


DEFAULT_TIMEOUT = 12.0
MAX_PER_SOURCE = 50
USER_AGENT = "AI-Job-Application-Agent/6.0"


SKILL_PATTERNS = [
    "python", "sql", "mysql", "postgresql", "javascript", "typescript",
    "java", "c++", "c#", "go", "rust", "react", "next.js", "node.js",
    "html", "css", "bootstrap", "git", "github", "docker", "kubernetes",
    "aws", "azure", "gcp", "linux", "rest api", "fastapi", "django",
    "flask", "machine learning", "deep learning", "computer vision",
    "tensorflow", "keras", "pytorch", "opencv", "scikit-learn",
    "cnn", "nlp", "natural language processing", "data science",
    "data analysis", "data processing", "pandas", "numpy", "spark",
    "tableau", "power bi", "streamlit", "mongodb", "oracle", "redis",
    "airflow", "llm", "generative ai", "langchain", "api", "agile",
]


def _clean_html(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def _skills_from_text(text: str) -> list[str]:
    lowered = text.lower()
    found: list[str] = []

    for skill in SKILL_PATTERNS:
        pattern = re.escape(skill)
        if re.search(rf"(?<![a-z0-9+#]){pattern}(?![a-z0-9+#])", lowered):
            found.append(skill)

    return found


def _job_id(source: str, source_id: Any, url: str, title: str, company: str) -> str:
    identity = str(source_id or url or f"{title}|{company}").strip()
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    return f"{source}-{digest}"


def _normalize_job(
    *,
    source: str,
    source_id: Any,
    title: str,
    company: str,
    location: str,
    description: str,
    url: str,
    experience_required: str = "",
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
) -> dict[str, Any]:
    description = _clean_html(description)
    required = list(dict.fromkeys(required_skills or []))
    preferred = list(dict.fromkeys(preferred_skills or []))

    if not required:
        required = _skills_from_text(
            f"{title} {description}"
        )

    return {
        "job_id": _job_id(source, source_id, url, title, company),
        "title": _clean_html(title),
        "company": _clean_html(company) or "Unknown company",
        "location": _clean_html(location) or "Remote / unspecified",
        "description": description,
        "required_skills": required,
        "preferred_skills": preferred,
        "source": source,
        "source_url": url.strip(),
        "experience_required": experience_required or "",
    }


def _remotive(client: httpx.Client, query: str) -> list[dict[str, Any]]:
    response = client.get(
        "https://remotive.com/api/remote-jobs",
        params={"search": query, "limit": MAX_PER_SOURCE},
    )
    response.raise_for_status()
    data = response.json()

    jobs = []
    for item in data.get("jobs", [])[:MAX_PER_SOURCE]:
        jobs.append(
            _normalize_job(
                source="remotive",
                source_id=item.get("id"),
                title=item.get("title", ""),
                company=item.get("company_name", ""),
                location=item.get("candidate_required_location", "Remote"),
                description=item.get("description", ""),
                url=item.get("url", ""),
                required_skills=_skills_from_text(
                    f"{item.get('title', '')} {item.get('description', '')}"
                ),
            )
        )
    return jobs


def _arbeitnow(client: httpx.Client, query: str) -> list[dict[str, Any]]:
    response = client.get(
        "https://www.arbeitnow.com/api/job-board-api",
    )
    response.raise_for_status()
    data = response.json()

    query_terms = [
        normalize(part)
        for part in query.split()
        if part.strip()
    ]

    jobs = []
    for item in data.get("data", []):
        title = item.get("title", "")
        description = item.get("description", "")
        company = item.get("company_name", "")
        searchable = normalize(
            f"{title} {company} {description}"
        )

        if query_terms and not all(term in searchable for term in query_terms):
            continue

        jobs.append(
            _normalize_job(
                source="arbeitnow",
                source_id=item.get("slug") or item.get("id"),
                title=title,
                company=company,
                location=item.get("location", ""),
                description=description,
                url=item.get("url", ""),
                required_skills=_skills_from_text(
                    f"{title} {description}"
                ),
            )
        )

        if len(jobs) >= MAX_PER_SOURCE:
            break

    return jobs


def _jobicy(client: httpx.Client, query: str) -> list[dict[str, Any]]:
    response = client.get(
        "https://jobicy.com/api/v2/remote-jobs",
        params={"count": MAX_PER_SOURCE, "tag": query},
    )
    response.raise_for_status()
    data = response.json()

    jobs = []
    for item in data.get("jobs", [])[:MAX_PER_SOURCE]:
        title = item.get("jobTitle", item.get("title", ""))
        description = item.get("jobDescription", item.get("description", ""))
        company = item.get("companyName", item.get("company", ""))

        jobs.append(
            _normalize_job(
                source="jobicy",
                source_id=item.get("id"),
                title=title,
                company=company,
                location=item.get("jobGeo", item.get("location", "Remote")),
                description=description,
                url=item.get("url", ""),
                required_skills=_skills_from_text(
                    f"{title} {description}"
                ),
            )
        )

    return jobs


def _remoteok(client: httpx.Client, query: str) -> list[dict[str, Any]]:
    response = client.get(
        "https://remoteok.com/api",
    )
    response.raise_for_status()
    data = response.json()

    query_terms = [
        normalize(part)
        for part in query.split()
        if part.strip()
    ]

    jobs = []
    for item in data:
        if not isinstance(item, dict) or not item.get("position"):
            continue

        title = item.get("position", "")
        description = item.get("description", "")
        company = item.get("company", "")
        searchable = normalize(
            f"{title} {company} {description} {item.get('tags', '')}"
        )

        if query_terms and not all(term in searchable for term in query_terms):
            continue

        tags = item.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]

        jobs.append(
            _normalize_job(
                source="remoteok",
                source_id=item.get("id"),
                title=title,
                company=company,
                location=item.get("location", "Remote"),
                description=description,
                url=item.get("url", ""),
                required_skills=list(tags) + _skills_from_text(
                    f"{title} {description}"
                ),
            )
        )

        if len(jobs) >= MAX_PER_SOURCE:
            break

    return jobs


def _classify_web_source(url: str) -> str:
    lower_url = url.lower()
    if "linkedin.com/jobs" in lower_url:
        return "linkedin-websearch"
    if "naukri.com" in lower_url:
        return "naukri-websearch"
    if "indeed.com" in lower_url:
        return "indeed-websearch"
    if "greenhouse.io" in lower_url:
        return "greenhouse-websearch"
    if "lever.co" in lower_url:
        return "lever-websearch"
    if "workdayjobs.com" in lower_url or "myworkdayjobs.com" in lower_url:
        return "workday-websearch"
    return "company-careers-websearch"


def _tavily_web_search(
    client: httpx.Client,
    query: str,
    location: str = "",
    source_filter: str = "all",
) -> list[dict[str, Any]]:
    """Search real job pages through Tavily.

    Searches each requested job-board family separately so LinkedIn, Naukri,
    Indeed, ATS-hosted careers pages, and other company career sites remain
    distinguishable. This does not scrape or bypass protected pages.
    """
    import os

    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not configured")

    loc = location.strip() or "India"
    source_queries = {
        "linkedin": f'{query} {loc} jobs site:linkedin.com/jobs',
        "naukri": f'{query} {loc} jobs site:naukri.com',
        "indeed": f'{query} {loc} jobs site:indeed.com',
        "greenhouse": f'{query} {loc} jobs site:greenhouse.io',
        "lever": f'{query} {loc} jobs site:lever.co',
        "workday": f'{query} {loc} jobs (site:workdayjobs.com OR site:myworkdayjobs.com)',
        "company-careers": (
            f'{query} {loc} jobs careers '
            '-site:linkedin.com -site:naukri.com -site:indeed.com '
            '-site:greenhouse.io -site:lever.co '
            '-site:workdayjobs.com -site:myworkdayjobs.com'
        ),
    }

    if source_filter == "all":
        requested = list(source_queries)
    elif source_filter in source_queries:
        requested = [source_filter]
    else:
        requested = ["all"] if source_filter == "tavily_websearch" else []

    if not requested:
        return []

    jobs: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    for source_name in requested:
        response = client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": source_queries[source_name],
                "search_depth": "advanced",
                "max_results": MAX_PER_SOURCE,
                "include_answer": False,
                "include_raw_content": False,
            },
        )
        response.raise_for_status()
        data = response.json()

        for item in data.get("results", [])[:MAX_PER_SOURCE]:
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "").strip()
            content = item.get("content") or ""
            if not url or not title:
                continue

            canonical = url.lower().rstrip("/")
            if canonical in seen_urls:
                continue

            # For source-specific searches, reject off-domain results.
            if source_name == "linkedin" and "linkedin.com/jobs" not in canonical:
                continue
            if source_name == "naukri" and "naukri.com" not in canonical:
                continue
            if source_name == "indeed" and "indeed.com" not in canonical:
                continue
            if source_name == "greenhouse" and "greenhouse.io" not in canonical:
                continue
            if source_name == "lever" and "lever.co" not in canonical:
                continue
            if source_name == "workday" and not (
                "workdayjobs.com" in canonical or "myworkdayjobs.com" in canonical
            ):
                continue

            seen_urls.add(canonical)
            source = _classify_web_source(url)

            company = "Unknown company"
            clean_title = title
            for separator in (" | ", " - ", " — "):
                parts = [part.strip() for part in title.split(separator) if part.strip()]
                if len(parts) >= 2:
                    clean_title = parts[0]
                    company = parts[-1]
                    break

            # Search providers may expose a publication timestamp. Preserve it
            # when available; never invent a posting date.
            published_date = item.get("published_date") or item.get("publishedDate")

            jobs.append(
                _normalize_job(
                    source=source,
                    source_id=url,
                    title=clean_title,
                    company=company,
                    location=loc,
                    description=content,
                    url=url,
                    required_skills=_skills_from_text(f"{clean_title} {content}"),
                )
                | {"published_date": published_date}
            )

    return jobs


PROVIDERS = {
    "tavily_websearch": _tavily_web_search,
    "linkedin": _tavily_web_search,
    "naukri": _tavily_web_search,
    "indeed": _tavily_web_search,
    "greenhouse": _tavily_web_search,
    "lever": _tavily_web_search,
    "workday": _tavily_web_search,
    "company-careers": _tavily_web_search,
    "remotive": _remotive,
    "arbeitnow": _arbeitnow,
    "jobicy": _jobicy,
    "remoteok": _remoteok,
}


def _location_matches(job: dict[str, Any], location: str) -> bool:
    if not location.strip():
        return True

    requested = normalize(location)
    job_location = normalize(job.get("location", ""))
    description = normalize(job.get("description", ""))

    if requested in job_location:
        return True

    # Remote listings are useful for a location search because the job
    # may accept applicants from the requested country/region.
    if "remote" in job_location:
        return True

    return requested in description


def _deduplicate(jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output = []

    for job in jobs:
        url = job.get("source_url", "").strip().lower().rstrip("/")
        identity = url or normalize(
            f"{job.get('title', '')}|{job.get('company', '')}|{job.get('location', '')}"
        )

        if not identity or identity in seen:
            continue

        seen.add(identity)
        output.append(job)

    return output


def search_jobs(
    query: str,
    source: str = "auto",
    location: str = "",
) -> tuple[list[dict[str, Any]], str]:
    """
    Search real permitted job feeds.

    Returns:
        (jobs, source_summary)

    No demo/fake jobs are returned. If every source fails or returns no
    matching jobs, the result is an empty list and source_summary explains
    which sources were attempted.
    """
    query = query.strip()

    if not query:
        return [], "no query"

    # Web search is opt-in through TAVILY_API_KEY. This keeps local/offline
    # development deterministic while allowing a genuine live-web path.
    import os
    web_enabled = bool(os.getenv("TAVILY_API_KEY", "").strip())
    selected = (
        list(PROVIDERS)
        if source == "auto"
        else [source]
    )
    if source == "auto" and not web_enabled:
        selected = [
            name for name in selected
            if name not in {
                "tavily_websearch", "linkedin", "naukri", "indeed",
                "greenhouse", "lever", "workday", "company-careers"
            }
        ]
    all_jobs: list[dict[str, Any]] = []
    successful: list[str] = []
    failed: list[str] = []

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    }

    with httpx.Client(
        timeout=DEFAULT_TIMEOUT,
        headers=headers,
        follow_redirects=True,
    ) as client:
        for provider_name in selected:
            provider = PROVIDERS.get(provider_name)

            if provider is None:
                failed.append(f"{provider_name}: unknown source")
                continue

            try:
                if provider_name in {
                    "tavily_websearch", "linkedin", "naukri", "indeed",
                    "greenhouse", "lever", "workday", "company-careers"
                }:
                    source_filter = (
                        "all" if provider_name == "tavily_websearch"
                        else provider_name
                    )
                    try:
                        jobs = provider(
                            client, query, location, source_filter
                        )
                    except TypeError:
                        # Backward-compatible with simple test/custom providers
                        # that accept only (client, query).
                        jobs = provider(client, query)
                else:
                    jobs = provider(client, query)

                successful.append(provider_name)
                all_jobs.extend(jobs)
            except Exception as exc:
                failed.append(
                    f"{provider_name}: {type(exc).__name__}"
                )

    jobs = [
        job for job in all_jobs
        if _location_matches(job, location)
    ]
    jobs = _deduplicate(jobs)

    # Prefer jobs whose title contains the query terms, but do not throw
    # away otherwise relevant feed results.
    query_terms = [
        normalize(part)
        for part in query.split()
        if part.strip()
    ]

    def relevance(job: dict[str, Any]) -> tuple[int, int]:
        title = normalize(job.get("title", ""))
        matches = sum(term in title for term in query_terms)
        return matches, len(job.get("required_skills", []))

    jobs.sort(key=relevance, reverse=True)

    if successful:
        summary = " + ".join(successful)
    else:
        summary = "none"

    if failed:
        summary += " | unavailable: " + ", ".join(failed)

    return jobs, summary
