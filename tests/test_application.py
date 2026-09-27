from app.application import answer_question
def test_unknown_experience_needs_review():
    p={"experience":[]}
    assert answer_question("How many years of professional experience do you have?",p)["status"]=="MANUAL_REVIEW_REQUIRED"
