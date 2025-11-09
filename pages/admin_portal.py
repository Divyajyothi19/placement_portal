import streamlit as st
import pandas as pd
import os
import csv
import sqlite3
from datetime import datetime
from database import add_auto_user, get_all_users, export_users_to_csv

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="Admin Portal", layout="wide", page_icon="👩‍💼")

# ---------------------- ACCESS CONTROL ----------------------
if "logged_in" not in st.session_state or st.session_state.get("role") != "Admin":
    st.error("🚫 Access Denied! Please log in as Admin.")
    st.stop()

# ---------------------- HEADER ----------------------
st.title("👩‍💼 Admin Portal — Manage & Generate Accounts")
st.markdown("""
Welcome to the **Placement Management Admin Dashboard**.  
Here you can create Student and HOD accounts, export user data, and monitor the overall portal status.
""")

st.divider()

# ---------------------- SETTINGS / UTILITIES ----------------------
GENERATED_CSV = "generated_users.csv"

def append_to_generated_csv(rows):
    """Append rows (list of dicts) to generated_users.csv (create header if missing)."""
    file_exists = os.path.exists(GENERATED_CSV)
    with open(GENERATED_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["username", "password", "role", "department", "generated_on"])
        for r in rows:
            writer.writerow([
                r["username"],
                r["password"],
                r["role"],
                r.get("department", ""),
                r["generated_on"]
            ])

# ---------------------- DEPARTMENT OPTIONS ----------------------
DEPARTMENTS = ["CSE", "ECE", "EEE", "MECH", "CIVIL", "AI&DS"]

# ---------------------- SYSTEM SUMMARY ----------------------
st.subheader("📊 System Summary")

conn = sqlite3.connect("placement_portal.db")
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM users WHERE role='Student'")
student_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM users WHERE role='HOD'")
hod_count = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM users WHERE role='Admin'")
admin_count = c.fetchone()[0]
conn.close()

col1, col2, col3 = st.columns(3)
col1.metric("👩‍🎓 Total Students", student_count)
col2.metric("👨‍🏫 Total HODs", hod_count)
col3.metric("👩‍💼 Admin Accounts", admin_count)

st.divider()

# ---------------------- GENERATE NEW ACCOUNTS ----------------------
st.subheader("➕ Quick Generate Accounts")

col1, col2, col3 = st.columns([3, 2, 1])
with col1:
    role = st.selectbox("Role to create", ["Student", "HOD", "Admin"])

with col2:
    if role == "HOD":
        department = st.radio("Select Department (required for HOD)", DEPARTMENTS)
    else:
        department = st.text_input("Department (optional for Students/Admins)", "")

with col3:
    count = st.number_input("How many?", min_value=1, max_value=200, value=1, step=1)

# ---------------------- CHECK FUNCTIONS ----------------------
def hod_exists(department):
    conn = sqlite3.connect("placement_portal.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE role='HOD' AND department=?", (department,))
    exists = c.fetchone()
    conn.close()
    return exists is not None

def admin_exists():
    conn = sqlite3.connect("placement_portal.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE role='Admin'")
    count = c.fetchone()[0]
    conn.close()
    return count >= 1

# ---------------------- CREATE USERS ----------------------
if st.button("🧾 Generate & Save Accounts"):
    created = []
    errors = []

    # ✅ Restrict multiple Admins
    if role == "Admin":
        if admin_exists():
            st.error("🚫 Only one Admin account is allowed. Access to create more Admins is restricted.")
            st.stop()

    # ✅ HOD must be unique per department
    if role == "HOD":
        if not department:
            st.error("⚠️ Please select a department for HOD.")
            st.stop()
        if hod_exists(department):
            st.error(f"⚠️ A HOD already exists for the {department} department.")
            st.stop()

    # ✅ Create Users
    for _ in range(int(count)):
        try:
            username, password = add_auto_user(role, department if department else None)
            created.append({
                "username": username,
                "password": password,
                "role": role,
                "department": department,
                "generated_on": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            errors.append(str(e))

    # ✅ Save Results
    if created:
        append_to_generated_csv(created)
        st.success(f"✅ {len(created)} account(s) created successfully.")
        st.dataframe(pd.DataFrame(created)[["username", "password", "role", "department"]], use_container_width=True)

    if errors:
        st.error("Some errors occurred:")
        for e in errors:
            st.text(f" - {e}")

st.divider()

# ---------------------- DOWNLOAD GENERATED USERS CSV ----------------------
st.subheader("📤 Download Latest Generated Credentials")

if os.path.exists(GENERATED_CSV):
    with open(GENERATED_CSV, "rb") as f:
        st.download_button(
            "⬇️ Download generated_users.csv",
            data=f,
            file_name="generated_users.csv",
            mime="text/csv"
        )
else:
    st.info("No generated CSV found yet. Use 'Generate & Save' to create credentials.")

st.divider()

# ---------------------- VIEW ALL USERS FROM DB ----------------------
st.subheader("📋 All Users in Database")

db_users = get_all_users()
if db_users:
    df = pd.DataFrame(db_users, columns=["id", "username", "password", "role", "department"])
    st.dataframe(df.drop(columns=["id"]), use_container_width=True)

    if st.button("📦 Export All Users (CSV)"):
        csv_path = export_users_to_csv("all_users_export.csv")
        with open(csv_path, "rb") as f:
            st.download_button(
                "⬇️ Download all_users_export.csv",
                data=f,
                file_name="all_users_export.csv",
                mime="text/csv"
            )
else:
    st.info("No users found in the database yet.")

st.divider()

# ---------------------- FOOTER NOTES ----------------------
st.markdown("""
**Notes**
- 🧩 Only **one Admin account** can exist.  
- 👨‍🏫 Each department can have **only one HOD**.  
- 🧑‍💻 Department is required for HOD and optional for others.  
- 📁 `generated_users.csv` stores only newly generated credentials.  
- 💾 Use **Export All Users** to download full user database.
""")

st.caption("© 2025 College Placement Portal | Admin Dashboard")