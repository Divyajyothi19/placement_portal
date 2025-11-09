import sqlite3
import csv
import os
import random
import string
from datetime import datetime
from collections import Counter

# Use a fixed DB path compatible with Streamlit Cloud
DB_FILE = os.path.join(os.getcwd(), "placement_portal.db")

# ------------------- DATABASE INITIALIZATION -------------------
def init_db():
    """Initialize the database safely (even in Streamlit Cloud)."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Create table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT
        )
    """)

    # ✅ Create resume_analysis table
    c.execute("""
        CREATE TABLE IF NOT EXISTS resume_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            score INTEGER,
            feedback TEXT,
            skills TEXT
        )
    """)

    # ✅ Create required HOD tables
    ensure_hod_tables()

    # ✅ Create default Admin if missing
    c.execute("SELECT * FROM users WHERE username='admin' AND role='Admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password, role, department) VALUES (?, ?, ?, ?)",
            ('admin', 'admin123', 'Admin', 'Administration')
        )
        print("✅ Default Admin user created: admin / admin123")

    conn.commit()
    conn.close()


# ------------------- AUTHENTICATION -------------------
def authenticate_user(username, password, role):
    """Verify login credentials."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=? AND role=?", (username, password, role))
    user = c.fetchone()
    conn.close()
    return user


# ------------------- AUTO USER GENERATION -------------------
def generate_username(role):
    prefix = role[:3].upper()
    random_num = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{random_num}"

def generate_password(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def add_auto_user(role, department=None):
    """Automatically create users; department required for HOD and unique per dept."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # ✅ HOD must have a department and be unique per department
    if role == "HOD":
        if not department or department.strip() == "":
            conn.close()
            return None, "⚠️ Department is required when creating a HOD account."
        c.execute("SELECT * FROM users WHERE role='HOD' AND department=?", (department,))
        if c.fetchone():
            conn.close()
            return None, f"⚠️ A HOD already exists for department '{department}'."

    username = generate_username(role)
    password = generate_password()

    c.execute("INSERT INTO users (username, password, role, department) VALUES (?, ?, ?, ?)",
              (username, password, role, department))
    conn.commit()
    conn.close()
    return (username, password), f"✅ {role} account created successfully."


# ------------------- GET ALL USERS -------------------
def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, password, role, department FROM users ORDER BY id DESC")
    data = c.fetchall()
    conn.close()
    return data


# ------------------- EXPORT USERS TO CSV -------------------
def export_users_to_csv(filename="all_users_export.csv"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, username, password, role, department FROM users ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()

    with open(filename, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "username", "password", "role", "department"])
        writer.writerows(rows)

    return filename


# ------------------- RESUME ANALYSIS -------------------
def save_resume_analysis(username, score, feedback, skills):
    """Save AI Resume Analysis for a student"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO resume_analysis (username, score, feedback, skills) VALUES (?, ?, ?, ?)",
              (username, score, feedback, ",".join(skills)))
    conn.commit()
    conn.close()


def get_resume_analysis(username):
    """Retrieve latest resume analysis for the given student"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT score, feedback, skills FROM resume_analysis WHERE username = ? ORDER BY id DESC LIMIT 1",
              (username,))
    data = c.fetchone()
    conn.close()
    if data:
        return {"score": data[0], "feedback": data[1], "skills": data[2].split(",")}
    return None


# ------------------- HOD TABLES & ANALYTICS -------------------
def ensure_hod_tables():
    """Create extra tables required for HOD analytics and placements."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # student_profiles: student's academic info & placement status
    c.execute("""
        CREATE TABLE IF NOT EXISTS student_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            reg_no TEXT,
            cgpa REAL,
            placed INTEGER DEFAULT 0,
            package REAL DEFAULT 0
        )
    """)

    # placements: placement records
    c.execute("""
        CREATE TABLE IF NOT EXISTS placements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            company TEXT,
            package REAL,
            placed_on TEXT
        )
    """)

    conn.commit()
    conn.close()


def get_department_stats(department):
    """Return stats for a department (total, placed %, avg CGPA)."""
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
