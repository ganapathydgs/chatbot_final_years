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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Gemini init error: {e}")


def test_gemini_connection():
    """🧪 Test Gemini API key on startup - returns status"""
    global gemini_model
    
    print("\n🔍 TESTING GEMINI API CONNECTION...")
    print("=" * 50)
    
    # 1. Check .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file MISSING!")
        print("   → Create .env with: GEMINI_API_KEY=your_key_here")
        return False
    
    # 2. Check API key loaded
    if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_key_here":
        print("❌ GEMINI_API_KEY missing or invalid in .env")
        return False
    
    # 3. Try actual API call (REAL VALIDATION)
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Send test prompt (takes 2-3 seconds)
        response = model.generate_content("Say 'API WORKS!'")
        test_result = response.text.strip()
        
        if "API WORKS" in test_result.upper():
            print("✅ GEMINI API KEY VALID ✓")
            print(f"   🟢 Model: gemini-1.5-flash")
            print(f"   📡 Latency: {len(test_result)} chars")
            gemini_model = model  # Set global model
            return True
        else:
            print("❌ API responded but unexpected result")
            return False
            
    except Exception as e:
        error_msg = str(e).lower()
        print(f"❌ GEMINI API ERROR: {e}")
        if "invalid key" in error_msg:
            print("   → Get new key: aistudio.google.com/app/apikey")
        elif "quota" in error_msg:
            print("   → Free quota used up")
        elif "network" in error_msg:
            print("   → Check internet connection")
        return False

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

    # notification for the admins
def send_admin_query_email(user_name, user_role, user_email, query_text, query_id):
    """Send NEW admin query to admin email"""
    try:
        subject = f"🚨 NEW STUDENT QUERY #{query_id}"
        body = f"""
🚨 NEW ADMIN QUERY RECEIVED!

Student: {user_name} ({user_role})
Email: {user_email}
Query ID: #{query_id}
Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

QUERY:
{query_text}

---
🔗 Reply: http://localhost:5000/admin_queries
---
        """
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = ADMIN_EMAIL
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        print(f"✅ Admin query email sent for #{query_id}")
        return True
    except Exception as e:
        print(f"Admin query email error: {e}")
        return False


@app.route('/api/chat/send-to-admin', methods=['POST'])
def send_to_admin():
    user_id = session.get('user_id', 0)
    role = session.get('role', 'visitor')
    data = request.get_json()
    message = data.get("message", "").strip()
    
    if not message:
        return jsonify({"success": False, "message": "Message cannot be empty"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        username = session.get('username', 'Visitor')
        
        # Get user email
        cur.execute("SELECT email FROM user WHERE id = %s", (user_id,))
        user_row = cur.fetchone()
        user_email = user_row['email'] if user_row else 'Not registered'
        
        # Save to database
        cur.execute("""
            INSERT INTO admin_queries (user_id, username, role, query, status, created_at) 
            VALUES (%s, %s, %s, %s, 'pending', NOW())
        """, (user_id, username, role, message))
        query_id = cur.lastrowid
        
        conn.commit()
        
        # Send email to admin
        send_admin_query_email(username, role, user_email, message, query_id)
        
        # Log activity
        save_activity_log(0, f"🚨 ADMIN QUERY #{query_id}: {message[:100]}... from {username}")
        
        return jsonify({
            "success": True, 
            "response": f"✅ Query sent to admin (ID: #{query_id})! Email notification sent.",
            "intent": "admin_query_sent"
        })
    except Exception as e:
        conn.rollback()
        print(f"Admin query error: {e}")
        return jsonify({"success": False, "message": "Failed to send query"}), 500
    finally:
        cur.close()
        conn.close()


# Admin view route (add to admin_dashboard)
@app.route('/admin_queries')
def admin_queries():
    if session.get('role') != 'admin':
        return redirect('/login')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get pending count
    cur.execute("SELECT COUNT(*) as pending FROM admin_queries WHERE status = 'pending'")
    pending_count = cur.fetchone()['pending']
    
    # Get all queries
    cur.execute("""
        SELECT aq.*, u.email, u.username as user_name
        FROM admin_queries aq 
        LEFT JOIN user u ON aq.user_id = u.id 
        ORDER BY aq.created_at DESC
    """)
    queries = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('admin_queries.html', queries=queries, pending_count=pending_count)

@app.route('/api/admin_queries/<int:query_id>/reply', methods=['POST'])
def reply_query(query_id):
    if session.get('role') != 'admin':
        return jsonify({"success": False, "message": "Admin only"}), 403
    
    response = request.form.get('response', '').strip()
    if not response:
        return jsonify({"success": False, "message": "Response required"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE admin_queries 
            SET status = 'answered', admin_response = %s, updated_at = NOW()
            WHERE id = %s
        """, (response, query_id))  # ✅ MATCHES HTML PERFECTLY
        
        conn.commit()
        
        # Log activity
        save_activity_log(0, f"✅ ADMIN REPLIED TO QUERY #{query_id}: {response[:100]}...")
        
        return jsonify({"success": True, "response": "✅ Query replied successfully"})
    except Exception as e:
        conn.rollback()
        print(f"Admin reply error: {e}")
        return jsonify({"success": False, "message": "Failed to reply query"}), 500
    finally:
        cur.close()
        conn.close()




# Close an admin query without replying
@app.route('/api/admin_queries/<int:query_id>/close', methods=['POST'])
def close_query(query_id):
    if session.get('role') != 'admin':
        return jsonify({"success": False, "message": "Admin only"}), 403
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE admin_queries 
            SET status = 'closed', closed_at = NOW() 
            WHERE id = %s
        """, (query_id,))
        conn.commit()
        save_activity_log(0, f"🛑 ADMIN CLOSED QUERY #{query_id}")
        return jsonify({"success": True, "message": "Query closed"})
    except Exception as e:
        conn.rollback()
        print(f"Admin close error: {e}")
        return jsonify({"success": False, "message": "Failed to close query"}), 500
    finally:
        cur.close()
        conn.close()

# ---------------- CHATBOT API (FULL RESTORATION + GEMINI) ----------------

@app.route('/api/chat/send', methods=['POST'])
def handle_chat_main():
    user_id = session.get('user_id', 0)
    role = session.get('role', 'visitor')
    data = request.get_json()
    user_text = data.get("message", "").strip()

    # Log activity
    save_activity_log(user_id, f"[{role.upper()}] Chat: {user_text}")

    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Get user profile + student data
        cur.execute("SELECT email, username FROM user WHERE id = %s", (user_id,))
        user_profile = cur.fetchone() or {'email': 'Visitor@Guest', 'username': 'Visitor'}
        cur.execute("SELECT * FROM completepr_student WHERE user_id = %s", (user_id,))
        student_data = cur.fetchone()

        # 1️⃣ ALWAYS TRY GEMINI FIRST (handles ANY question)
        bot_text = "I'm the MSPVL Assistant. Ask me anything!"
        intent = "gemini_ai"
        confidence = 1.0

        if gemini_model:
            try:
                # Build smart context
                context = f"You are MSPVL College AI Assistant. "
                if student_data:
                    context += f"Student: {student_data['full_name']} (Roll: {student_data['roll_number']}, Course: {student_data['course_enrolled']}). "
                context += f"Current time: {datetime.now().strftime('%d %b %Y, %I:%M %p')}. Answer: {user_text}"

                response = gemini_model.generate_content(context)
                if response and response.text.strip():
                    bot_text = response.text.strip()
                else:
                    bot_text = "I understand your question! Ask about college or anything else."
                
            except Exception as e:
                print(f"Gemini error: {e}")
                # 2️⃣ NLP FALLBACK (if Gemini fails)
                bot_text, intent, confidence = get_bot_response(user_text, student_data)
        else:
            # 3️⃣ NLP ONLY (no Gemini key)
            bot_text, intent, confidence = get_bot_response(user_text, student_data)

        # Save messages to DB
        cur.execute("INSERT INTO chat_messages (sender_id, message, is_ai_response, intent) VALUES (%s, %s, 0, %s)", (user_id, user_text, "user"))
        cur.execute("INSERT INTO chat_messages (sender_id, message, is_ai_response, intent) VALUES (%s, %s, 1, %s)", (user_id, bot_text, intent))
        conn.commit()

        return jsonify({
            "success": True, 
            "response": bot_text,
            "intent": intent,
            "confidence": confidence
        })

    except Exception as e:
        conn.rollback()
        print(f"Chat Error: {e}")
        return jsonify({"success": False, "message": "Something went wrong."}), 500
    finally:
        cur.close()
        conn.close()


@app.route('/logout')
def logout():
    save_activity_log(session.get('user_id'), "Logged out")
    session.clear(); return redirect('/login')

if __name__ == "__main__":
     # 🔥 AUTO-CHECK GEMINI ON STARTUP
    gemini_status = test_gemini_connection()
    
    print("\n🚀 MSPVL College Chatbot Starting...")
    print(f"📱 Gemini Status: {'🟢 READY' if gemini_status else '🔴 OFFLINE'}")
    print(f"🧠 NLP Fallback: Always ON")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
