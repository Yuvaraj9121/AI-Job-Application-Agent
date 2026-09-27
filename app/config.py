import os
from dataclasses import dataclass

def _bool(v): return str(v).lower() in {"1","true","yes","on"}

@dataclass(frozen=True)
class Settings:
    database_path: str = os.getenv("DATABASE_PATH","data/jobs.db")
    min_matched_skills: int = int(os.getenv("MIN_MATCHED_SKILLS","2"))
    autonomous_mode: bool = _bool(os.getenv("AUTONOMOUS_MODE","false"))
    max_applications_per_run: int = int(os.getenv("MAX_APPLICATIONS_PER_RUN","10"))
    max_applications_per_day: int = int(os.getenv("MAX_APPLICATIONS_PER_DAY","25"))

settings=Settings()
