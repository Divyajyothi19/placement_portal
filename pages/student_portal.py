# pages/student_portal.py
import streamlit as st
import random
import sqlite3
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
    # drives: created by admin/tpo (but safe-create here)
    c.execute("""
    CREATE TABLE IF NOT EXISTS drives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company TEXT,
        role TEXT,
        package REAL,
        department TEXT,        -- department the drive is targeted to (e.g., CSE) or 'ALL'
        open_for_all INTEGER DEFAULT 0, -- 1 => any department can apply
        date TEXT,
        deadline TEXT,
        description TEXT,
        is_active INTEGER DEFAULT 1
    )
    """)
    # applications: student applications to drives
    c.execute("""
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        drive_id INTEGER,
        applied_on TEXT,
        status TEXT DEFAULT 'Applied',  -- Applied / Shortlisted / Selected / Rejected
        remarks TEXT
    )
    """)
    conn.commit()
    conn.close()

ensure_drive_tables()

# ---------------------- HEADER ----------------------
st.title("🎓 Student Portal — AI Career Coach")
st.markdown(f"Welcome, **{username}** 👋  — upload resume, view active drives and check your application status.")

# ---------------------- STUDENT DETAILS FORM ----------------------
st.markdown("## 🧾 Student Academic Details")
col1, col2 = st.columns(2)
with col1:
    department = st.selectbox("Department", ["CSE", "ECE", "EEE", "MECH", "CIVIL", "AI&DS"], index=0)
with col2:
    cgpa = st.number_input("Enter your CGPA (0.0 - 10.0)", min_value=0.0, max_value=10.0, step=0.01, value=7.0)

if st.button("💾 Save Details"):
    upsert_student_profile(username, reg_no=None, cgpa=cgpa)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET department=? WHERE username=?", (department, username))
    conn.commit()
    conn.close()
    st.success("✅ Details saved successfully!")

st.markdown("---")

# ---------------------- RESUME UPLOAD SECT (unchanged but kept) ----------------------
st.subheader("📄 Upload Resume for AI Analysis")
uploaded_file = st.file_uploader("Upload your resume (PDF or DOCX)", type=["pdf", "docx"], key="resume_uploader")

if uploaded_file:
    st.success("✅ Resume uploaded successfully! Running AI evaluation...")

    # ---------------------------------------------------
    # Simulated AI analysis (placeholder). Replace with real API later.
    ai_skills = ["Python", "Machine Learning", "SQL", "Data Analysis", "Communication"]
    detected = random.sample(ai_skills, random.randint(2, len(ai_skills)))
    score = random.randint(60, 98)

    if cgpa >= 8.5:
        score += 2
    elif cgpa < 6.0:
        score -= 3
    score = max(0, min(score, 100))

    feedback_list = [
        "Excellent technical foundation. Add more project details.",
        "Consider improving the skills section with specific tools.",
        "Try highlighting internships or certifications.",
        "Add measurable achievements under projects.",
        "Focus on clarity and structure — recruiters love concise resumes."
    ]
    feedback = random.choice(feedback_list)

    # Save to database
    save_resume_analysis(username, score, feedback, detected)
    upsert_student_profile(username, reg_no=None, cgpa=cgpa)

    # Show results
    st.markdown("### 🧠 AI Resume Evaluation Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Resume Score", f"{score}/100")
    c2.metric("CGPA", f"{cgpa:.2f}")
    match_percent = round((score * 0.6 + cgpa * 10 * 0.4), 2)
    c3.metric("Placement Readiness", f"{match_percent}%")
    st.write("**Feedback:**", feedback)
    st.write("**Skills Detected:**", ", ".join(detected))
    st.info(f"🤖 AI Summary: Based on resume + CGPA your readiness estimate is **{match_percent}%**.")
    st.success("✅ Resume evaluation saved.")

st.markdown("---")

# ---------------------- ACTIVE PLACEMENT DRIVES ----------------------
st.subheader("🚀 Active Placement Drives")

# Option for demo seeding (useful for judge demo)
demo_col = st.columns([1,6,1])
with demo_col[0]:
    seed_demo = st.checkbox("Seed demo drives (for presentation)", value=False)
if seed_demo:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # insert only if drives table empty to avoid duplicates
    c.execute("SELECT COUNT(*) FROM drives")
    if c.fetchone()[0] == 0:
        demo_drives = [
            ("Infosys", "Software Engineer", 6.5, "CSE", 0, "2025-02-10", "2025-02-28", "On-campus hiring for freshers"),
            ("TCS", "System Engineer", 5.0, "ALL", 1, "2025-02-15", "2025-03-05", "Apply if CGPA >= 6.0"),
            ("FinTech Pvt Ltd", "Data Analyst Intern", 4.0, "AI&DS", 0, "2025-02-20", "2025-03-01", "Internship with conversion")
        ]
        for d in demo_drives:
            c.execute("INSERT INTO drives (company, role, package, department, open_for_all, date, deadline, description) VALUES (?,?,?,?,?,?,?,?)", d)
        conn.commit()
        st.success("Demo drives seeded.")
    else:
        st.info("Drives already exist; demo seeding skipped.")
    conn.close()

# Load active drives (department-specific or open to all)
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
# drives targeted to student's department or open_for_all=1 or department='ALL'
c.execute("""
    SELECT id, company, role, package, department, open_for_all, date, deadline, description
    FROM drives
    WHERE is_active=1 AND (department=? OR open_for_all=1 OR department='ALL')
    ORDER BY date ASC
""", (department,))
drives = c.fetchall()
conn.close()

if not drives:
    st.info("No placement drives available for your department right now.")
else:
    for d in drives:
        d_id, company, role_name, package, dept, open_for_all, date_str, deadline_str, desc = d
        box = st.container()
        with box:
            cols = st.columns([4,2,1])
            left = cols[0]
            mid = cols[1]
            right = cols[2]

            left.markdown(f"### 🚀 **{company}** — {role_name}")
            left.write(f"**Details:** {desc}")
            left.write(f"**Department:** {dept if dept!='ALL' else 'All Departments'}    •    **Drive Date:** {date_str}    •    **Deadline:** {deadline_str}")

            mid.metric("Package (LPA)", f"{package}")
            right.write("")  # spacer

            # check if student already applied
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("SELECT id, status FROM applications WHERE username=? AND drive_id=?", (username, d_id))
            app = c.fetchone()
            conn.close()

            if app:
                app_id, app_status = app
                st.info(f"🔔 You already applied to this drive. Status: **{app_status}**")
            else:
                apply_col1, apply_col2 = st.columns([1,3])
                with apply_col1:
                    if st.button("Apply ▶️", key=f"apply_{d_id}"):
                        # insert application
                        conn = sqlite3.connect(DB_FILE)
                        c = conn.cursor()
                        c.execute("INSERT INTO applications (username, drive_id, applied_on, status) VALUES (?,?,?,?)",
                                  (username, d_id, datetime.utcnow().isoformat(), "Applied"))
                        conn.commit()
                        conn.close()
                        st.success("✅ Application submitted. Check 'My Applications & Status' below.")
                with apply_col2:
                    st.write("")

st.markdown("---")

# ---------------------- MY APPLICATIONS & STATUS ----------------------
st.subheader("📋 My Applications & Status")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""
    SELECT a.id, d.company, d.role, d.package, d.date, a.applied_on, a.status, d.deadline
    FROM applications a
    JOIN drives d ON a.drive_id = d.id
    WHERE a.username = ?
    ORDER BY a.applied_on DESC
""", (username,))
apps = c.fetchall()
conn.close()

if not apps:
    st.info("You haven't applied for any drives yet.")
else:
    apps_df = []
    for a in apps:
        aid, company, role_name, package, drive_date, applied_on, status, deadline = a
        apps_df.append({
            "Application ID": aid,
            "Company": company,
            "Role": role_name,
            "Package (LPA)": package,
            "Drive Date": drive_date,
            "Applied On": applied_on.split("T")[0] if applied_on else applied_on,
            "Deadline": deadline,
            "Status": status
        })
    st.table(apps_df)

st.markdown("---")

# ---------------------- PREVIOUS ANALYSIS (unchanged) ----------------------
st.subheader("📊 Previous Resume Analysis")
previous = get_resume_analysis(username)
if previous:
    st.metric("Last Resume Score", f"{previous['score']} / 100")
    st.write("**Feedback:**", previous["feedback"])
    st.write("**Skills:**", ", ".join(previous["skills"]))
    if previous["score"] >= 85:
        st.success("💼 Highly placement-ready.")
    elif previous["score"] >= 70:
        st.warning("📈 Moderately ready.")
    else:
        st.error("⚙️ Improvement needed.")
else:
    st.info("No previous analysis found. Upload your resume to get AI insights.")