import streamlit as st
import os
import json
import re
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from datetime import date

def hiring_dashboard(go_to_func):
    """
    Main function for the Hiring Manager Dashboard.
    Requires go_to_func for logout.
    """
    
    # --- Dashboard Header and Logout Button ---
    col_title, nav_col = st.columns([10, 2])


# -------------------------
# CONFIGURATION & API SETUP
# -------------------------

GROQ_MODEL = "llama-3.1-8b-instant"
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

if not GROQ_API_KEY:
    class MockGroqClient:
        def chat(self):
            class Completions:
                def create(self, **kwargs):
                    raise ValueError("GROQ_API_KEY not set.")
            return Completions()
    client = MockGroqClient()
else:
    client = Groq(api_key=GROQ_API_KEY)

# -------------------------
# UTILITY FUNCTIONS
# -------------------------

def go_to(page_name):
    st.session_state.page = page_name

def hiring_pool_chatbot(question):
    """AI Chatbot to query the approved candidate pool."""
    # Collect all approved/shortlisted candidates' data
    approved_resumes = [
        res['parsed'] for res in st.session_state.resumes_to_analyze 
        if st.session_state.resume_statuses.get(res['name']) in ["Approved", "Shortlisted"]
    ]
    
    if not approved_resumes:
        return "No approved candidates found in the pool yet."

    context = json.dumps(approved_resumes, indent=2)
    prompt = f"""
    You are a Recruitment Assistant. You have access to the following approved candidate data:
    {context}
    
    Based ONLY on this data, answer the following hiring manager question:
    Question: {question}
    """
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error querying candidate pool: {e}"

# -------------------------
# DASHBOARD TABS
# -------------------------

def hiring_dashboard():
    st.title("🏢 Hiring Company Dashboard")
    
    # Navigation Block
    nav_col, _ = st.columns([1, 5])
    with nav_col:
        if st.button("🚪 Log Out", use_container_width=True):
            go_to("login")
            st.rerun()

    st.markdown("---")

    # Initialize hiring-specific state if not exists
    if "company_jds" not in st.session_state:
        st.session_state.company_jds = []

    tab_postings, tab_candidates, tab_chatbot, tab_stats = st.tabs([
        "📝 Job Postings", 
        "👥 Review Candidates", 
        "🤖 Hiring Assistant",
        "📊 Hiring Stats"
    ])

    # --- TAB 1: Job Postings ---
    with tab_postings:
        st.header("Manage Job Postings")
        
        with st.expander("➕ Create New Job Posting"):
            with st.form("hiring_jd_form", clear_on_submit=True):
                role = st.text_input("Job Role Title", placeholder="e.g. Senior Data Scientist")
                jd_text = st.text_area("Full Job Description", height=200)
                job_type = st.selectbox("Job Type", ["Full-time", "Contract", "Remote", "Internship"])
                
                if st.form_submit_button("Publish Posting"):
                    if role and jd_text:
                        new_jd = {
                            "id": len(st.session_state.admin_jd_list) + 1,
                            "name": role,
                            "content": jd_text,
                            "job_type": job_type,
                            "role": role,
                            "key_skills": [] # Metadata can be added via LLM here if needed
                        }
                        # Add to the global Admin JD list so candidates can see it
                        st.session_state.admin_jd_list.append(new_jd)
                        st.success(f"Job Posting for '{role}' is now live!")
                        st.rerun()

        st.markdown("### Active Postings")
        if not st.session_state.admin_jd_list:
            st.info("You haven't posted any jobs yet.")
        else:
            for jd in st.session_state.admin_jd_list:
                with st.container(border=True):
                    st.subheader(jd['name'])
                    st.caption(f"Type: {jd.get('job_type', 'N/A')}")
                    if st.button("View Applications", key=f"view_app_{jd['name']}"):
                        st.session_state.active_review_jd = jd['name']

    # --- TAB 2: Review Candidates ---
    with tab_candidates:
        st.header("Candidate Review Queue")
        
        # Filter pool: Resumes that are Approved/Shortlisted
        review_pool = [
            res for res in st.session_state.resumes_to_analyze 
            if st.session_state.resume_statuses.get(res['name']) in ["Approved", "Shortlisted"]
        ]

        if not review_pool:
            st.warning("No candidates have been approved by the Admin for review yet.")
        else:
            # Dropdown to filter by JD
            available_jds = list(set([res.get('applied_jd', 'Unassigned') for res in review_pool]))
            selected_filter = st.selectbox("Filter by Job Posting", ["All"] + available_jds)

            display_list = []
            for res in review_pool:
                if selected_filter == "All" or res.get('applied_jd') == selected_filter:
                    display_list.append({
                        "Candidate Name": res['name'],
                        "Applied For": res.get('applied_jd', 'N/A'),
                        "Status": st.session_state.resume_statuses.get(res['name']),
                        "Email": res['parsed'].get('email', 'N/A'),
                        "Contact": res['parsed'].get('phone', 'N/A')
                    })
            
            st.table(display_list)
            
            for res in review_pool:
                with st.expander(f"View Full Profile: {res['name']}"):
                    st.json(res['parsed'])

    # --- TAB 3: Hiring Chatbot ---
    with tab_chatbot:
        st.header("Recruitment AI Assistant")
        st.markdown("Ask questions about your approved candidate pool.")
        
        user_query = st.text_input("Query Pool", placeholder="e.g., 'Which candidates have more than 5 years of Python experience?'")
        
        if st.button("Search Pool"):
            if user_query:
                with st.spinner("Analyzing approved candidates..."):
                    answer = hiring_pool_chatbot(user_query)
                    st.markdown("### AI Analysis:")
                    st.write(answer)
            else:
                st.error("Please enter a search query.")

    # --- TAB 4: Hiring Stats ---
    with tab_stats:
        st.header("Hiring Overview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Active Postings", len(st.session_state.admin_jd_list))
        with col2:
            approved_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Approved")
            st.metric("Approved Candidates", approved_count)
        with col3:
            shortlisted_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Shortlisted")
            st.metric("Shortlisted", shortlisted_count)

# -------------------------
# MAIN EXECUTION
# -------------------------
if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="Hiring Company Dashboard")

    # Shared Session States (Should be consistent across all dashboards)
    if 'page' not in st.session_state: st.session_state.page = "hiring_dashboard"
    if 'admin_jd_list' not in st.session_state: st.session_state.admin_jd_list = []
    if 'resumes_to_analyze' not in st.session_state: st.session_state.resumes_to_analyze = []
    if 'resume_statuses' not in st.session_state: st.session_state.resume_statuses = {}

    hiring_dashboard()
    
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
