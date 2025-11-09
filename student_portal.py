# ---------------------- PATH FIX ----------------------
import os, sys
HERE = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# ---------------------- IMPORTS ----------------------
import streamlit as st
import random
import sqlite3
import pandas as pd
from datetime import datetime
from database import save_resume_analysis, get_resume_analysis, upsert_student_profile, DB_FILE

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Student Portal", layout="wide")

# ---------------------- ACCESS CONTROL ----------------------
if "logged_in" not in st.session_state or st.session_state.get("role") != "Student":
    st.error("🚫 Access Denied! Please log in as a Student.")
    st.stop()

username = st.session_state["username"]

# ---------------------- UTILS: ensure tables ----------------------
def ensure_drive_tables():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS drives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT,
        role TEXT,
        package REAL,
        department TEXT,
        open_for_all INTEGER DEFAULT 0,
        date TEXT,
        deadline TEXT,
        description TEXT,
        is_active INTEGER DEFAULT 1
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        drive_id INTEGER,
        applied_on TEXT,
        status TEXT DEFAULT 'Applied',
        remarks TEXT
    )
    """)
    conn.commit()
    conn.close()

ensure_drive_tables()

# ---------------------- HEADER ----------------------
st.title("🎓 Student Portal — AI Career Coach")
st.markdown(f"Welcome, **{username}** 👋  — upload resume, view drives, and track your status.")

# ---------------------- STUDENT DETAILS ----------------------
st.markdown("## 🧾 Student Academic Details")
col1, col2 = st.columns(2)
with col1:
    department = st.selectbox("Department", ["CSE", "ECE", "EEE", "MECH", "CIVIL", "AI&DS"], index=0)
with col2:
    cgpa = st.number_input("Enter your CGPA", min_value=0.0, max_value=10.0, step=0.01, value=7.0)

if st.button("💾 Save Details"):
    upsert_student_profile(username, reg_no=None, cgpa=cgpa)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET department=? WHERE username=?", (department, username))
    conn.commit()
    conn.close()
    st.success("✅ Details saved successfully!")

st.markdown("---")

# ---------------------- RESUME UPLOAD ----------------------
st.subheader("📄 Upload Resume for AI Analysis")
uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"], key="resume")

if uploaded_file:
    st.success("✅ Resume uploaded! Running AI evaluation...")
    ai_skills = ["Python", "Machine Learning", "SQL", "Data Analysis", "Communication"]
    detected = random.sample(ai_skills, random.randint(2, len(ai_skills)))
    score = random.randint(60, 98)
    if cgpa >= 8.5:
        score += 2
    elif cgpa < 6.0:
        score -= 3
    score = max(0, min(score, 100))
    feedback = random.choice([
        "Add more project details.", "Highlight certifications.", 
        "Improve skills section.", "Add measurable results.", 
        "Keep your resume concise."
    ])
    save_resume_analysis(username, score, feedback, detected)
    upsert_student_profile(username, reg_no=None, cgpa=cgpa)
    st.metric("Resume Score", f"{score}/100")
    st.metric("Placement Readiness", f"{round((score*0.6 + cgpa*10*0.4),2)}%")
    st.write("**Feedback:**", feedback)
    st.write("**Skills Detected:**", ", ".join(detected))

st.markdown("---")

# ---------------------- ACTIVE PLACEMENT DRIVES ----------------------
st.subheader("🚀 Active Placement Drives")
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""
    SELECT id, company, role, package, department, open_for_all, date, deadline, description
    FROM drives
    WHERE is_active=1 AND (department=? OR open_for_all=1 OR department='ALL')
    ORDER BY date ASC
""", (department,))
drives = c.fetchall()
conn.close()

if not drives:
    st.info("No placement drives available right now.")
else:
    for d in drives:
        d_id, company, role_name, package, dept, open_for_all, date_str, deadline_str, desc = d
        st.markdown(f"### 💼 {company} — {role_name}")
        st.write(f"📅 Date: {date_str} | Deadline: {deadline_str}")
        st.write(f"💰 Package: {package} LPA | Department: {dept}")
        st.write(f"📝 Description: {desc}")

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id FROM applications WHERE username=? AND drive_id=?", (username, d_id))
        applied = c.fetchone()
        conn.close()

        if applied:
            st.info("✅ Already applied.")
        else:
            if st.button(f"Apply to {company}", key=f"apply_{d_id}"):
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("INSERT INTO applications (username, drive_id, applied_on, status) VALUES (?,?,?,?)",
                          (username, d_id, datetime.utcnow().isoformat(), "Applied"))
                conn.commit()
                conn.close()
                st.success(f"Applied to {company}!")

st.markdown("---")

# ---------------------- MY APPLICATIONS ----------------------
st.subheader("📋 My Applications")
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""
    SELECT a.id, d.company, d.role, a.status, d.date, d.deadline
    FROM applications a JOIN drives d ON a.drive_id=d.id
    WHERE a.username=? ORDER BY a.applied_on DESC
""", (username,))
apps = c.fetchall()
conn.close()

if apps:
    df = pd.DataFrame(apps, columns=["ID", "Company", "Role", "Status", "Drive Date", "Deadline"])
    st.dataframe(df, width='stretch')
else:
    st.info("You haven't applied for any drives yet.")
