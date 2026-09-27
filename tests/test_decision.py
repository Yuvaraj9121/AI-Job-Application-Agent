from app.decision import decide
P={"skills":["Python","SQL","Machine Learning"]}
def test_zero(): assert decide({"required_skills":["Java","Spring"]},P)["status"]=="REJECTED"
def test_one(): assert decide({"required_skills":["Python","Java"]},P)["status"]=="REJECTED"
def test_two(): assert decide({"required_skills":["Python","SQL","Docker"]},P)["status"]=="APPLICATION_CANDIDATE"
def test_three(): assert decide({"required_skills":["Python","SQL","Machine Learning"]},P)["status"]=="APPLICATION_CANDIDATE"
def test_duplicate(): assert decide({"required_skills":["Python","SQL"]},P,True)["status"]=="DUPLICATE"
def test_senior_rejected(): assert decide({"required_skills":["Python","SQL"],"experience_required":"5+ years"},P)["status"]=="REJECTED"
