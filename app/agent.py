import json
from .profile import load_profile
from .database import connect, duplicate, event
from .decision import decide
from .application import generate_cover_letter
from .providers import ProviderRegistry


class Agent:
    def __init__(self):
        self.profile = load_profile()
        self.providers = ProviderRegistry()

    def analyze(self, job):
        c = connect()
        dup = duplicate(c, job)
        result = decide(job, self.profile, dup)
        c.execute(
            """
            INSERT OR REPLACE INTO jobs
            (job_id,title,company,location,description,required_skills,preferred_skills,
             source,source_url,experience_required,status,matched_skills,missing_skills,
             reason,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            """,
            (
                job["job_id"], job["title"], job["company"],
                job.get("location", ""), job.get("description", ""),
                json.dumps(job.get("required_skills", [])),
                json.dumps(job.get("preferred_skills", [])),
                job.get("source", "manual"), job.get("source_url", ""),
                job.get("experience_required", ""), result["status"],
                json.dumps(result["matched_skills"]),
                json.dumps(result["missing_skills"]), result["reason"],
            ),
        )
        event(c, job["job_id"], result["status"], result["reason"])
        c.close()
        return {"job_id": job["job_id"], **result}

    def prepare(self, job):
        """Prepare application materials and save them for explicit human review."""
        result = self.analyze(job)
        if result["status"] != "APPLICATION_CANDIDATE":
            return result

        result["resume_name"] = self.profile.get("name", "")
        result["cover_letter"] = generate_cover_letter(
            job, result["matched_skills"], self.profile
        )
        result["status"] = "PENDING_USER_REVIEW"
        result["requires_user_review"] = True
        result["submission_performed"] = False
        result["reason"] = (
            "Application materials prepared. Review the job, resume and cover letter; "
            "nothing has been submitted."
        )

        c = connect()
        c.execute(
            """
            INSERT INTO applications(job_id,status,provider,notes)
            VALUES(?,?,?,?)
            ON CONFLICT(job_id) DO UPDATE SET
                status=excluded.status,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                job["job_id"], "PENDING_USER_REVIEW", None,
                "Prepared only; awaiting explicit user review. Not submitted.",
            ),
        )
        event(c, job["job_id"], "PENDING_USER_REVIEW", result["reason"])
        c.close()
        return result

    def submit(self, job):
        """Submission is blocked unless the user explicitly approves this job."""
        if not job.get("review_approved", False):
            return {
                "job_id": job.get("job_id"),
                "status": "REVIEW_APPROVAL_REQUIRED",
                "submission_performed": False,
                "reason": "Explicit review approval is required for this individual application.",
            }

        result = self.prepare(job)
        if result["status"] != "PENDING_USER_REVIEW":
            return result

        provider = self.providers.select(job)
        if not provider:
            result["status"] = "AUTOMATION_UNAVAILABLE"
            result["reason"] = (
                "No authorized application provider is configured. "
                "Open the official job page and submit manually."
            )
            return result

        response = provider.submit(job, result)
        result.update(response)
        return result

    def run_batch(self, jobs):
        """Batch processing is review-only; it never submits applications."""
        results = []
        for job in jobs:
            try:
                results.append(self.prepare(job))
            except Exception as exc:
                results.append({
                    "job_id": job.get("job_id"),
                    "status": "PREPARATION_FAILED",
                    "submission_performed": False,
                    "reason": str(exc),
                })
        return results
