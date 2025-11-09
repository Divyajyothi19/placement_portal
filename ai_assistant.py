# ai_assistant.py
import os
from openai import OpenAI

# ✅ Initialize OpenAI client (reads API key from environment)
# Run this once in PowerShell: setx OPENAI_API_KEY "your_api_key"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def ask_ai(prompt: str, role: str = "general") -> str:
    """
    Handles AI conversations across all roles.
    role: "student", "hod", "admin" — controls tone and context.
    """

    # Role-based system personalities
    base_prompt = {
        "student": (
            "You are Career-AI, a friendly and smart assistant that helps students in the college placement portal. "
            "Assist them in understanding placement drives, resume preparation, interview readiness, and skills improvement. "
            "If asked unrelated or personal questions, respond politely and guide them back to placement-related topics."
        ),
        "hod": (
            "You are AIDEX, the HOD’s AI-driven analytics assistant. "
            "Provide department-level insights like placement statistics, recruiter trends, skill gaps, and student readiness. "
            "Always maintain a formal, data-driven tone and avoid personal or speculative comments."
        ),
        "admin": (
            "You are AIVA, the Admin’s intelligent assistant in the Placement Portal. "
            "Help manage user accounts, check database issues, generate CSVs, and provide quick troubleshooting or procedural help. "
            "Be professional, concise, and solution-oriented."
        ),
        "general": "You are a helpful assistant for the college placement portal."
    }

    system_message = base_prompt.get(role, base_prompt["general"])

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # ✅ lightweight, faster model
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=350,
        )

        # Extract and return AI response
        return completion.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ AI Assistant error: {str(e)}"