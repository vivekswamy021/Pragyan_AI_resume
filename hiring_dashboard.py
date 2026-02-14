import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from groq import Groq

# --- Configuration & Initialization ---
# This MUST be the first Streamlit command
st.set_page_config(layout="wide", page_title="Pragyan-AI Talent Management System")

# Initialize session state for authentication and data persistence
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

# Mock Data Persistence
if 'mock_users' not in st.session_state:
    st.session_state.mock_users = [
        {"id": "C-101", "name": "Alice Johnson", "role": "Candidate", "status": "Pending"},
        {"id": "C-102", "name": "Bob Smith", "role": "Candidate", "status": "Approved"},
        {"id": "V-201", "name": "Global Staffing", "role": "Vendor", "status": "Pending"},
        {"id": "V-202", "name": "Tech Recruiters Inc.", "role": "Vendor", "status": "Approved"},
    ]

if 'mock_cvs' not in st.session_state:
    st.session_state.mock_cvs = [
        {"id": "CV-01", "name": "Data Scientist CV", "skills": "Python, ML, Pandas", "status": "Processed"},
        {"id": "CV-02", "name": "Frontend Resume", "skills": "React, JS, CSS", "status": "Pending"},
    ]

# --- Global Mock Data ---
MOCK_METRICS = {
    "Total Candidates": 1250,
    "Total JDs": 450,
    "Total Vendors": 85,
    "No of Applications": 5200,
}

MOCK_JDS = [
    {"id": "JD-001", "title": "Senior Python Developer", "skill": "Python, AWS, ML", "type": "Remote"},
    {"id": "JD-002", "title": "Marketing Manager", "skill": "SEO, Content, Analytics", "type": "Onsite"},
]

# --- Core Logic Functions ---

def logout():
    """Clears session and reruns the app to show login page."""
    st.session_state.authenticated = False
    st.session_state.role = None
    st.rerun()

def llm_call(prompt, task):
    """Interacts with Groq API or returns mock analysis."""
    if not st.session_state.get('api_key'):
        time.sleep(1)
        return f"**Mock Analysis for {task}:** High alignment detected for {prompt[:30]}..."
    
    try:
        client = Groq(api_key=st.session_state.api_key)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": f"Task: {task}. Prompt: {prompt}"}],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API Error: {str(e)}"

def display_dashboard_header(title):
    st.markdown(f"""
        <div style="background-color: #0077B6; padding: 15px; border-radius: 10px; color: white; margin-bottom: 20px;">
            <h1 style="margin: 0; font-size: 2em;">{title}</h1>
            <p style="margin: 0;">User: <strong>{st.session_state.role.replace('_',' ').title()}</strong></p>
        </div>
    """, unsafe_allow_html=True)

# --- Pages / Dashboards ---

def login_page():
    col1, _, _ = st.columns([2, 1, 1])
    with col1:
        st.title("Pragyan-AI Login")
        role = st.selectbox("Role", ["Admin", "Candidate", "Hiring Company"])
        user = st.text_input("Username")
        pwd = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True, type="primary"):
            if user and pwd:
                st.session_state.authenticated = True
                st.session_state.role = role.lower().replace(" ", "_")
                st.rerun()
        
        if st.button("Need an account? Sign Up"):
            st.session_state.show_signup = True
            st.rerun()

def signup_page():
    col1, _, _ = st.columns([2, 1, 1])
    with col1:
        st.title("Create Account")
        st.text_input("Full Name")
        st.text_input("Email")
        st.selectbox("Desired Role", ["Admin", "Candidate", "Hiring Company"])
        if st.button("Register", type="primary"):
            st.success("Account created! Please log in.")
            st.session_state.show_signup = False
            st.rerun()
        if st.button("Back to Login"):
            st.session_state.show_signup = False
            st.rerun()

# --- Dashboard Definitions ---

def admin_dashboard():
    display_dashboard_header("Admin Control Center")
    with st.sidebar:
        st.button("Logout", on_click=logout)
        st.metric("Total Applications", MOCK_METRICS["No of Applications"])

    tab1, tab2 = st.tabs(["User Management", "System Logs"])
    with tab1:
        st.subheader("Pending Approvals")
        for i, user in enumerate(st.session_state.mock_users):
            if user["status"] == "Pending":
                c1, c2 = st.columns([3, 1])
                c1.write(f"{user['name']} - {user['role']}")
                if c2.button("Approve", key=f"adm_app_{i}"):
                    st.session_state.mock_users[i]["status"] = "Approved"
                    st.rerun()

def candidate_dashboard():
    display_dashboard_header("Candidate Portal")
    with st.sidebar:
        st.button("Logout", on_click=logout)

    t1, t2, t3 = st.tabs(["My Resume", "Job Matching", "Skill Roadmap"])
    with t1:
        st.file_uploader("Upload New CV", type=['pdf', 'docx'])
        st.dataframe(st.session_state.mock_cvs)
    with t2:
        jd_sel = st.selectbox("Select JD", [j['title'] for j in MOCK_JDS])
        if st.button("Analyze Match"):
            st.write(llm_call(jd_sel, "Candidate Matching"))

def hiring_company_dashboard():
    display_dashboard_header("Hiring Manager Dashboard")
    with st.sidebar:
        st.button("Logout", on_click=logout)

    t1, t2, t3 = st.tabs(["Post JD", "Screen Candidates", "Interviews"])
    with t1:
        st.text_input("Job Title")
        st.text_area("Job Description")
        if st.button("Post Job"):
            st.success("Job posted successfully!")
    with t2:
        st.write("Ranked Candidates")
        st.table(st.session_state.mock_cvs)

# --- Main App Execution ---

def main():
    # Sidebar API Settings
    with st.sidebar:
        st.title("⚙️ Settings")
        key = st.text_input("Groq API Key", type="password", value=st.session_state.api_key)
        if key:
            st.session_state.api_key = key

    # Routing Logic
    if not st.session_state.authenticated:
        if st.session_state.show_signup:
            signup_page()
        else:
            login_page()
    else:
        role = st.session_state.role
        if role == "admin":
            admin_dashboard()
        elif role == "candidate":
            candidate_dashboard()
        elif role == "hiring_company":
            hiring_company_dashboard()

if __name__ == "__main__":
    main()
