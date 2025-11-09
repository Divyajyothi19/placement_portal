import sqlite3
import csv
import random
import string
from datetime import datetime
from collections import Counter

DB_FILE = "placement_portal.db"

# ---------------------- INITIALIZE DB ----------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Users
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT
        )
    ''')

    # Resume analysis
    c.execute('''
        CREATE TABLE IF NOT EXISTS resume_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            score INTEGER,
            feedback TEXT,
            skills TEXT
        )
    ''')

    # Student profiles
    c.execute('''
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            reg_no TEXT,
            cgpa REAL,
            placed INTEGER DEFAULT 0,
            package REAL DEFAULT 0
        )
    ''')

    # Placements
    c.execute('''
        CREATE TABLE IF NOT EXISTS placements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            company TEXT,
            package REAL,
            placed_on TEXT
        )
    ''')

    # Ensure default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, role, department) VALUES (?, ?, ?, ?)",
                  ('admin', 'admin123', 'Admin', 'Administration'))
        print("✅ Default Admin user created: admin / admin123")

    conn.commit()
    conn.close()

# ---------------------- AUTH ----------------------
def authenticate_user(username, password, role):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?", (username, password, role))
    user = c.fetchone()
    conn.close()
    return user

# ---------------------- RESUME ANALYSIS ----------------------
def save_resume_analysis(username, score, feedback, skills):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO resume_analysis (username, score, feedback, skills) VALUES (?, ?, ?, ?)",
              (username, score, feedback, ",".join(skills)))
    conn.commit()
    conn.close()

def get_resume_analysis(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT score, feedback, skills FROM resume_analysis WHERE username=? ORDER BY id DESC LIMIT 1",
              (username,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"score": row[0], "feedback": row[1], "skills": row[2].split(",")}
    return None

# ---------------------- STUDENT PROFILE ----------------------
def upsert_student_profile(username, reg_no=None, cgpa=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM student_profiles WHERE username=?", (username,))
    if c.fetchone():
        if reg_no:
            c.execute("UPDATE student_profiles SET reg_no=? WHERE username=?", (reg_no, username))
        if cgpa is not None:
            c.execute("UPDATE student_profiles SET cgpa=? WHERE username=?", (cgpa, username))
    else:
        c.execute("INSERT INTO student_profiles (username, reg_no, cgpa) VALUES (?, ?, ?)",
                  (username, reg_no, cgpa))
    conn.commit()
    conn.close()

# ---------------------- DEPARTMENT ANALYTICS ----------------------
def get_department_stats(department):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE role='Student' AND department=?", (department,))
    total = c.fetchone()[0] or 0

    c.execute("""
        SELECT COUNT(*) FROM student_profiles sp
        JOIN users u ON sp.username=u.username
        WHERE u.department=? AND sp.placed=1
    """, (department,))
    placed = c.fetchone()[0] or 0

    c.execute("""
        SELECT AVG(sp.cgpa) FROM student_profiles sp
        JOIN users u ON sp.username=u.username
        WHERE u.department=? AND sp.placed=1
    """, (department,))
    avg_cgpa = c.fetchone()[0] or 0.0

    unplaced = total - placed
    placed_pct = (placed / total * 100) if total > 0 else 0.0

    conn.close()
    return {
        "total_students": total,
        "placed_count": placed,
        "unplaced_count": unplaced,
        "placed_percentage": round(placed_pct, 2),
        "avg_cgpa_placed": round(avg_cgpa, 2)
    }

# ---------------------- TOP RECRUITERS ----------------------
def get_top_recruiters(department, top_n=5):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT p.company, COUNT(*), AVG(p.package)
        FROM placements p
        JOIN users u ON p.username=u.username
        WHERE u.department=?
        GROUP BY p.company
        ORDER BY COUNT(*) DESC
        LIMIT ?
    """, (department, top_n))
    rows = c.fetchall()
    conn.close()
    return [(r[0], int(r[1]), round(r[2] or 0, 2)) for r in rows]

# ---------------------- SKILL GAP INSIGHTS ----------------------
def get_skill_gap_insights(department, top_k=5):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute("""
        SELECT u.username FROM users u
        JOIN student_profiles sp ON u.username=sp.username
        WHERE u.department=? AND sp.placed=1
    """, (department,))
    placed_users = [r[0] for r in c.fetchall()]

    c.execute("""
        SELECT u.username FROM users u
        LEFT JOIN student_profiles sp ON u.username=sp.username
        WHERE u.department=? AND (sp.placed=0 OR sp.placed IS NULL)
    """, (department,))
    unplaced_users = [r[0] for r in c.fetchall()]

    def extract_skills(usernames):
        counter = Counter()
        if not usernames:
            return counter
        q_marks = ",".join("?" * len(usernames))
        query = f"SELECT skills FROM resume_analysis WHERE username IN ({q_marks})"
        c.execute(query, tuple(usernames))
        for row in c.fetchall():
            for s in (row[0] or "").split(","):
                s = s.strip().lower()
                if s:
                    counter[s] += 1
        return counter

    placed_skills = extract_skills(placed_users)
    unplaced_skills = extract_skills(unplaced_users)
    placed_common = placed_skills.most_common(top_k)
    unplaced_common = unplaced_skills.most_common(top_k)
    missing = [s for s, _ in placed_common if s not in dict(unplaced_common)]

    conn.close()
    recommendation = (
        f"Top missing skills among unplaced students: {', '.join(missing)}"
        if missing else "No major skill gaps detected."
    )

    return {
        "placed_common": placed_common,
        "unplaced_common": unplaced_common,
        "missing_skills": missing,
        "recommendation": recommendation
    }
