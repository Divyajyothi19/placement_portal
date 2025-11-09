# ---------------------- PATH FIX ----------------------
import os, sys
HERE = os.path.dirname(__file__)
REPO_ROOT = os.path.abspath(os.path.join(HERE, ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# ---------------------- IMPORTS ----------------------
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from io import BytesIO
from datetime import datetime
from database import (
    DB_FILE,
    get_department_stats,
    get_top_recruiters,
    get_skill_gap_insights,
)

# ---------------------- PAGE CONFIG ----------------------
st.set_page_config(page_title="HOD Portal", layout="wide")

# ---------------------- ACCESS CONTROL ----------------------
if "logged_in" not in st.session_state or st.session_state.get("role") != "HOD":
    st.error("🚫 Access Denied! Please log in as a HOD.")
    st.stop()

hod_username = st.session_state["username"]

# ---------------------- GET HOD DEPARTMENT ----------------------
def get_hod_department(username):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT department FROM users WHERE username = ? AND role='HOD'", (username,))
    r = c.fetchone()
    conn.close()
    return r[0] if r else None

department = get_hod_department(hod_username)
if not department:
    st.warning("⚠️ No department found for this HOD. Contact Admin.")
    st.stop()

# ---------------------- HEADER ----------------------
st.title(f"👨‍🏫 HOD Dashboard — {department} Department")
st.markdown("""
Welcome to your **Department Placement Management Portal**.  
Here, you can view analytics, placement insights, student performance, and generate reports.
""")

# ---------------------- DEPARTMENT ANALYTICS ----------------------
st.subheader("📊 Department Statistics")
stats = get_department_stats(department)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Students", stats["total_students"])
col2.metric("Placed Students", stats["placed_count"])
col3.metric("Unplaced Students", stats["unplaced_count"])
col4.metric("Placement %", f"{stats['placed_percentage']}%")
st.metric("Avg CGPA (Placed)", stats["avg_cgpa_placed"])

# ---------------------- STUDENT DETAILS ----------------------
st.markdown("---")
st.subheader("🎓 Student Placement Details")

conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute("""
    SELECT u.username, sp.cgpa, sp.placed, sp.package, ra.score
    FROM users u
    LEFT JOIN student_profiles sp ON u.username = sp.username
    LEFT JOIN (
        SELECT username, MAX(id) AS last_id FROM resume_analysis GROUP BY username
    ) t ON t.username = u.username
    LEFT JOIN resume_analysis ra ON ra.id = t.last_id
    WHERE u.role = 'Student' AND u.department = ?
""", (department,))
rows = c.fetchall()
conn.close()

if not rows:
    st.info("No student records yet.")
else:
    df = pd.DataFrame(rows, columns=["Username", "CGPA", "Placed", "Package (LPA)", "Resume Score"])
    placed_df = df[df["Placed"] == 1]
    unplaced_df = df[(df["Placed"] != 1) | (df["Placed"].isnull())]

    st.write("### ✅ Placed Students")
    if not placed_df.empty:
        st.dataframe(placed_df, width='stretch')
    else:
        st.warning("No placed students yet.")

    st.write("### 🚫 Unplaced Students")
    if not unplaced_df.empty:
        st.dataframe(unplaced_df, width='stretch')
    else:
        st.success("🎉 All students placed!")

# ---------------------- VISUALIZATION ----------------------
st.markdown("---")
st.subheader("📈 Placement Overview")

if stats["total_students"] > 0:
    fig, ax = plt.subplots()
    ax.pie(
        [stats["placed_count"], stats["unplaced_count"]],
        labels=["Placed", "Unplaced"],
        autopct="%1.1f%%",
        startangle=90,
        colors=["#4CAF50", "#FFC107"]
    )
    ax.axis("equal")
    st.pyplot(fig)
else:
    st.info("No student data to visualize.")

# ---------------------- TOP RECRUITERS ----------------------
st.markdown("---")
st.subheader("🏢 Top Recruiters")

top_recs = get_top_recruiters(department)
if top_recs:
    rec_df = pd.DataFrame(top_recs, columns=["Company", "Students Placed", "Avg Package (LPA)"])
    st.dataframe(rec_df, width='stretch')
else:
    st.info("No recruiters have been added yet for this department.")

# ---------------------- SKILL GAP INSIGHTS ----------------------
st.markdown("---")
st.subheader("🧠 Skill Gap Insights")

skill_insight = get_skill_gap_insights(department)
if skill_insight:
    st.write("**AI Recommendation:**", skill_insight["recommendation"])
else:
    st.info("Skill gap insights not available yet.")

# ---------------------- AI ASSISTANT ----------------------
st.markdown("---")
st.subheader("🤖 AI Placement Assistant")

with st.expander("💬 Chat with AI Assistant"):
    user_input = st.text_input("Ask about placement performance, improvements, or recruiter stats:")
    if user_input:
        if "placement" in user_input.lower():
            st.write("📊 The department placement rate is improving steadily this semester.")
        elif "recruiter" in user_input.lower():
            st.write("🏢 Top recruiters this year are Infosys, TCS, and Wipro.")
        elif "skill" in user_input.lower():
            st.write("🧠 Students should focus on Data Visualization and SQL skills.")
        else:
            st.write("🤖 Try improving resumes with project-based learning and certifications.")

# ---------------------- AI SUMMARY & PDF ----------------------
st.markdown("---")
st.subheader("📄 Generate AI Summary Report")

ai_summary = f"""
📊 Department: {department}
• Total Students: {stats['total_students']}
• Placed Students: {stats['placed_count']}
• Unplaced Students: {stats['unplaced_count']}
• Avg CGPA (Placed): {stats['avg_cgpa_placed']}
• Recommendation: Focus on Data Analytics, Python, and Communication Skills.

🧠 Department placement improving — expected to reach 90% next cycle.
"""

st.info(ai_summary)

try:
    from fpdf import FPDF
    if st.button("📥 Generate Report PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"{department} Department Placement Report", ln=True, align="C")
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, ai_summary)
        pdf.ln(10)
        pdf.cell(0, 10, f"Generated on {datetime.now().strftime('%d %b %Y, %I:%M %p')}", ln=True, align="C")

        pdf_output = BytesIO()
        pdf_bytes = pdf.output(dest="S").encode("latin1")
        pdf_output.write(pdf_bytes)
        pdf_output.seek(0)
        fname = f"{department}_Placement_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        st.download_button("⬇️ Download Department Report", data=pdf_output, file_name=fname, mime="application/pdf")
except Exception:
    st.warning("⚠️ PDF generation not available. Run `pip install fpdf`.")
