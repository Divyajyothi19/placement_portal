# pages/drive_portal.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from database import DB_FILE

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Placement Drive Management", layout="wide")

# ---------------------- ACCESS CONTROL ----------------------
if "logged_in" not in st.session_state or st.session_state.get("role") != "Admin":
    st.error("🚫 Access Denied! Only Admin/TPO can access this page.")
    st.stop()

# ---------------------- INITIALIZE TABLES ----------------------
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
    conn.commit()
    conn.close()

ensure_drive_tables()

# ---------------------- HEADER ----------------------
st.title("🚀 Placement Drive Management")
st.markdown("""
Manage all placement drives from here.  
You can add, edit, close or view drives. Drives marked **Active** will be visible to eligible students in their portals.
""")

st.markdown("---")

# ---------------------- ADD NEW DRIVE ----------------------
st.subheader("🆕 Add a New Placement Drive")

col1, col2 = st.columns(2)
with col1:
    company = st.text_input("🏢 Company Name")
    role = st.text_input("💼 Role / Position")
    package = st.number_input("💰 Package (in LPA)", min_value=0.0, step=0.1)
    department = st.selectbox("🎓 Target Department", ["ALL", "CSE", "ECE", "EEE", "MECH", "CIVIL", "AI&DS"])
with col2:
    open_for_all = st.checkbox("🌐 Open for All Departments", value=(department == "ALL"))
    date = st.date_input("📅 Drive Date", datetime.now())
    deadline = st.date_input("⏰ Application Deadline", datetime.now())
    description = st.text_area("📝 Short Description (eligibility, process, etc.)")

if st.button("✅ Add Placement Drive"):
    if not company or not role or package <= 0:
        st.error("⚠️ Please fill all required fields (company, role, package).")
    else:
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            INSERT INTO drives (company, role, package, department, open_for_all, date, deadline, description, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (company, role, package, department, 1 if open_for_all else 0, str(date), str(deadline), description))
        conn.commit()
        conn.close()
        st.success(f"🎯 Drive for {company} added successfully!")

st.markdown("---")

# ---------------------- VIEW / MANAGE EXISTING DRIVES ----------------------
st.subheader("📋 Manage Existing Drives")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("SELECT id, company, role, package, department, open_for_all, date, deadline, description, is_active FROM drives ORDER BY id DESC")
rows = c.fetchall()
conn.close()

if not rows:
    st.info("No placement drives available yet. Add one above.")
else:
    df = pd.DataFrame(rows, columns=["ID", "Company", "Role", "Package", "Department", "Open for All", "Date", "Deadline", "Description", "Active"])
    st.dataframe(df, use_container_width=True)

    selected_id = st.selectbox("Select Drive ID to Edit or Close", [r[0] for r in rows])

    action_col1, action_col2, action_col3 = st.columns(3)
    with action_col1:
        if st.button("🛑 Close Drive"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("UPDATE drives SET is_active=0 WHERE id=?", (selected_id,))
            conn.commit()
            conn.close()
            st.warning(f"Drive ID {selected_id} closed successfully.")
            st.experimental_rerun()

    with action_col2:
        if st.button("🗑️ Delete Drive"):
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM drives WHERE id=?", (selected_id,))
            conn.commit()
            conn.close()
            st.error(f"Drive ID {selected_id} deleted permanently.")
            st.experimental_rerun()

st.markdown("---")

# ---------------------- FOOTER ----------------------
st.caption("💼 Placement Management Portal — Created for College Placement Automation © 2025")