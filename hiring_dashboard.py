import streamlit as st
import os
import json
import re
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from datetime import date

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
# MAIN DASHBOARD FUNCTION
# -------------------------

def hiring_dashboard(go_to_func):
    """
    Main function for the Hiring Manager Dashboard.
    Requires go_to_func for logout and navigation.
    """
    
    # --- Dashboard Header and Logout Button ---
    col_title, nav_col = st.columns([10, 2])
    
    with col_title:
        st.title("🏢 Hiring Company Dashboard")
        st.caption("Manage your job vacancies and track hiring metrics.")

    with nav_col:
        # Logout logic handles state clearing and redirect
        if st.button("🚪 Log Out", use_container_width=True, key="hiring_logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            go_to_func("login")
            st.rerun()
    
    st.markdown("---")

    # --- Safety Initialization of Shared Session States ---
    if 'admin_jd_list' not in st.session_state: 
        st.session_state.admin_jd_list = []
    if 'resume_statuses' not in st.session_state: 
        st.session_state.resume_statuses = {}

    # --- Dashboard Tabs (Remaining 2 Tabs) ---
    tab_postings, tab_stats = st.tabs([
        "📝 My Job Postings", 
        "📊 Hiring Analytics"
    ])

    # --- TAB 1: Job Postings ---
    with tab_postings:
        st.header("Manage Vacancies")
        
        # Form to add new JDs
        with st.expander("➕ Create New Job Posting"):
            with st.form("hiring_jd_form", clear_on_submit=True):
                role_title = st.text_input("Job Role Title", placeholder="e.g. Senior Data Scientist")
                jd_text = st.text_area("Full Job Description", height=200)
                job_type = st.selectbox("Employment Type", ["Full-time", "Contract", "Remote", "Internship", "Part-time"])
                
                if st.form_submit_button("Publish Posting"):
                    if role_title and jd_text:
                        new_jd = {
                            "name": role_title,
                            "content": jd_text,
                            "job_type": job_type,
                            "role": role_title,
                            "key_skills": [], 
                            "date_posted": date.today().strftime("%Y-%m-%d")
                        }
                        # Add to shared list so candidates can see it
                        st.session_state.admin_jd_list.append(new_jd)
                        st.success(f"Job Posting for '{role_title}' is now live!")
                        st.rerun()
                    else:
                        st.error("Please provide both a Role Title and Job Description.")

        st.markdown("### Active Postings")
        if not st.session_state.admin_jd_list:
            st.info("You haven't posted any jobs yet.")
        else:
            # Display current JDs with a delete option
            for i, jd in enumerate(st.session_state.admin_jd_list):
                with st.container(border=True):
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.subheader(f"{jd['name']}")
                        st.caption(f"Type: {jd.get('job_type', 'N/A')} | Posted: {jd.get('date_posted', 'N/A')}")
                        with st.expander("View Description"):
                            st.write(jd['content'])
                    with col_b:
                        if st.button("🗑️ Delete", key=f"del_jd_{i}"):
                            st.session_state.admin_jd_list.pop(i)
                            st.rerun()

    # --- TAB 2: Hiring Stats ---
    with tab_stats:
        st.header("Hiring Metrics Overview")
        
        # Calculate totals from session state
        total_postings = len(st.session_state.admin_jd_list)
        approved_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Approved")
        shortlisted_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Shortlisted")
        rejected_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Rejected")

        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Live Vacancies", total_postings)
        with col2:
            st.metric("Approved Talent", approved_count)
        with col3:
            st.metric("Shortlisted", shortlisted_count)
        with col4:
            st.metric("Rejected", rejected_count)
            
        st.markdown("---")
        st.subheader("Application Funnel")
        
        # Simple data representation for the funnel
        funnel_data = pd.DataFrame({
            "Stage": ["Approved", "Shortlisted", "Rejected"],
            "Count": [approved_count, shortlisted_count, rejected_count]
        })
        st.bar_chart(funnel_data.set_index("Stage"))
