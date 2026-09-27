from app.resume import build_profile_from_resume
from app.skills import match_skills


def test_resume_extracts_name_and_skills():
    text = """KUDUPUDI YUVARAJ\nHyderabad, Telangana\nPython SQL Git GitHub Machine Learning\n"""
    p = build_profile_from_resume(text, "resume.pdf")
    assert p["name"] == "Kudupudi Yuvaraj"
    assert "Python" in p["skills"]
    assert "SQL" in p["skills"]


def test_two_skill_rule_for_verified_resume():
    p = {"skills": ["Python", "SQL"]}
    matched, _ = match_skills(["Python", "SQL", "Docker"], p)
    assert len(matched) == 2
