def get_bot_response(user_text, student_data=None):
    # Normalize input for easier matching
    user_text = user_text.lower().strip()
    
    # --- 1. NEW FEATURE: GREETINGS & POLITENESS ---
    greetings = {
        "hi": "Hello! Welcome to MSPVL College Helpdesk. How can I assist you today?",
        "hello": "Hi there! I am your AI assistant. You can ask me about admissions, fees, or courses.",
        "thanks": "You're very welcome! Is there anything else you'd like to know?",
        "thank you": "Happy to help! Let me know if you have more questions.",
        "vanakkam": "வணக்கம்! நான் உங்களுக்கு எப்படி உதவ முடியும்?"
    }
    
    for greet in greetings:
        if greet == user_text: 
            return greetings[greet], "greeting", 1.0

    # --- 2. FAST-PATH LOOKUP (Default Features + Your New Content) ---
    fast_responses = {
        # Tamil Keywords
        "கட்டணம்": ("கல்லூரி கட்டணம் செமஸ்டருக்கு ₹35,000 முதல் ₹55,000 வரை.", "fee_inquiry", 0.98),
        "சேர்க்கை": ("2026 ஆம் ஆண்டிற்கான சேர்க்கை ஜூலை 31 வரை திறந்திருக்கும். நீங்கள் ஆன்லைனில் விண்ணப்பிக்கலாம்.", "admission_info", 0.98),
        "நேரம்": ("🕒 கல்லூரி நேரம்: காலை 9:00 முதல் மாலை 4:10 வரை.", "college_timings", 0.98),
        "விடுதி": ("மாணவர் மற்றும் மாணவிகளுக்கு தனித்தனி பாதுகாப்பான விடுதி வசதிகள் உள்ளன.", "hostel_info", 0.95),
        "உணவு": ("🍴 உணவகத்தில் காலை 8:00 முதல் மாலை 5:00 வரை தரமான உணவு கிடைக்கும்.", "canteen_info", 0.98),
        "தேர்வு": ("📅 செமஸ்டர் தேர்வுகள் ஏப்ரல் மற்றும் நவம்பர் மாதங்களில் நடைபெறும்.", "exam_info", 0.98),
        "உதவித்தொகை": ("தகுதியுள்ள மாணவர்களுக்கு அரசு மற்றும் தனியார் உதவித்தொகைகள் வழங்கப்படுகின்றன.", "scholarship_info", 0.98),

        # English Keywords
        "admission": ("Admissions for 2026 are open until July 31st. You can apply via the portal in the Admin section.", "admission_info", 0.95),
	"exam fees": ("The Exam fees of the semester is 💵600 rupees.","exam_fees",0.98),
        "fee": ("Course fees at MSPVL range from ₹35,000 to ₹55,000 per semester.", "fee_inquiry", 0.95),
        "scholarships": ("We support NSP and State scholarships based on merit and community. Apply through the Scholarship portal.", "scholarship_info", 0.98),
        "hostel": ("We offer separate secure hostels for boys and girls with Wi-Fi and mess facilities.", "hostel_info", 0.90),
        "placement": ("Top recruiters include TCS, Wipro, and HCL with avg packages of ₹4.5 LPA.", "placement_info", 0.98),
        "computer science": ("The Computer Science department covers Python, AI, and Web Development. You can download the syllabus from your dashboard.", "cs_syllabus", 0.98),
        "electronics": ("The ECE department features advanced VLSI and Embedded Systems hardware labs.", "ece_labs", 0.98),
        "mechanical": ("The Mechanical department includes CNC machines and Thermal Engineering workshops.", "mech_workshops", 0.98),
        "civil engineering": ("The Civil department focuses on Sustainable Construction and Structural Health Monitoring.", "civil_projects", 0.98),
        "canteen": ("🍴 MSPVL Canteen: Open 8:00 AM to 5:00 PM. Serving breakfast, lunch, and snacks.", "canteen_info", 0.98),
        "exam": ("📅 Exams are held in Nov/Dec and April/May. See the 'Examination' tab for your timetable.", "exam_info", 0.98),
        
        "diploma courses": ("We offer Diploma in Civil, Mechanical, EEE, ECE, and Computer Science.", "course_list", 0.98),
        "duration": ("The standard diploma course duration is 3 years (6 semesters).", "duration_info", 0.98),
        "approved": ("Yes, all our courses are AICTE approved and affiliated with the State Board / DOTE.", "approval_info", 0.98),
        "syllabus structure": ("Our syllabus follows a 60/40 structure (60% Practical + 40% Theory).", "syllabus_info", 0.98),
        "eligibility": ("Eligibility: 10th pass for first year, or 12th/ITI pass for Lateral Entry.", "eligibility_info", 0.98),
        "documents": ("Required: 10th/12th Marksheet, TC, Community Certificate, and Aadhar card.", "docs_required", 0.98),
        "merit-based": ("Admission is purely merit-based following government communal reservation rules.", "admission_type", 0.98),
        "wifi": ("Yes, we have high-speed WiFi and modern computer labs/workshops.", "wifi_labs", 0.98),
        "transport": ("Yes, we provide bus facilities covering all major nearby routes.", "transport_bus", 0.98),
        "practical training": ("Yes, we focus heavily on hands-on training and conduct regular Industrial Visits.", "training_focus", 0.98),
        "internship": ("Yes, short-term internships are encouraged for final year projects.", "internship_info", 0.98),
        "lateral entry": ("Yes! After diploma, you can join B.E. directly in the 2nd year.", "lateral_entry", 0.98),
        "uniform": ("Yes, there is a prescribed uniform for all students.", "uniform_rule", 0.98),
        "attendance": ("A minimum of 75% attendance is required to appear for board exams.", "attendance_rule", 0.98),
        "mobile phones": ("Mobile phones are generally not allowed inside classrooms or labs.", "mobile_rule", 0.98)
    }

    for key in fast_responses:
        if key in user_text:
            return fast_responses[key]

    # --- 3. RECOMMENDATION LOGIC ---
    if "best course" in user_text or "recommend" in user_text:
        return "It depends on your interest! If you love coding, choose Computer Science. For machines, Mechanical is best.", "recommendation", 0.90

    # --- 4. EXISTING LOGIC & PERSONAL DATA ---
    response = "I'm the MSPVL Assistant. I didn't quite catch that. Try asking about fees or admissions."
    intent = "unknown"
    confidence = 0.5

# --- restored college name logic ---
    if "college name" in user_text:
        response = "The college name is MSP Velayutha Nadar Lakshmithaiammal Polytechnic College."
        intent = "college_name"
        confidence = 1.0

    elif any(word in user_text for word in ["name", "who am i"]):
        if student_data and student_data.get('full_name'):
            response = f"Your name is {student_data['full_name']}."
        else:
            response = "I don't know your name yet. Please complete your profile."
        intent = "personal_query"
        confidence = 1.0

    elif "roll" in user_text:
        if student_data and student_data.get('roll_number'):
            response = f"Your roll number is {student_data['roll_number']}."
        else:
            response = "I couldn't find a roll number."
        intent = "personal_query"
        confidence = 1.0

    elif "department" in user_text:
        if student_data and student_data.get('course_enrolled'):
            response = f"Your department is {student_data['course_enrolled']}."
        else:
            response = "I couldn't find a department."
        intent = "personal_query"
        confidence = 1.0

    

    # --- FAQ & OTHER LOGIC ---
    elif "library timings" in user_text:
        response = "The library is open from 8:30 AM to 6:30 PM, Monday to Saturday."
        intent = "library_info"
        confidence = 0.9
    elif "contact info" in user_text:
        response = "Email us at info@mspvlcollege.edu.in or call +91 04637-230000."
        intent = "contact_details"
        confidence = 0.9
    elif "college start" in user_text:
        response = "The college starts at 9:00am and ends at 4:55pm."
        intent = "college_start"
        confidence = 0.9
    elif "exam fees" in user_text:
        response = "The Exam fees of the one semester is 💵600"
        intent = "exam_fees"
        confidence = 0.95

    return response, intent, confidence