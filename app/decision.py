from .skills import match_skills
from .eligibility import check_eligibility
from .config import settings

def decide(job,profile,duplicate=False):
    skills=list(dict.fromkeys(job.get("required_skills",[])+job.get("preferred_skills",[])))
    matched,missing=match_skills(skills,profile)
    if duplicate:
        return {"status":"DUPLICATE","reason":"A matching job/application already exists.","matched_skills":matched,"missing_skills":missing}
    if len(matched)<settings.min_matched_skills:
        return {"status":"REJECTED","reason":f"{len(matched)} matched skill(s); minimum is {settings.min_matched_skills}.","matched_skills":matched,"missing_skills":missing}
    eligible,reason=check_eligibility(job,profile)
    if not eligible:
        return {"status":"REJECTED","reason":reason,"matched_skills":matched,"missing_skills":missing}
    return {"status":"APPLICATION_CANDIDATE","reason":f"{len(matched)} matched skill(s) meets the threshold.","matched_skills":matched,"missing_skills":missing}
