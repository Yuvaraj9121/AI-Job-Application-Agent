from .profile import load_profile

def generate_cover_letter(job,matched,profile=None):
    p=profile or load_profile()
    return (f"Dear Hiring Team,\n\n"
            f"I am {p['name']}, a 2026 B.Tech graduate in Artificial Intelligence & Data Science. "
            f"My project work includes machine-learning and computer-vision applications, and the "
            f"skills matching this role include: {', '.join(matched)}.\n\n"
            f"I would welcome the opportunity to contribute and learn in this role.\n\n"
            f"Regards,\n{p['name']}")

def answer_question(question,profile):
    q=question.lower()
    if "years of professional experience" in q or "years of experience" in q:
        if not profile.get("experience"): return {"status":"MANUAL_REVIEW_REQUIRED","answer":None}
    return {"status":"MANUAL_REVIEW_REQUIRED","answer":None}
