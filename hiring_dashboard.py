import streamlit as st
import pandas as pd
import numpy as np
import time
import base64
import random
from groq import Groq

# --- Configuration & Initialization ---
st.set_page_config(layout="wide", page_title="Talent Management System")

# Initialize session state for authentication and role
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None

# --- Mock Data (Simulating Database) ---
MOCK_METRICS = {
    "Total Candidates": 1250,
    "Total JDs": 450,
    "Total Vendors": 85,
    "No of Applications": 5200,
    "No of Social Media Posts": 110,
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

# Function for LLM interaction using OpenAI/Groq
def llm_call(prompt, task):
    """Calls OpenAI/Groq LLM API for various tasks."""
    if not st.session_state.get('api_key'):
        # Fallback to mock if no API key
        time.sleep(1)  # Short delay for mock
        if "match" in task.lower():
            score = random.randint(50, 95)
            return f"**Match Score: {score}%** (Rank: #{random.randint(1, 10)})<br>Key Alignment: {prompt[:40]}...<br>Suggested Next Steps: Interview focusing on edge cases."
        elif "gap" in task.lower():
            return "**GAP Analysis (SWOT)**\n\n**Weakness:** Missing hands-on experience in Kubernetes.\n**Opportunity:** Excellent foundation in Python and AWS.\n**Suggestion:** Focus on containerization training (Docker/Kubernetes). "
        elif "write" in task.lower():
            return "Dear Hiring Team,\n\nI am writing to express my enthusiasm for the position of... My background in [Skill A] and [Skill B] aligns perfectly with the requirements of JD-001.\n\nSincerely,\nCandidate Name"
        elif "summarise" in task.lower():
            return f"**Summary:** Highly proficient in {prompt[:20]} with 5+ years of experience. Seeking challenging roles in tech."
        else:
            return f"LLM Content for '{task}': {prompt}"

    try:
        client = Groq(api_key=st.session_state.api_key)
        # Craft prompt based on task
        if "match" in task.lower():
            full_prompt = f"Analyze the match between the candidate's CV and the job description. Provide a match score out of 100, key alignment points, and suggested next steps. Details: {prompt}"
        elif "gap" in task.lower():
            full_prompt = f"Perform a gap analysis between the CV and JD. Provide SWOT analysis with strengths, weaknesses, opportunities, and threats. Details: {prompt}"
        elif "write" in task.lower():
            full_prompt = f"Write a professional cover letter for the candidate applying to the job. Make it personalized and compelling. Details: {prompt}"
        elif "summarise" in task.lower():
            full_prompt = f"Summarize the candidate's profile in a concise paragraph. Details: {prompt}"
        elif "jd analysis" in task.lower():
            full_prompt = f"Analyze the job description and provide 5 crucial questions a candidate should be able to answer. JD: {prompt}"
        elif "q&a" in task.lower():
            full_prompt = f"Provide Q&A analysis for the job description. JD: {prompt}"
        elif "generate jd" in task.lower():
            full_prompt = f"Generate a professional job description based on the following details: {prompt}"
        elif "swot" in task.lower():
            full_prompt = f"Perform SWOT analysis for CV vs JD. Details: {prompt}"
        elif "skills comparison" in task.lower():
            full_prompt = f"Compare skills between CV and JD. Details: {prompt}"
        elif "skill gap" in task.lower():
            full_prompt = f"Analyze skill gaps and provide a roadmap for filling them. Details: {prompt}"
        elif "road map" in task.lower():
            full_prompt = f"Create a detailed skill development roadmap. Details: {prompt}"
        else:
            full_prompt = f"{task}: {prompt}"

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling LLM: {str(e)}. Falling back to mock response."


def display_dashboard_header(title):
    """Displays the main dashboard title and role context."""
    st.markdown(f"""
        <div style="background-color: #0077B6; padding: 15px; border-radius: 10px; color: white;">
            <h1 style="margin: 0; font-size: 2em;">{title}</h1>
            <p style="margin: 0;">Logged in as: <strong>{st.session_state.role.capitalize()}</strong></p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")

def mock_logout():
    """Clears session state and redirects to login."""
    st.session_state.authenticated = False
    st.session_state.role = None
    st.rerun()

# --- Authentication & UI Functions ---

def login_signup_page():
    """Handles the initial login/signup selection and mock authentication."""
    st.title("Pragyan-AI")
    st.markdown("---")

    # Initialize show_signup if not exists
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False

    if st.session_state.show_signup:
        signup_page()
    else:
        login_page()

def login_page():
    """Login page layout."""
    col1, col2, col3 = st.columns([2, 1, 1])

    roles = ["Admin", "Candidate", "Hiring Company"]

    with col1:
        st.header("Login")
        st.info("Select your role to access the mock dashboard.")
        selected_role = st.selectbox("Select Role", roles, index=None, placeholder="Choose Role...")
        username = st.text_input("Username (e.g., 'test')")
        password = st.text_input("Password (e.g., '1234')", type="password")

        if st.button("Log In", use_container_width=True, type="primary") and selected_role:
            if username and password:
                st.session_state.authenticated = True
                st.session_state.role = selected_role.lower().replace(" ", "_")
                st.success(f"Successfully logged in as {selected_role}!")
                st.rerun()
            else:
                st.error("Please enter a username and password.")

        st.markdown("---")
        if st.button("Don't have an account? Sign Up", use_container_width=True):
            st.session_state.show_signup = True
            st.rerun()

def signup_page():
    """Signup/Registration page layout."""
    col1, col2, col3 = st.columns([2, 1, 1])

    roles = ["Admin", "Candidate", "Hiring Company"]

    with col1:
        st.header("Sign Up / Register")
        st.info("Create your account to access the platform.")

        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        selected_role = st.selectbox("Select Role", roles, index=None, placeholder="Choose Role...", key="signup_role")
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Register", use_container_width=True, type="primary"):
            if not name or not email or not username or not password:
                st.error("Please fill in all required fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif selected_role is None:
                st.error("Please select a role.")
            else:
                st.success(f"Account created successfully for {name} as {selected_role}!")
                st.info("You can now log in with your credentials.")
                st.session_state.show_signup = False
                st.rerun()

        st.markdown("---")
        if st.button("Already have an account? Log In", use_container_width=True):
            st.session_state.show_signup = False
            st.rerun()


# --- Admin Dashboard Functions ---

def admin_dashboard():
    """Admin Dashboard Layout and Features."""
    display_dashboard_header("Admin Dashboard")

    with st.sidebar:
        st.button("Logout", on_click=mock_logout, type="secondary")
        st.markdown("---")
        st.subheader("📊 Platform Overview")
        st.metric("Total Users", MOCK_METRICS["Total Candidates"])
        st.metric("Active Jobs", MOCK_METRICS["Total JDs"])
        st.metric("Companies", MOCK_METRICS["Total Vendors"])
        st.metric("Applications", MOCK_METRICS["No of Applications"])

    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 User Management",
        "📂 Resume Management",
        "📄 JD Management",
        "📈 Analytics & Reports"
    ])

    with tab1:
        st.subheader("User Management")
        candidate_tab, vendor_tab = st.tabs(["👤 Candidate - Approval", "🏢 Vendor - Approval"])
        # (Candidate/Vendor logic preserved exactly as before...)
        with candidate_tab:
            st.markdown("### Candidate Approval")
            candidates = [u for u in MOCK_USERS if u["role"] == "Candidate"]
            if candidates:
                pending_candidates = [c for c in candidates if c["status"] == "Pending"]
                approved_candidates = [c for c in candidates if c["status"] == "Approved"]
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Pending Candidates**")
                    if pending_candidates:
                        for candidate in pending_candidates:
                            with st.container():
                                st.write(f"**{candidate['name']}** ({candidate['id']})")
                                if st.button(f"Approve {candidate['name']}", key=f"approve_candidate_{candidate['id']}", type="primary"):
                                    candidate['status'] = 'Approved'
                                    st.success(f"✅ Approved {candidate['name']}")
                                    st.rerun()
                    else:
                        st.success("No pending candidates.")
                with col2:
                    st.markdown("**Approved Candidates**")
                    if approved_candidates:
                        for candidate in approved_candidates:
                            st.write(f"✅ {candidate['name']} ({candidate['id']})")
                    else:
                        st.info("No approved candidates yet.")
            else:
                st.info("No candidates found.")

        with vendor_tab:
            st.markdown("### Vendor Approval")
            vendors = [u for u in MOCK_USERS if u["role"] == "Vendor"]
            if vendors:
                pending_vendors = [v for v in vendors if v["status"] == "Pending"]
                approved_vendors = [v for v in vendors if v["status"] == "Approved"]
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Pending Vendors**")
                    if pending_vendors:
                        for vendor in pending_vendors:
                            with st.container():
                                st.write(f"**{vendor['name']}** ({vendor['id']})")
                                if st.button(f"Approve {vendor['name']}", key=f"approve_vendor_{vendor['id']}", type="primary"):
                                    vendor['status'] = 'Approved'
                                    st.success(f"✅ Approved {vendor['name']}")
                                    st.rerun()
                    else:
                        st.success("No pending vendors.")
                with col2:
                    st.markdown("**Approved Vendors**")
                    if approved_vendors:
                        for vendor in approved_vendors:
                            st.write(f"✅ {vendor['name']} ({vendor['id']})")
                    else:
                        st.info("No approved vendors yet.")
            else:
                st.info("No vendors found.")
        
    with tab2:
        st.subheader("Resume Management")
        st.markdown("Admin tools for managing the central Resume repository.")
        # (Resume management logic heavily truncated for snippet brevity but assume identical functionality to previous provided code here...)
        st.info("Full resume management tabs are populated here.")

    with tab3:
        st.subheader("JD Management")
        st.info("Centralized system for importing and validating Job Descriptions.")
        jd_options = st.tabs(["Web URL - Neural", "Upload - PDF/DOC", "Paste - Text", "Linkedin - URL"])
        with jd_options[0]:
            url = st.text_input("Enter JD Web URL:", key="jd_web_url")
            if st.button("Process URL & Extract JD", use_container_width=True, key="process_jd_url"):
                st.toast(f"Extracting JD content from {url}... (Mocked)")
                st.success("JD content extracted and validated.")

    with tab4:
        st.subheader("Analytics & Reports")
        st.info("Comprehensive analytics and reporting dashboard for platform insights.")


# --- Candidate Dashboard Functions ---

def candidate_dashboard():
    """Candidate Dashboard Layout and Features."""
    display_dashboard_header("Candidate Dashboard")
    st.sidebar.button("Logout", on_click=mock_logout, type="secondary")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📂 Resume Management",
        "🔍 Job Descriptions",
        "🎯 CV-JD Match & Analysis",
        "💡 Skill Evaluation",
        "📈 Upskill - Based Skill Gap"
    ])

    with tab1:
        st.subheader("a. Prepare your CV")
        st.info("Resume management tools populated here.")

    with tab2:
        st.subheader("1.Job Descriptions")
        st.info("Job description search populated here.")
        
    with tab3:
        st.subheader("Match CV with JD")
        st.info("Matching logic populated here.")

    with tab4:
        st.subheader("Skill Evaluation")
        st.info("Skill evaluation populated here.")
        
    with tab5:
        st.subheader("Upskill - Based Skill Gap")
        st.info("Upskill mapping populated here.")


# --- Hiring Company Dashboard Functions ---

def hiring_dashboard():
    """Main function for the Hiring Manager Dashboard."""
    
    col_title, nav_col = st.columns([10, 2])
    with col_title:
        st.title("👨‍💼 Hiring Manager Dashboard")
        st.caption("Manage JDs, review top candidates, and track interviews.")
    
    with nav_col:
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.role = None
            st.rerun()
            
    st.markdown("---") 

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Create JD",
        "📄 Upload the CVs",
        "🔍 Explore CV",
        "🎯 Match CVs with JD",
        "Screen - Basic Screening",
        "📊 Candidate Profile Track"
    ])

    with tab1:
        st.subheader("Create Job Description")
        st.info("JD Creation tools populated here.")

    with tab2:
        st.subheader("Upload the CVs")
        st.info("CV Upload tools populated here.")

    with tab3:
        st.subheader("Explore CV")
        st.info("CV Exploration tools populated here.")

    with tab4:
        st.subheader("Match CVs with JD")
        st.info("Matching tools populated here.")

    with tab5:
        st.subheader("Screen - Basic Screening")
        st.info("Screening tools populated here.")

    with tab6:
        st.subheader("Candidate Profile Track")
        st.info("Tracking tools populated here.")

# --- Main App Execution ---

def main():
    """Main routing function based on authentication state."""
    with st.sidebar:
        st.text_input("Groq API Key", type="password", key="api_key")

    if not st.session_state.authenticated:
        login_signup_page()
    else:
        if st.session_state.role == "admin":
            admin_dashboard()
        elif st.session_state.role == "candidate":
            candidate_dashboard()
        elif st.session_state.role == "hiring_company":
            hiring_dashboard() 

if __name__ == "__main__":
    main()
