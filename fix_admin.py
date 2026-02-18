from app import get_db_connection, generate_password_hash

def fix_parent_account():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 1. Generate the correct hash for the password 'parent123'
    # This ensures the algorithm matches what your app.py expects
    hashed_pw = generate_password_hash("parent123")
    
    # 2. Update the user table
    # We use 'visitor' or 'parent' as the role to match your login dropdown
    email = "parent@gmail.com"
    try:
        cur.execute("UPDATE user SET password=%s, role='visitor' WHERE email=%s", (hashed_pw, email))
        conn.commit()
        
        if cur.rowcount > 0:
            print(f"Success! Account {email} updated with password: parent123")
        else:
            print(f"Error: No user found with email {email}. Please create the user first.")
            
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_parent_account()