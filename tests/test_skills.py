from app.skills import match_skills
P={"skills":["Python","SQL","Machine Learning","Git"]}
def test_alias_and_matches():
    m,x=match_skills(["Python","ML","Docker"],P)
    assert m==["Python","ML"] and x==["Docker"]
