import streamlit as st
import pandas as pd
import numpy as np
import time
import random
from groq import Groq

# --- Configuration & Initialization ---
st.set_page_config(layout="wide", page_title="Pragyan-AI Talent Management")

# 1. Unified Session State Initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'show_signup' not in st.session_state:
    st.session_state.show_signup = False

# 2. Data Persistence (Storing Mock Data in Session State)
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

# --- Global Constants ---
MOCK_METRICS = {
    "Total Candidates": 1250,
    "Total JDs": 450,
    "Total Vendors": 85,
    "No of Applications": 5200,
    "No of Social Media Posts": 110,
}

MOCK_JDS = [
    {"id": "JD-001", "title": "Senior Python Developer", "skill": "Python, AWS, ML", "type": "Remote"},
    {"id": "JD-002", "title": "Marketing Manager", "skill": "SEO, Content, Analytics", "type": "Onsite"},
    {"id": "JD-003", "title": "Cloud Architect", "skill": "Azure, DevOps, Networking", "type": "Remote"},
]

# --- Helper Functions ---

def logout():
    """Universal logout function to clear state and refresh."""
    st.session_state.authenticated = False
    st.session_state.role = None
    st.session_state.chat_step = 0
    st.session_state.quiz_step = 0
    st.rerun()

def llm_call(prompt, task):
    """Calls Groq LLM API or falls back to mock responses."""
    if not st.session_state.get('api_key'):
        time.sleep(1)
        if "match" in task.lower():
            score = random.randint(50, 95)
            return f"**Match Score: {score}%** (Rank: #{random.randint(1, 10)})<br>Key Alignment: {prompt[:40]}...<br>Suggested Next Steps: Interview focusing on edge cases."
        elif "gap" in task.lower():
            return "**GAP Analysis (SWOT)**\n\n**Weakness:** Missing hands-on experience in Kubernetes.\n**Opportunity:** Excellent foundation in Python and AWS.\n**Suggestion:** Focus on containerization training (Docker/Kubernetes). "
        else:
            return f"LLM Content for '{task}': {prompt}"

    try:
        client = Groq(api_key=st.session_state.api_key)
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": f"{task}: {prompt}"}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {str(e)}. Using mock data."

def display_dashboard_header(title):
    """Displays the main dashboard title and role context."""
    st.markdown(f"""
        <div style="background-color: #0077B6; padding: 15px; border-radius: 10px; color: white;">
            <h1 style="margin: 0; font-size: 2em;">{title}</h1>
            <p style="margin: 0;">Logged in as: <strong>{st.session_state.role.replace('_',' ').capitalize()}</strong></p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")

# --- Authentication Pages ---

def login_signup_page():
    st.title("Pragyan-AI")
    st.markdown("---")
    if st.session_state.show_signup:
        signup_page()
    else:
        login_page()

def login_page():
    col1, _, _ = st.columns([2, 1, 1])
    roles = ["Admin", "Candidate", "Hiring Company"]
    with col1:
        st.header("Login")
        selected_role = st.selectbox("Select Role", roles, index=None, placeholder="Choose Role...")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Log In", use_container_width=True, type="primary"):
            if selected_role and username and password:
                st.session_state.authenticated = True
                st.session_state.role = selected_role.lower().replace(" ", "_")
                st.rerun()
            else:
                st.error("Please fill all fields.")

        if st.button("Don't have an account? Sign Up", use_container_width=True):
            st.session_state.show_signup = True
            st.rerun()

def signup_page():
    col1, _, _ = st.columns([2, 1, 1])
    roles = ["Admin", "Candidate", "Hiring Company"]
    with col1:
        st.header("Sign Up")
        st.text_input("Full Name")
        st.text_input("Email Address")
        st.selectbox("Select Role", roles, index=None, key="signup_role")
        st.text_input("Username", key="signup_user")
        st.text_input("Password", type="password", key="signup_pass")
        if st.button("Register", use_container_width=True, type="primary"):
            st.success("Account created! Please log in.")
            st.session_state.show_signup = False
            st.rerun()
        if st.button("Back to Login", use_container_width=True):
            st.session_state.show_signup = False
            st.rerun()

# --- Admin Dashboard ---

def admin_dashboard():
    display_dashboard_header("Admin Dashboard")
    with st.sidebar:
        st.button("Logout", on_click=logout, type="secondary")
        st.markdown("---")
        st.metric("Total Users", MOCK_METRICS["Total Candidates"])
        st.metric("Active Jobs", MOCK_METRICS["Total JDs"])

    tab1, tab2, tab3, tab4 = st.tabs(["👥 User Management", "📂 Resumes", "📄 JDs", "📈 Analytics"])

    with tab1:
        st.subheader("User Approval")
        users = st.session_state.mock_users
        for i, user in enumerate(users):
            if user["status"] == "Pending":
                col_u, col_b = st.columns([3, 1])
                col_u.write(f"**{user['name']}** ({user['role']})")
                if col_b.button("Approve", key=f"app_{i}"):
                    st.session_state.mock_users[i]["status"] = "Approved"
                    st.rerun()

    with tab2:
        st.subheader("Bulk Resume Upload")
        st.file_uploader("Upload ZIP", type=['zip'])
        st.dataframe(pd.DataFrame(st.session_state.mock_cvs), use_container_width=True)

    with tab3:
        st.subheader("JD Management")
        st.text_input("Enter JD URL")
        st.dataframe(pd.DataFrame(MOCK_JDS), use_container_width=True)

    with tab4:
        st.subheader("Growth Trends")
        st.line_chart(np.random.randn(10, 2))

# --- Candidate Dashboard ---

def candidate_dashboard():
    display_dashboard_header("Candidate Dashboard")
    st.sidebar.button("Logout", on_click=logout, type="secondary")

    tab1, tab2, tab3, tab4 = st.tabs(["📂 My CV", "🔍 Jobs", "🎯 Match Analysis", "💡 Skill Gap"])

    with tab1:
        st.file_uploader("Upload CV (PDF/DOCX)")
        st.code("# John Doe\nPython Developer\nSkills: AWS, ML, Django", language="markdown")

    with tab2:
        skill_q = st.text_input("Search by Skill")
        if st.button("Search"):
            st.table(MOCK_JDS)

    with tab3:
        sel_jd = st.selectbox("Select JD", [jd['id'] for jd in MOCK_JDS])
        if st.button("Run Match"):
            st.write(llm_call(f"CV vs {sel_jd}", "Match Analysis"))

    with tab4:
        if st.button("Generate Roadmap"):
            st.info("Roadmap: 1. Docker Certification 2. Advanced Kubernetes 3. Groq API Integration")

# --- Hiring Company Dashboard ---

def hiring_company_dashboard():
    display_dashboard_header("Hiring Company Dashboard")
    st.sidebar.button("Logout", on_click=logout, type="secondary")

    tab1, tab2, tab3, tab4 = st.tabs(["📝 Create JD", "📂 Explore CVs", "🎯 Match & Rank", "📊 Tracking"])

    with tab1:
        st.text_input("Job Title")
        st.text_area("Responsibilities")
        if st.button("Generate AI JD"):
            st.write(llm_call("Senior Python Dev", "JD Generation"))

    with tab2:
        st.dataframe(pd.DataFrame(st.session_state.mock_cvs), use_container_width=True)

    with tab3:
        st.selectbox("Select JD", [jd['title'] for jd in MOCK_JDS])
        if st.button("Match Candidates"):
            st.success("Top match: Alice Johnson (92%)")

    with tab4:
        st.subheader("Hiring Pipeline")
        st.bar_chart({"Applied": 50, "Screening": 20, "Interview": 5, "Offered": 2})

# --- Main Routing ---

def main():
    with st.sidebar:
        st.title("Settings")
        st.text_input("Groq API Key", type="password", key="api_key_input")
        if st.session_state.api_key_input:
            st.session_state.api_key = st.session_state.api_key_input

    if not st.session_state.authenticated:
        login_signup_page()
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
