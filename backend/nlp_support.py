import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key="AIzaSyAeTokpZ-wv1sGlcRp9DeQMUX_xwJZOEWY")
model = genai.GenerativeModel("gemini-1.5-flash")


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-zA-Z0-9\u0B80-\u0BFF\s]", "", text)  # keep Tamil + English
    return text.strip()


def get_gemini_response(user_text):
    prompt = f"""
You are an AI assistant for MSPVL Polytechnic College.
Answer clearly and shortly.

User: {user_text}
"""
    response = model.generate_content(prompt)
    return response.text


def get_bot_response(user_text, student_data=None):
    user_text = clean_text(user_text)

    # --- 1. GREETINGS ---
    greetings = {
        "hi": "Hello! Welcome to MSPVL College Helpdesk. How can I assist you today?",
        "hello": "Hi there! I am your AI assistant. You can ask me about admissions, fees, or courses.",
        "thanks": "You're very welcome!",
        "thank you": "Happy to help!",
        "vanakkam": "வணக்கம்! நான் உங்களுக்கு எப்படி உதவ முடியும்?"
    }

    if user_text in greetings:
        return greetings[user_text], "greeting", 1.0


    # --- 2. FAST RESPONSES (YOUR CORE DATA) ---
    fast_responses = {
        "fee": ("Course fees range from ₹35,000 to ₹55,000 per semester.", "fee", 0.98),
        "admission": ("Admissions for 2026 are open until July 31.", "admission", 0.98),
        "hostel": ("Separate hostels are available for boys and girls.", "hostel", 0.95),
        "placement": ("Top recruiters include TCS, Wipro, and HCL.", "placement", 0.95),
        "exam fees": ("Exam fees per semester is ₹600.", "exam_fees", 0.98),
        "library": ("Library is open from 8:30 AM to 6:30 PM.", "library", 0.95),
        "uniform": ("Uniform is compulsory for all students.", "uniform", 0.95),
        "attendance": ("Minimum 75% attendance is required.", "attendance", 0.95),
    }

    for key, value in fast_responses.items():
        if key in user_text:
            return value


    # --- 3. PERSONAL DATA ---
    if "name" in user_text and student_data:
        return f"Your name is {student_data.get('full_name','Unknown')}", "personal", 1.0

    if "roll" in user_text and student_data:
        return f"Your roll number is {student_data.get('roll_number','Unknown')}", "personal", 1.0

    if "department" in user_text and student_data:
        return f"Your department is {student_data.get('course_enrolled','Unknown')}", "personal", 1.0


    # --- 4. AI FALLBACK (GEMINI) ---
    ai_reply = get_gemini_response(user_text)
    return ai_reply, "ai_response", 0.85
