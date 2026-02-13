import streamlit as st
import pandas as pd
import numpy as np
import time
import base64
import random
from groq import Groq

def hiring_dashboard():
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
st.set_page_config(
    layout="wide", 
    page_title="Pragyan-AI | Talent Management System",
    page_icon="🎯"
)

# --- Session State Management ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# --- Mock Data ---
MOCK_METRICS = {
    "Total Candidates": 1250,
    "Total JDs": 450,
    "Total Vendors": 85,
    "No of Applications": 5200,
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
    """Calls Groq API or falls back to Mock responses."""
    if not st.session_state.api_key:
        time.sleep(0.5)
        return f"**[MOCK MODE]** Analysis for {task}: Based on the data, the candidate shows high proficiency in {prompt[:30]}..."

    try:
        client = Groq(api_key=st.session_state.api_key)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": f"Task: {task}. Context: {prompt}"}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

def display_dashboard_header(title):
    st.markdown(f"""
        <div style="background-color: #0077B6; padding: 20px; border-radius: 10px; color: white; margin-bottom: 25px;">
            <h1 style="margin: 0;">{title}</h1>
            <p style="margin: 0; opacity: 0.8;">Portal Access: {st.session_state.role.replace('_', ' ').upper()}</p>
        </div>
    """, unsafe_allow_html=True)

def logout():
    st.session_state.authenticated = False
    st.session_state.role = None
    st.rerun()

# --- UI Components ---

def login_page():
    st.title("🚀 Pragyan-AI")
    st.subheader("Next-Gen Talent Acquisition")
    
    col1, _ = st.columns([1, 1])
    with col1:
        with st.form("login_form"):
            role = st.selectbox("I am a...", ["Candidate", "Hiring Company", "Admin"])
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if user and pw:
                    st.session_state.authenticated = True
                    st.session_state.role = role.lower().replace(" ", "_")
                    st.rerun()
                else:
                    st.error("Please enter credentials.")

# --- Dashboards ---

def admin_dashboard():
    display_dashboard_header("Administrator Control Center")
    with st.sidebar:
        st.button("Sign Out", on_click=logout)
        st.info("System Health: Operational")
        
    t1, t2, t3 = st.tabs(["User Approvals", "System Analytics", "Configuration"])
    with t1:
        st.dataframe(pd.DataFrame(MOCK_USERS), use_container_width=True)
    with t2:
        c1, c2 = st.columns(2)
        c1.metric("Database Load", "24%", "-2%")
        c2.metric("Active Sessions", "142", "+12")

def candidate_dashboard():
    display_dashboard_header("Candidate Career Portal")
    with st.sidebar:
        st.button("Sign Out", on_click=logout)
        st.session_state.api_key = st.text_input("Enter Groq API Key", type="password")
        
    t1, t2, t3 = st.tabs(["My Resume", "Job Search", "AI Interview Prep"])
    with t1:
        st.file_uploader("Upload New Resume Version", type=['pdf', 'docx'])
        st.info("Current Active Resume: `Alice_Johnson_CV_2026.pdf`")
    with t2:
        st.table(MOCK_JDS)
        if st.button("AI Matching Score"):
            st.write(llm_call("Python, AWS vs JD-001", "Match Analysis"))

def hiring_dashboard():
    display_dashboard_header("Recruiter Workspace")
    with st.sidebar:
        st.button("Sign Out", on_click=logout)
        
    t1, t2, t3 = st.tabs(["Post Job", "Applicant Tracking", "AI Screening"])
    with t1:
        st.text_input("Job Title")
        st.text_area("Job Description")
        st.button("Post & Index with AI")
    with t2:
        st.write("Recent Applicants:")
        st.dataframe(pd.DataFrame(MOCK_CVS))

# --- Main Entry ---

def main():
    if not st.session_state.authenticated:
        login_page()
    else:
        if st.session_state.role == "admin":
            admin_dashboard()
        elif st.session_state.role == "candidate":
            candidate_dashboard()
        else:
            hiring_dashboard()

if __name__ == "__main__":
    main()
