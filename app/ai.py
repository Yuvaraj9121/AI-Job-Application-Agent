import json
import urllib.request
import urllib.error


OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "llama3.2:3b"


def ask_ai(prompt: str) -> str:
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an accurate job application assistant. "
                    "Use only information supplied by the user. "
                    "Never invent qualifications, experience, education, "
                    "certifications, skills, or employment history."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=120
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        return result["message"]["content"]

    except urllib.error.URLError as exc:
        raise RuntimeError(
            "Could not connect to Ollama. "
            "Make sure Ollama is running."
        ) from exc


def analyze_job_match(
    resume_skills: list[str],
    job_text: str
) -> str:

    skills_text = "\n".join(
        f"- {skill}"
        for skill in resume_skills
    )

    prompt = f"""
You are analyzing a job against a candidate's VERIFIED resume skills.

VERIFIED RESUME SKILLS:
{skills_text}

JOB DESCRIPTION:
{job_text}

Identify which skills from the VERIFIED RESUME SKILLS
are relevant matches for the job.

IMPORTANT RULES:

1. Only use skills present in the VERIFIED RESUME SKILLS list.
2. Never invent candidate skills.
3. Do not count a skill just because it appears in the job description.
4. Identify the candidate skills that are relevant to the job.
5. Identify important job skills that are not present in the candidate skills.
6. Do not decide whether to apply.
7. The application system independently enforces the minimum
   requirement of 2 matched skills.

Return exactly this structure:

MATCHED:
- skill 1
- skill 2

MISSING:
- skill 1
- skill 2
"""

    return ask_ai(prompt)