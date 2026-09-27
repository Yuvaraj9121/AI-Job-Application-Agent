from pathlib import Path
import re
from pypdf import PdfReader
from .skills import normalize

KNOWN_SKILLS = [
    "Python", "SQL", "JavaScript", "HTML", "CSS", "Machine Learning", "Deep Learning",
    "CNNs", "Computer Vision", "Image Classification", "Object Detection", "Model Evaluation",
    "MySQL", "Data Processing", "Querying", "Joins", "Aggregation", "Git", "GitHub", "VS Code", "Streamlit",
    "TensorFlow", "Keras", "OpenCV", "Scikit-learn", "Java", "C++", "React", "Next.js", "Node.js", "Docker"
]

def extract_pdf_text(path: str) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)

def skills_from_text(text: str) -> list[str]:
    normalized = normalize(text)
    found = []
    for skill in KNOWN_SKILLS:
        if normalize(skill) in normalized:
            found.append(skill)
    return found

def build_profile_from_resume(text: str, filename: str) -> dict:
    skills = skills_from_text(text)
    email = re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I)
    phone = re.search(r"(?:\+91[-\s]?)?[6-9]\d{9}", text)
    lines=[re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]
    name="Uploaded Candidate"
    for line in lines[:12]:
        if (2 <= len(line.split()) <= 4 and "@" not in line and not re.search(r"\d{7,}", line)
                and line.lower() not in {"professional summary", "technical skills", "projects", "education", "certifications"}):
            name=line.title()
            break
    return {
        "name": name,
        "email": email.group(0) if email else "",
        "phone": phone.group(0) if phone else "",
        "location": "",
        "skills": skills,
        "resume_filename": filename,
        "source": "uploaded_resume"
    }
