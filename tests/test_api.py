from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)
def test_profile_endpoint():
    r=client.get("/api/profile");assert r.status_code==200;assert r.json()["name"]=="Kudupudi Yuvaraj"
def test_dashboard_endpoint():
    r=client.get("/api/dashboard");assert r.status_code==200
