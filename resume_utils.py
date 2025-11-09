import fitz  # PyMuPDF
import re

# ------------------- PDF Text Extraction -------------------
def extract_text_from_pdf_bytes(file_bytes):
    text = ""
    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        for page in pdf:
            text += page.get_text("text")
    return text

# ------------------- Simple Resume Scoring Logic -------------------
def simple_resume_score(text, cgpa=None, department=None):
    """
    A lightweight AI-like resume scorer.
    This uses keyword detection, structure check, and GPA boost.
    """

    text_lower = text.lower()

    # Key sections expected
    sections = ["education", "skills", "projects", "experience", "certifications"]
    section_score = sum([1 for s in sections if s in text_lower]) / len(sections) * 40

    # Detect skills
    skill_keywords = [
        "python", "java", "c++", "sql", "html", "css", "javascript", "ml",
        "ai", "data", "network", "cloud", "django", "react", "node", "flask"
    ]
    detected_skills = [s for s in skill_keywords if s in text_lower]
    skill_score = min(len(detected_skills), 10) / 10 * 40

    # GPA influence
    gpa_score = 0
    if cgpa:
        try:
            cgpa_val = float(cgpa)
            if cgpa_val >= 9:
                gpa_score = 20
            elif cgpa_val >= 8:
                gpa_score = 15
            elif cgpa_val >= 7:
                gpa_score = 10
        except ValueError:
            gpa_score = 0

    # Final score
    total_score = section_score + skill_score + gpa_score

    # Feedback generation
    missing_sections = [s for s in sections if s not in text_lower]
    feedback = []
    if missing_sections:
        feedback.append(f"Add these sections: {', '.join(missing_sections)}.")
    if len(detected_skills) < 5:
        feedback.append("Add more technical skills for better visibility.")
    if total_score < 60:
        feedback.append("Consider improving formatting and including quantifiable results in projects.")

    feedback_text = " ".join(feedback) if feedback else "Resume looks strong!"

    # Department adjustment
    if department:
        feedback_text += f" Your department ({department}) has strong placement scope — tailor your projects accordingly."

    return total_score, feedback_text, detected_skills