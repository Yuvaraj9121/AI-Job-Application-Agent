import sqlite3
from pathlib import Path
from .config import settings

SCHEMA='''
CREATE TABLE IF NOT EXISTS jobs(
 job_id TEXT PRIMARY KEY,title TEXT NOT NULL,company TEXT NOT NULL,location TEXT,
 description TEXT,required_skills TEXT,preferred_skills TEXT,source TEXT,source_url TEXT,
 experience_required TEXT,status TEXT,matched_skills TEXT,missing_skills TEXT,reason TEXT,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS applications(
 id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT UNIQUE,status TEXT NOT NULL,
 provider TEXT,confirmation_id TEXT,confirmation_url TEXT,notes TEXT,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP,updated_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS events(
 id INTEGER PRIMARY KEY AUTOINCREMENT,job_id TEXT,event TEXT NOT NULL,details TEXT,
 created_at TEXT DEFAULT CURRENT_TIMESTAMP);
'''

def connect():
    p=Path(settings.database_path);p.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(p);c.row_factory=sqlite3.Row;c.executescript(SCHEMA);return c

def canonical_url(url):
    return (url or "").strip().lower().rstrip("/")

def duplicate(c,job):
    url=canonical_url(job.get("source_url",""))
    if url:
        r=c.execute("SELECT job_id FROM jobs WHERE lower(rtrim(source_url,'/'))=?",(url,)).fetchone()
        if r:return True
    r=c.execute("SELECT job_id FROM jobs WHERE lower(company)=lower(?) AND lower(title)=lower(?) AND lower(coalesce(location,''))=lower(?)",
                (job["company"],job["title"],job.get("location",""))).fetchone()
    return r is not None

def event(c,job_id,name,details=""):
    c.execute("INSERT INTO events(job_id,event,details) VALUES(?,?,?)",(job_id,name,details))
    c.commit()
