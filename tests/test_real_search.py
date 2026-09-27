import json

import httpx

from app import search


def response(url, payload):
    request = httpx.Request("GET", url)
    return httpx.Response(200, request=request, json=payload)


def test_search_combines_and_deduplicates_real_provider_results(monkeypatch):
    def fake_remotive(client, query):
        return [{
            "job_id": "remotive-1",
            "title": "Python Developer",
            "company": "Acme",
            "location": "Remote",
            "description": "Python SQL Git",
            "required_skills": ["python", "sql", "git"],
            "preferred_skills": [],
            "source": "remotive",
            "source_url": "https://example.test/job/1",
            "experience_required": "",
        }]

    def fake_arbeitnow(client, query):
        return [{
            "job_id": "arbeitnow-1",
            "title": "AI Engineer",
            "company": "Beta",
            "location": "Hyderabad",
            "description": "Python Machine Learning",
            "required_skills": ["python", "machine learning"],
            "preferred_skills": [],
            "source": "arbeitnow",
            "source_url": "https://example.test/job/2",
            "experience_required": "",
        }]

    monkeypatch.setitem(search.PROVIDERS, "remotive", fake_remotive)
    monkeypatch.setitem(search.PROVIDERS, "arbeitnow", fake_arbeitnow)
    monkeypatch.setitem(search.PROVIDERS, "jobicy", lambda client, query: [])
    monkeypatch.setitem(search.PROVIDERS, "remoteok", lambda client, query: [])

    jobs, source = search.search_jobs("Python", location="Hyderabad")

    assert len(jobs) == 2
    assert {job["company"] for job in jobs} == {"Acme", "Beta"}
    assert "remotive" in source
    assert "arbeitnow" in source


def test_search_returns_no_fake_jobs_when_sources_fail(monkeypatch):
    def fail(client, query):
        raise httpx.ConnectError("offline")

    for key in search.PROVIDERS:
        monkeypatch.setitem(search.PROVIDERS, key, fail)

    jobs, source = search.search_jobs("Python")

    assert jobs == []
    assert "unavailable" in source


def test_real_provider_normalization():
    class FakeClient:
        pass

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "jobs": [{
                    "id": 123,
                    "title": "Python Engineer",
                    "company_name": "Acme",
                    "candidate_required_location": "Remote",
                    "description": "<p>Python and SQL</p>",
                    "url": "https://example.test/1",
                }]
            }

    class Client:
        def get(self, *args, **kwargs):
            return Response()

    jobs = search._remotive(Client(), "Python")

    assert len(jobs) == 1
    assert jobs[0]["source"] == "remotive"
    assert jobs[0]["company"] == "Acme"
    assert "Python" in [x.title() for x in jobs[0]["required_skills"]]


def test_tavily_web_search_normalizes_real_search_results(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "results": [{
                    "title": "Python Developer | Example Tech",
                    "url": "https://www.linkedin.com/jobs/view/123",
                    "content": "Python SQL FastAPI Hyderabad",
                }]
            }

    class Client:
        def post(self, *args, **kwargs):
            assert args[0] == "https://api.tavily.com/search"
            assert kwargs["json"]["api_key"] == "test-key"
            return Response()

    jobs = search._tavily_web_search(Client(), "Python Developer")

    assert len(jobs) == 1
    assert jobs[0]["source"] == "linkedin-websearch"
    assert jobs[0]["company"] == "Example Tech"
    assert jobs[0]["source_url"].startswith("https://www.linkedin.com/jobs/")
    assert "python" in jobs[0]["required_skills"]


def test_auto_search_uses_websearch_when_key_is_configured(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "test-key")

    monkeypatch.setitem(search.PROVIDERS, "tavily_websearch", lambda client, query: [{
        "job_id": "web-1", "title": "Python Developer", "company": "Web Co",
        "location": "Hyderabad", "description": "Python SQL",
        "required_skills": ["python", "sql"], "preferred_skills": [],
        "source": "linkedin-websearch", "source_url": "https://example.test/job/1",
        "experience_required": "",
    }])
    for key in ("remotive", "arbeitnow", "jobicy", "remoteok"):
        monkeypatch.setitem(search.PROVIDERS, key, lambda client, query: [])

    jobs, source = search.search_jobs("Python Developer", location="Hyderabad")
    assert jobs and jobs[0]["source"] == "linkedin-websearch"
    assert "tavily_websearch" in source
\n\ndef test_experience_matching():\n    assert search._experience_matches({"experience_required": "Fresher / 0 years"}, "fresher")\n    assert search._experience_matches({"experience_required": "0-1 years"}, "0-1")\n    assert not search._experience_matches({"experience_required": "2-3 years"}, "0-1")\n    assert not search._experience_matches({"experience_required": "5+ years"}, "0-1")\n    assert search._experience_matches({"experience_required": ""}, "0-1")\n\n\ndef test_experience_search_suffix():\n    assert "0-1 years" in search._experience_search_suffix("0-1")\n    assert "fresher" in search._experience_search_suffix("fresher")\n