import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from groq import Groq

def hiring_dashboard(go_to):
    """
    Main function for the Hiring Manager Dashboard.
    Requires go_to_func for logout.
    """
    
    # --- Dashboard Header and Logout Button ---
    col_title, nav_col = st.columns([10, 2])
    
    with col_title:
        st.title("👨‍💼 Hiring Manager Dashboard")
        st.caption("Manage JDs, review top candidates, and track interviews.")
    
    with nav_col:
        # FIX: The logout logic must be placed inside the if st.button(...) block
        # rather than an on_click callback for immediate state changes and rerun() to work reliably.
        if st.button("🚪 Log Out", use_container_width=True):
            # 1. Clear authentication state
            st.session_state.logged_in = False
            st.session_state.user_type = None
            
            # 2. Set the target page using the passed function
            go_to_func("login")
            
            # 3. Force the application to re-run
            st.rerun()
            
    st.markdown("---") # Visual separator after the header/logout



# --- Configuration & Initialization ---
st.set_page_config(layout="wide", page_title="Pragyan-AI Talent Management")

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'chat_step' not in st.session_state:
    st.session_state.chat_step = 0
if 'profile_data' not in st.session_state:
    st.session_state.profile_data = {}
if 'quiz_step' not in st.session_state:
    st.session_state.quiz_step = 0
if 'quiz_responses' not in st.session_state:
    st.session_state.quiz_responses = {}
if 'quiz_candidate' not in st.session_state:
    st.session_state.quiz_candidate = None

# --- Mock Data ---
MOCK_METRICS = {
    "Total Candidates": 1250, "Total JDs": 450, "Total Vendors": 85,
    "No of Applications": 5200, "No of Social Media Posts": 110,
}

MOCK_USERS = [
    {"id": "C-101", "name": "Alice Johnson", "role": "Candidate", "status": "Pending"},
    {"id": "C-102", "name": "Bob Smith", "role": "Candidate", "status": "Approved"},
    {"id": "V-201", "name": "Global Staffing", "role": "Vendor", "status": "Pending"},
    {"id": "V-202", "name": "Tech Recruiters Inc.", "role": "Vendor", "status": "Approved"},
]

MOCK_JDS = [
    {"id": "JD-001", "title": "Senior Python Developer", "skill": "Python, AWS, ML", "type": "Remote"},
    {"id": "JD-002", "title": "Marketing Manager", "skill": "SEO, Content, Analytics", "type": "Onsite"},
    {"id": "JD-003", "title": "Cloud Architect", "skill": "Azure, DevOps, Networking", "type": "Remote"},
]

MOCK_CVS = [
    {"id": "CV-01", "name": "Data Scientist CV", "skills": "Python, ML, Pandas", "status": "Processed"},
    {"id": "CV-02", "name": "Frontend Resume", "skills": "React, JS, CSS", "status": "Pending"},
]

# --- Helper Functions ---

def llm_call(prompt, task):
    """Calls Groq API or falls back to mock if key is missing."""
    api_key = st.session_state.get('api_key')
    
    if not api_key or api_key.strip() == "":
        time.sleep(1)
        if "match" in task.lower():
            return f"**Match Score: {random.randint(50, 95)}%**<br>Key Alignment: Good technical fit."
        return f"Mock response for {task}: Data processed successfully."

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": f"{task}: {prompt}"}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def mock_logout():
    st.session_state.authenticated = False
    st.session_state.role = None
    st.rerun()

def display_dashboard_header(title):
    st.markdown(f"""
        <div style="background-color: #0077B6; padding: 15px; border-radius: 10px; color: white; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2em;">{title}</h1>
            <p style="margin: 0;">User Role: <strong>{st.session_state.role.upper()}</strong></p>
        </div>
    """, unsafe_allow_html=True)

# --- Pages ---

def login_page():
    st.title("🚀 Pragyan-AI")
    col1, _ = st.columns([1, 1])
    with col1:
        st.subheader("Login")
        role = st.selectbox("Select Role", ["Admin", "Candidate", "Hiring Company"])
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Login", type="primary"):
            if user and pwd:
                st.session_state.authenticated = True
                st.session_state.role = role.lower().replace(" ", "_")
                st.rerun()
            else:
                st.error("Invalid Credentials")

def admin_dashboard():
    display_dashboard_header("Admin Control Center")
    with st.sidebar:
        st.button("Logout", on_click=mock_logout)
        st.metric("Total Users", MOCK_METRICS["Total Candidates"])
    
    tabs = st.tabs(["User Approval", "Analytics"])
    with tabs[0]:
        st.dataframe(pd.DataFrame(MOCK_USERS))
        if st.button("Approve All Pending"):
            st.success("All users approved!")

def candidate_dashboard():
    display_dashboard_header("Candidate Portal")
    with st.sidebar:
        st.button("Logout", on_click=mock_logout)

    tabs = st.tabs(["My Resume", "Job Search", "Match Analysis"])
    with tabs[1]:
        st.subheader("Explore Opportunities")
        skill_query = st.text_input("Filter by Skill")
        st.table(MOCK_JDS)
    with tabs[2]:
        jd_sel = st.selectbox("Select JD", [j['id'] for j in MOCK_JDS])
        if st.button("Analyze Match"):
            st.write(llm_call(f"CV vs {jd_sel}", "Matching"))

def hiring_dashboard():
    display_dashboard_header("Employer Dashboard")
    with st.sidebar:
        st.button("Logout", on_click=mock_logout)

    tabs = st.tabs(["Create JD", "Candidate Screening", "Profile Tracking"])
    
    with tabs[0]:
        st.text_area("Paste Job Requirements")
        if st.button("Generate JD"):
            st.write(llm_call("New Role", "Generate JD"))

    with tabs[1]:
        st.subheader("AI Screening Bot")
        step = st.session_state.chat_step
        questions = ["Current Company", "Notice Period", "Expected CTC"]
        if step < len(questions):
            ans = st.text_input(f"Question: {questions[step]}")
            if st.button("Submit Answer"):
                st.session_state.profile_data[questions[step]] = ans
                st.session_state.chat_step += 1
                st.rerun()
        else:
            st.write("Screening Complete!", st.session_state.profile_data)
            if st.button("Reset"):
                st.session_state.chat_step = 0
                st.rerun()

# --- Main Logic ---
def main():
    with st.sidebar:
        st.title("Settings")
        st.text_input("Groq API Key", type="password", key="api_key")
        st.caption("Get your key from [console.groq.com](https://console.groq.com)")

    if not st.session_state.authenticated:
        login_page()
    else:
        if st.session_state.role == "admin": admin_dashboard()
        elif st.session_state.role == "candidate": candidate_dashboard()
        else: hiring_dashboard()

if __name__ == "__main__":
    main()
