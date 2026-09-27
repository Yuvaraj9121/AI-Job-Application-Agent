def check_eligibility(job,profile):
    exp=(job.get("experience_required") or "").lower()
    # Conservative entry-level check. Unknown experience is not automatically rejected.
    if any(x in exp for x in ("5+ years","6+ years","7+ years","8+ years","senior","lead","principal")):
        return False,"The listed experience level is beyond the configured entry-level target."
    return True,"Eligible under the configured entry-level rules."
