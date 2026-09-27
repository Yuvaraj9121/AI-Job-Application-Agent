import json
from .profile import load_profile
from .database import connect,duplicate,event
from .decision import decide
from .application import generate_cover_letter
from .providers import ProviderRegistry

class Agent:
    def __init__(self):
        self.profile=load_profile()
        self.providers=ProviderRegistry()

    def analyze(self,job):
        c=connect()
        # Same job_id already stored is treated as duplicate only when it has a prior application/job record.
        dup=duplicate(c,job)
        result=decide(job,self.profile,dup)
        c.execute('''INSERT OR REPLACE INTO jobs
        (job_id,title,company,location,description,required_skills,preferred_skills,source,source_url,
         experience_required,status,matched_skills,missing_skills,reason,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)''',
        (job["job_id"],job["title"],job["company"],job.get("location",""),job.get("description",""),
         json.dumps(job.get("required_skills",[])),json.dumps(job.get("preferred_skills",[])),
         job.get("source","manual"),job.get("source_url",""),job.get("experience_required",""),
         result["status"],json.dumps(result["matched_skills"]),json.dumps(result["missing_skills"]),result["reason"]))
        event(c,job["job_id"],result["status"],result["reason"])
        c.close()
        return {"job_id":job["job_id"],**result}

    def prepare(self,job):
        r=self.analyze(job)
        if r["status"]!="APPLICATION_CANDIDATE": return r
        r["resume_name"]=self.profile["name"]
        r["cover_letter"]=generate_cover_letter(job,r["matched_skills"],self.profile)
        r["status"]="READY_FOR_AUTHORIZED_SUBMISSION"
        return r

    def submit(self,job):
        r=self.prepare(job)
        if r["status"]!="READY_FOR_AUTHORIZED_SUBMISSION": return r
        provider=self.providers.select(job)
        if not provider:
            r["status"]="AUTOMATION_UNAVAILABLE"
            r["reason"]="No authorized application provider is configured."
            return r
        response=provider.submit(job,r)
        r.update(response)
        return r

    def run_batch(self,jobs):
        results=[]
        for job in jobs:
            try:
                results.append(self.submit(job))
            except Exception as e:
                results.append({"job_id":job.get("job_id"),"status":"SUBMISSION_FAILED","reason":str(e)})
        return results
