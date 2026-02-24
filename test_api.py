import google.generativeai as genai

# 1. Use your key
genai.configure(api_key="AIzaSyAeTokpZ-wv1sGlcRp9DeQMUX_xwJZOEWY")

try:
    # 2. Try a simple model
    model = genai.GenerativeModel('gemini-1.5-flash')
    print("Connecting to Google Servers...")
    
    # 3. Ask a basic question
    response = model.generate_content("Hello, are you active?")
    
    print("-" * 30)
    print("SUCCESS! Gemini says:")
    print(response.text)
    print("-" * 30)

except Exception as e:
    print("-" * 30)
    print("FAILED! Here is why:")
    print(str(e))
    print("-" * 30)