from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from pathlib import Path
import tempfile
import re

from .agent import Agent
from .database import connect
from .resume import extract_pdf_text, build_profile_from_resume
from .search import search_jobs
from .skills import match_skills
from .ai import analyze_job_match


app = FastAPI(
    title="AI Job Application Agent",
    version="6.1.0",
)

agent = Agent()


class Job(BaseModel):
    job_id: str
    title: str
    company: str
    location: str = ""
    description: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    source: str = "manual"
    source_url: str = ""
    experience_required: str = ""
    authorized_provider: bool = False


class Batch(BaseModel):
    jobs: list[Job]


HOME = (
    Path(__file__).resolve().parent.parent
    / "static"
    / "index.html"
).read_text(encoding="utf-8")


@app.get("/", response_class=HTMLResponse)
def home():
    return HOME


# ---------------------------------------------------------
# PROFILE
# ---------------------------------------------------------

@app.get("/api/profile")
def profile():
    return agent.profile


@app.post("/api/profile/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a PDF resume.",
        )

    data = await file.read()

    if not data.startswith(b"%PDF"):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file does not look like a PDF.",
        )

    with tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False,
    ) as tmp:
        tmp.write(data)
        path = tmp.name

    try:
        try:
            text = extract_pdf_text(path)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Could not read this PDF resume: {exc}",
            ) from exc

        if not text.strip():
            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract text from this PDF. "
                    "Use a text-based PDF resume."
                ),
            )

        agent.profile = build_profile_from_resume(
            text,
            file.filename,
        )

        return {
            "name": agent.profile.get("name", ""),
            "email": agent.profile.get("email", ""),
            "phone": agent.profile.get("phone", ""),
            "skills": agent.profile.get("skills", []),
            "resume_filename": file.filename,
        }

    finally:
        Path(path).unlink(missing_ok=True)


# ---------------------------------------------------------
# AI SKILL MATCHING
# ---------------------------------------------------------

def normalize_skill(value: str) -> str:
    """
    Normalize a skill for safe comparison.

    This prevents the AI response from accidentally creating
    new skills that were not present in the verified resume.
    """
    value = value.lower().strip()

    value = re.sub(
        r"^[\-\*\•\d\.\)\s]+",
        "",
        value,
    )

    value = re.sub(
        r"[^a-z0-9+#./ -]",
        "",
        value,
    )

    return value.strip()


def verify_ai_matches(
    ai_result: str,
    resume_skills: list[str],
) -> list[str]:
    """
    Only accept AI matches that correspond to skills
    actually present in the verified resume.
    """

    normalized_resume = {
        normalize_skill(skill): skill
        for skill in resume_skills
    }

    matched = []

    in_matched_section = False

    for raw_line in ai_result.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        upper = line.upper()

        if upper.startswith("MATCHED"):
            in_matched_section = True
            continue

        if upper.startswith("MISSING"):
            in_matched_section = False
            continue

        if not in_matched_section:
            continue

        cleaned = normalize_skill(line)

        if not cleaned:
            continue

        # Exact verified resume skill
        if cleaned in normalized_resume:
            original = normalized_resume[cleaned]

            if original not in matched:
                matched.append(original)

            continue

        # Handle cases where the model writes:
        # "- Python — relevant to the role"
        for normalized, original in normalized_resume.items():
            if (
                cleaned.startswith(normalized + " ")
                or normalized in cleaned
            ):
                if original not in matched:
                    matched.append(original)

    return matched


# ---------------------------------------------------------
# JOB SEARCH
# ---------------------------------------------------------

@app.get("/api/search/sources")
def search_sources():
    import os
    web_configured = bool(os.getenv("TAVILY_API_KEY", "").strip())
    return {
        "sources": [
            {"name": "All Sources", "key": "auto", "type": "combined search", "configured": True},
            {"name": "LinkedIn", "key": "linkedin", "type": "web search", "configured": web_configured},
            {"name": "Naukri", "key": "naukri", "type": "web search", "configured": web_configured},
            {"name": "Indeed", "key": "indeed", "type": "web search", "configured": web_configured},
            {"name": "Greenhouse", "key": "greenhouse", "type": "web search", "configured": web_configured},
            {"name": "Lever", "key": "lever", "type": "web search", "configured": web_configured},
            {"name": "Workday", "key": "workday", "type": "web search", "configured": web_configured},
            {"name": "Company Careers", "key": "company-careers", "type": "web search", "configured": web_configured},
            {"name": "Remotive", "key": "remotive", "type": "public API", "configured": True},
            {"name": "Arbeitnow", "key": "arbeitnow", "type": "public API", "configured": True},
            {"name": "Jobicy", "key": "jobicy", "type": "public API", "configured": True},
            {"name": "Remote OK", "key": "remoteok", "type": "public API", "configured": True},
        ],
        "note": "The application uses permitted public/API feeds. It does not bypass job-board authentication, CAPTCHA, OTP, anti-bot controls, or rate limits.",
    }


@app.get("/api/search")
def search(
    query: str = "",
    location: str = "",
    source: str = "auto",
    experience: str = "0-1",
):
    if not query.strip():
        raise HTTPException(
            status_code=400,
            detail="Enter a job role or keyword.",
        )

    jobs, source = search_jobs(
        query,
        source=source,
        location=location,
        experience=experience,
    )

    resume_skills = agent.profile.get(
        "skills",
        [],
    )

    results = []

    for raw_job in jobs:

        job = dict(raw_job)

        required = job.get(
            "required_skills",
            [],
        )

        preferred = job.get(
            "preferred_skills",
            [],
        )

        all_job_skills = required + preferred

        job_text = f"""
TITLE:
{job.get("title", "")}

COMPANY:
{job.get("company", "")}

DESCRIPTION:
{job.get("description", "")}

REQUIRED SKILLS:
{", ".join(required)}

PREFERRED SKILLS:
{", ".join(preferred)}
"""

        # -------------------------------------------------
        # AI MATCH
        # -------------------------------------------------

        ai_matches = []

        try:
            ai_output = analyze_job_match(
                resume_skills,
                job_text,
            )

            ai_matches = verify_ai_matches(
                ai_output,
                resume_skills,
            )

        except Exception:
            # AI unavailable -> deterministic fallback.
            ai_matches, _ = match_skills(
                all_job_skills,
                agent.profile,
            )

        # -------------------------------------------------
        # APPLICATION RULE
        # -------------------------------------------------
        #
        # 2 or more verified resume skills = candidate
        #
        # 0 or 1 = rejected
        #

        if len(ai_matches) >= 2:
            status = "APPLICATION_CANDIDATE"
        else:
            status = "REJECTED"

        # Determine missing skills using deterministic
        # matching against the verified profile.
        deterministic_matches, missing = match_skills(
            all_job_skills,
            agent.profile,
        )

        job["matched_skills"] = ai_matches
        job["missing_skills"] = missing
        job["match_count"] = len(ai_matches)
        job["status"] = status

        results.append(job)

    # Candidate jobs first, then highest match count.
    results.sort(
        key=lambda item: (
            item["status"] == "APPLICATION_CANDIDATE",
            item["match_count"],
        ),
        reverse=True,
    )

    return {
        "jobs": results,
        "source": source,
        "rule": "2 or more verified resume skills",
        "experience": experience,
    }


# ---------------------------------------------------------
# MANUAL JOB ANALYSIS
# ---------------------------------------------------------

@app.post("/api/jobs")
def add(job: Job):
    return agent.analyze(job.model_dump())


# ---------------------------------------------------------
# PREPARE APPLICATION
# ---------------------------------------------------------

@app.post("/api/jobs/{job_id}/prepare")
def prepare(
    job_id: str,
    job: Job,
):
    return agent.prepare(job.model_dump())


# ---------------------------------------------------------
# APPLICATION
# ---------------------------------------------------------

@app.post("/api/jobs/{job_id}/apply")
def apply(
    job_id: str,
    job: Job,
):
    result = agent.submit(
        job.model_dump()
    )

    result["source_url"] = job.source_url

    return result


@app.post("/api/jobs/{job_id}/submit")
def submit(
    job_id: str,
    job: Job,
):
    return agent.submit(
        job.model_dump()
    )


# ---------------------------------------------------------
# BATCH AGENT
# ---------------------------------------------------------

@app.post("/api/agent/run")
def run(batch: Batch):
    return {
        "results": agent.run_batch(
            [
                job.model_dump()
                for job in batch.jobs
            ]
        )
    }


# ---------------------------------------------------------
# DATABASE / DASHBOARD
# ---------------------------------------------------------

@app.get("/api/jobs")
def jobs():
    connection = connect()

    rows = [
        dict(row)
        for row in connection.execute(
            """
            SELECT *
            FROM jobs
            ORDER BY updated_at DESC
            """
        )
    ]

    connection.close()

    return rows


@app.get("/api/jobs/ready")
def ready():
    connection = connect()

    rows = [
        dict(row)
        for row in connection.execute(
            """
            SELECT *
            FROM jobs
            WHERE status IN (
                'APPLICATION_CANDIDATE',
                'READY_FOR_AUTHORIZED_SUBMISSION'
            )
            ORDER BY updated_at DESC
            """
        )
    ]

    connection.close()

    return rows


@app.get("/api/applications")
def applications():
    connection = connect()

    rows = [
        dict(row)
        for row in connection.execute(
            """
            SELECT *
            FROM applications
            ORDER BY created_at DESC
            """
        )
    ]

    connection.close()

    return rows


@app.get("/api/events")
def events():
    connection = connect()

    rows = [
        dict(row)
        for row in connection.execute(
            """
            SELECT *
            FROM events
            ORDER BY created_at DESC
            """
        )
    ]

    connection.close()

    return rows


@app.get("/api/dashboard")
def dashboard():
    connection = connect()

    rows = connection.execute(
        """
        SELECT status, COUNT(*) n
        FROM jobs
        GROUP BY status
        """
    ).fetchall()

    connection.close()

    return {
        "counts": {
            row["status"]: row["n"]
            for row in rows
        }
    }