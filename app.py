from flask import Flask, render_template, request, jsonify, redirect, session
import pymysql # Fixed: Use pymysql to avoid the Protobuf/Gemini conflict
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from backend.nlp_support import get_bot_response
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import google.generativeai as genai # Added Gemini library
import os
from dotenv import load_dotenv
load_dotenv()



app = Flask(__name__)
app.secret_key = "secret123"
app.url_map.strict_slashes = False

# --- GEMINI AI CONFIGURATION ---
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# --- MAIL CONFIGURATION ---
ADMIN_EMAIL = "lovelyganapathy10@gmail.com" 
SENDER_EMAIL = "mrmarimuthu0987@gmail.com" 
SENDER_PASSWORD = "tbvz pmmq rcot osfc"  

def send_admin_email(user_email, user_name, user_query):
    """Sends an email to the admin when the bot doesn't know the answer."""
    try:
        subject = f"Unknown Query from {user_name}"
        body = (f"The chatbot could not answer the following query:\n\n"
                f"User Name: {user_name}\n"
                f"User Email: {user_email}\n"
                f"Query: {user_query}\n\n"
                f"Please follow up with the student directly.")
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = ADMIN_EMAIL
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Mail Error: {e}")
        return False

def save_activity_log(user_id, activity_name):
    """Universal logging for Students, Parents, and Visitors with IP & User Agent."""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        sql = "INSERT INTO activity_logs (user_id, activity, ip_address, user_agent, created_at) VALUES (%s, %s, %s, %s, %s)"
        values = (
            user_id if user_id else 0, 
            activity_name, 
            request.remote_addr,
            request.user_agent.string,
            datetime.now()
        )
        cursor.execute(sql, values)
        db.commit()
        cursor.close()
        db.close()
    except Exception as e:
        print(f"Logging Error: {e}")

# ---------------- DB CONNECTION (FIXED) ----------------
def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="mspvl_db",
        cursorclass=pymysql.cursors.DictCursor # Maintains 'dictionary=True' behavior
    )

# ---------------- ALL 11+ ROUTES RESTORED ----------------

@app.route('/')
@app.route('/index')
def index():
    save_activity_log(session.get('user_id'), "Visited Page: Home")
    return render_template("index.html")

@app.route('/about')
def about():
    save_activity_log(session.get('user_id'), "Visited Page: About Us")
    return render_template("about.html")

@app.route('/contact')
def contact():
    save_activity_log(session.get('user_id'), "Visited Page: Contact Us")
    return render_template("contact.html")

@app.route('/admissions')
def admissions():
    save_activity_log(session.get('user_id'), "Visited Page: Admissions")
    return render_template("admissions.html")

@app.route('/courses')
def courses():
    save_activity_log(session.get('user_id'), "Visited Page: Courses")
    return render_template("courses.html")

@app.route('/chatbot')
def chatbot():
    save_activity_log(session.get('user_id'), "Visited Page: Chatbot")
    return render_template("chatbot.html")

@app.route('/visitor')
def visitor():
    return render_template("visitor.html")

# ---------------- SIGNUP LOGIC (RETAINED) ----------------

@app.route('/signup')
def signup_page():
    return render_template("signup.html")

@app.route('/visitor_signup')
def visitor_signup_page():
    return render_template("visitor_signup.html")

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json()
    username, email, password = data.get("username"), data.get("email"), data.get("password")
    hashed_password = generate_password_hash(password)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM user WHERE email=%s", (email,))
    if cur.fetchone():
        cur.close(); conn.close()
        return jsonify({"success": False, "message": "Email already exists"})
    cur.execute("INSERT INTO user (username, email, password, role) VALUES (%s,%s,%s,%s)", (username, email, hashed_password, 'student'))
    conn.commit()
    user_id = cur.lastrowid
    session["user_id"], session["username"], session["role"] = user_id, username, 'student'
    cur.close(); conn.close()
    return jsonify({"success": True, "message": "Account created successfully", "redirect": "/completepr"})

@app.route("/api/visitor_signup", methods=["POST"])
def api_visitor_signup():
    data = request.get_json()
    username, email, password, role = data.get("username"), data.get("email"), data.get("password"), data.get("role", "visitor")
    hashed_password = generate_password_hash(password)
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT id FROM user WHERE email=%s", (email,))
    if cur.fetchone():
        cur.close(); conn.close()
        return jsonify({"success": False, "message": "Email already exists"})
    cur.execute("INSERT INTO user (username, email, password, role) VALUES (%s,%s,%s,%s)", (username, email, hashed_password, role))
    conn.commit(); cur.close(); conn.close()
    return jsonify({"success": True, "message": f"{role.capitalize()} account created!", "redirect": "/login"})

# ---------------- PROFILE & LOGIN (RETAINED) ----------------

@app.route('/completepr')
def completepr_page():
    role = session.get('role', 'Visitor')
    save_activity_log(session.get('user_id'), f"Viewing Page: Complete Profile (Role: {role})")
    return render_template("completepr.html")

@app.route("/api/completepr", methods=["POST"])
def save_completepr():
    if "user_id" not in session: return jsonify({"success": False, "message": "Not logged in"})
    f, user_id = request.form, session["user_id"]
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("""INSERT INTO completepr_student (user_id, roll_number, admission_number, full_name, date_of_birth, phone_number, aadhar_number, course_enrolled, address, city, state, pincode, guardian_name, guardian_phone, tenth_school, tenth_percentage, emergency_contact) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""", 
        (user_id, f["roll_number"], f["admission_number"], f["full_name"], f["date_of_birth"], f["phone_number"], f["aadhar_number"], f["course_enrolled"], f["address"], f["city"], f["state"], f["pincode"], f["guardian_name"], f["guardian_phone"], f["tenth_school"], f["tenth_percentage"], f["emergency_contact"]))
        conn.commit(); session.pop("user_id")
        return jsonify({"success": True, "redirect": "/login"})
    except Exception as e: return jsonify({"success": False, "message": str(e)})
    finally: cur.close(); conn.close()

@app.route('/login')
def login_page(): return render_template("login.html")

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username_input, password_input, selected_role = data.get('username', '').strip(), data.get('password', ''), data.get('role')
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM user WHERE email=%s OR username=%s", (username_input, username_input))
    user = cur.fetchone()
    cur.close(); conn.close()
    if not user or not check_password_hash(user["password"], password_input):
        return jsonify({"success": False, "message": "Invalid credentials."})
    db_role = user.get('role') or 'student'
    if db_role != selected_role: return jsonify({"success": False, "message": f"Account is {db_role}, not {selected_role}."})
    session['user_id'], session['role'], session['username'] = user["id"], db_role, user['username']
    save_activity_log(user["id"], f"Logged in as {db_role}")
    targets = {"admin": "/admin_dashboard", "student": "/student_dashboard", "parent": "/parent_view"}
    return jsonify({"success": True, "redirect": targets.get(db_role, "/visitor")})

# ---------------- DASHBOARDS & EDITING (RETAINED) ----------------

@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin': return redirect('/login')
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT u.id, u.username, s.full_name, s.course_enrolled FROM user u JOIN completepr_student s ON u.id = s.user_id")
    all_students = cur.fetchall()
    cur.execute("SELECT user_id, activity, ip_address, user_agent, created_at FROM activity_logs ORDER BY id DESC")
    activity_logs = cur.fetchall()
    cur.close(); conn.close()
    return render_template("admin_dashboard.html", students=all_students, logs=activity_logs)

@app.route('/student_dashboard')
def student_dashboard():
    if 'user_id' not in session: return redirect('/login')
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM completepr_student WHERE user_id = %s", (session["user_id"],))
    student_info = cur.fetchone()
    cur.close(); conn.close()
    return render_template("student_dashboard.html", student=student_info)

@app.route('/parent_view')
def parent_view():
    if 'user_id' not in session or session.get('role') != 'parent': return redirect('/login')
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM completepr_student WHERE guardian_name = %s", (session.get('username'),))
    students = cur.fetchall(); cur.close(); conn.close()
    return render_template("parent_dashboard.html", students=students)

@app.route('/edit_profile')
def edit_profile_page():
    if 'user_id' not in session: return redirect('/login')
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM completepr_student WHERE user_id = %s", (session["user_id"],))
    student_info = cur.fetchone(); cur.close(); conn.close()
    if not student_info: return redirect('/completepr') 
    return render_template("edit_profile.html", student=student_info)

@app.route("/api/update_profile", methods=["POST"])
def update_profile():
    if "user_id" not in session: return jsonify({"success": False, "message": "Unauthorized"})
    f, user_id = request.form, session["user_id"]
    conn = get_db_connection(); cur = conn.cursor()
    try:
        cur.execute("UPDATE completepr_student SET full_name=%s, phone_number=%s, course_enrolled=%s, address=%s WHERE user_id=%s", (f["full_name"], f["phone_number"], f["course_enrolled"], f["address"], user_id))
        conn.commit(); return jsonify({"success": True})
    except Exception as e: return jsonify({"success": False, "message": str(e)})
    finally: cur.close(); conn.close()

# ---------------- CHATBOT API (FULL RESTORATION + GEMINI) ----------------

@app.route('/api/chat/send', methods=['POST'])
def handle_chat_main():
    user_id = session.get('user_id', 0)
    role = session.get('role', 'visitor')
    data = request.get_json()
    user_text = data.get("message", "")

    # Log activity for admin monitoring
    save_activity_log(user_id, f"[{role.upper()}] Chatbot Query: {user_text}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # 1. Get User Profile for Email/Username
        cur.execute("SELECT email, username FROM user WHERE id = %s", (user_id,))
        user_profile = cur.fetchone() or {'email': 'Visitor@Guest', 'username': 'Visitor'}
        
        # 2. CRITICAL: Fetch the Student's Personal Details from the Database
        cur.execute("SELECT * FROM completepr_student WHERE user_id = %s", (user_id,))
        student_data = cur.fetchone()
        
        # 3. Try Local NLP (nlp_support.py)
        bot_text, intent, confidence = get_bot_response(user_text, student_data)

        # Persist the user's message first
        cur.execute("INSERT INTO chat_messages (sender_id, message, is_ai_response, intent) VALUES (%s, %s, 0, %s)", (user_id, user_text, "user"))
        
        # 4. If local bot is unsure, use Gemini with "Personal Context"
        if intent == "unknown":
            try:
                # We build a 'Knowledge Base' for Gemini using the database results
                if student_data:
                    personal_context = (
                        f"Student Name: {student_data['full_name']}, "
                        f"Roll No: {student_data['roll_number']}, "
                        f"Course: {student_data['course_enrolled']}, "
                        f"Guardian: {student_data['guardian_name']}, "
                        f"Phone: {student_data['phone_number']}."
                    )
                else:
                    personal_context = "The user is a visitor and has not completed their profile yet."

                # System prompt combining College Info + Personal Details
                system_prompt = (
                    f"You are the MSPVL College AI. Here is the data for the current user: {personal_context}. "
                    f"Answer the user's question accurately using this data. "
                    f"User Question: {user_text}"
                )
                
                ai_response = gemini_model.generate_content(system_prompt)
                
                if ai_response.text:
                    bot_text = ai_response.text
                    intent = "gemini_ai"
                else:
                    raise Exception("Empty Response")

            except Exception as e:
                # Fallback to Admin Email if Gemini fails
                print(f"Gemini Error: {e}")
                send_admin_email(user_profile['email'], user_profile['username'], user_text)
                bot_text = f"I couldn't retrieve that. I've notified the Admin to help you at {user_profile['email']}."

        # 5. Log the final message to chat_messages table
        cur.execute("INSERT INTO chat_messages (sender_id, message, is_ai_response, intent) VALUES (%s, %s, 1, %s)", 
                    (user_id, bot_text, intent))
        conn.commit()
        return jsonify({"success": True, "response": bot_text})
    except Exception as e:
        conn.rollback()
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        cur.close()
        conn.close()

@app.route('/logout')
def logout():
    save_activity_log(session.get('user_id'), "Logged out")
    session.clear(); return redirect('/login')

if __name__ == "__main__":
    app.run(debug=True)
