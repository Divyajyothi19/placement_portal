# placement_engine.py
# Minimal safe placement_engine used by hod_portal.py
# Put this file in the project root (same folder as app.py and database.py)

import random
from io import BytesIO
from datetime import datetime

def evaluate_department(department, match_threshold=0.65, mark_placements=False):
    """
    Minimal evaluator (non-destructive). Returns a simple structure with placements/unplaced.
    This is a safe stub if you haven't yet added the full engine.
    """
    # no DB actions here — just simulate empty results
    return {
        "department": department,
        "evaluated_at": datetime.utcnow().isoformat(),
        "placements": [],   # list of dicts {username, company, package, match_score}
        "unplaced": [],     # list of dicts {username, best_company, best_score}
        "detailed": {}
    }

def generate_department_pdf(department, evaluation_result=None):
    """
    Minimal PDF generator that returns BytesIO or (None, err)
    """
    try:
        from fpdf import FPDF
    except Exception as e:
        return None, "FPDF not installed"

    if evaluation_result is None:
        evaluation_result = evaluate_department(department, mark_placements=False)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"{department} Department Placement Report", ln=True, align="C")
    pdf.ln(6)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, "This is a placeholder report. Add placement_engine.py for full features.")
    out = BytesIO()
    out.write(pdf.output(dest='S').encode('latin1'))
    out.seek(0)
    return out, None

def generate_ai_summary(department):
    """Return a quick AI-style summary (placeholder)"""
    return f"AI summary placeholder: department {department}. (Replace placement_engine.py with full engine for real summary.)"