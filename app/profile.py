import json
from pathlib import Path
PROFILE_PATH=Path(__file__).resolve().parent.parent/"data"/"candidate-profile.json"
def load_profile():
    return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
