import re

ALIASES={
"ml":"machine learning","machine-learning":"machine learning",
"dl":"deep learning","deep-learning":"deep learning",
"cnn":"cnns","cv":"computer vision","computer-vision":"computer vision",
"js":"javascript","tf":"tensorflow","keras":"tensorflow","tensorflow/keras":"tensorflow"
}

def normalize(skill):
    s=re.sub(r"[^a-z0-9+#./ -]+"," ",skill.lower()).strip()
    return ALIASES.get(s,s)

def match_skills(job_skills,profile):
    available={normalize(x) for x in profile.get("skills",[])}
    matched=[];missing=[]
    for raw in job_skills:
        (matched if normalize(raw) in available else missing).append(raw)
    return list(dict.fromkeys(matched)),list(dict.fromkeys(missing))
