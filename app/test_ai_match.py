"""Manual Ollama job-match check.

Run with: python -m app.test_ai_match
"""

from .ai import analyze_job_match


def main():
    resume_skills = ["Python", "SQL", "Git", "Machine Learning"]
    job_text = """
Junior Python Developer
Required: Python, SQL, REST API, AWS
Work with Git and backend services.
"""
    result = analyze_job_match(resume_skills, job_text)
    print(result)


if __name__ == "__main__":
    main()
