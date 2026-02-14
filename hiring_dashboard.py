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
# SHARED LOGIC / AI HELPER
# -------------------------

def hiring_pool_chatbot(question):
    """AI Chatbot to query the approved candidate pool."""
    if "resumes_to_analyze" not in st.session_state or "resume_statuses" not in st.session_state:
        return "System error: Candidate database not initialized."

    approved_resumes = [
        res['parsed'] for res in st.session_state.resumes_to_analyze 
        if st.session_state.resume_statuses.get(res['name']) in ["Approved", "Shortlisted"]
    ]
    
    if not approved_resumes:
        return "No approved candidates found in the pool yet. Please wait for the Admin to approve candidates."

    context = json.dumps(approved_resumes, indent=2)
    prompt = f"""
    You are a Recruitment Assistant for a Hiring Manager. You have access to the following approved candidate data:
    {context}
    
    Based ONLY on this data, answer the following hiring manager question concisely.
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
# MAIN DASHBOARD FUNCTION
# -------------------------

def hiring_dashboard(go_to_func):
    """
    Hiring Company Dashboard.
    Args:
        go_to_func: The function used to change st.session_state.page
    """
    
    # --- Dashboard Header and Logout Button ---
    col_title, nav_col = st.columns([10, 2])
    
    with col_title:
        st.title("🏢 Hiring Company Dashboard")
        st.caption("Review approved talent and manage job vacancies.")

    with nav_col:
        # Logout logic handles state clearing and redirect
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            go_to_func("login")
            st.rerun()
    
    st.markdown("---")

    # --- Safety Initialization ---
    if 'admin_jd_list' not in st.session_state: st.session_state.admin_jd_list = []
    if 'resumes_to_analyze' not in st.session_state: st.session_state.resumes_to_analyze = []
    if 'resume_statuses' not in st.session_state: st.session_state.resume_statuses = {}

    # --- Dashboard Tabs ---
    tab_postings, tab_candidates, tab_chatbot, tab_stats = st.tabs([
        "📝 My Job Postings", 
        "👥 Review Approved Talent", 
        "🤖 AI Hiring Assistant",
        "📊 Hiring Analytics"
    ])

    # --- TAB 1: Job Postings ---
    with tab_postings:
        st.header("Manage Vacancies")
        
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
                        st.session_state.admin_jd_list.append(new_jd)
                        st.success(f"Job Posting for '{role_title}' is now live!")
                        st.rerun()
                    else:
                        st.error("Please provide both a Role Title and Job Description.")

        st.markdown("### Active Postings")
        if not st.session_state.admin_jd_list:
            st.info("You haven't posted any jobs yet.")
        else:
            for i, jd in enumerate(st.session_state.admin_jd_list):
                with st.container(border=True):
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.subheader(f"{jd['name']}")
                        st.caption(f"Type: {jd.get('job_type', 'N/A')} | Posted: {jd.get('date_posted', 'N/A')}")
                    with col_b:
                        if st.button("🗑️ Delete", key=f"del_jd_{i}"):
                            st.session_state.admin_jd_list.pop(i)
                            st.rerun()

    # --- TAB 2: Review Candidates ---
    with tab_candidates:
        st.header("Approved Candidate Queue")
        
        review_pool = [
            res for res in st.session_state.resumes_to_analyze 
            if st.session_state.resume_statuses.get(res['name']) in ["Approved", "Shortlisted"]
        ]

        if not review_pool:
            st.warning("No candidates have been approved for review yet.")
        else:
            assigned_jds = list(set([res.get('applied_jd', 'General Pool') for res in review_pool]))
            selected_filter = st.selectbox("Filter by Specific Job Posting", ["All Candidates"] + assigned_jds)

            display_data = []
            for res in review_pool:
                if selected_filter == "All Candidates" or res.get('applied_jd') == selected_filter:
                    status = st.session_state.resume_statuses.get(res['name'])
                    display_data.append({
                        "Candidate Name": res['name'],
                        "Assigned Role": res.get('applied_jd', 'N/A'),
                        "Current Status": status,
                        "Email": res['parsed'].get('email', 'N/A'),
                        "Phone": res['parsed'].get('phone', 'N/A')
                    })
            
            if display_data:
                st.table(display_data)
                for res in review_pool:
                    if selected_filter == "All Candidates" or res.get('applied_jd') == selected_filter:
                        with st.expander(f"📄 View Resume Details: {res['name']}"):
                            st.json(res['parsed'])
            else:
                st.info("No candidates found for this specific filter.")

    # --- TAB 3: Hiring Chatbot ---
    with tab_chatbot:
        st.header("Recruitment Assistant Chatbot")
        user_query = st.text_input("Ask about candidates:", placeholder="e.g. 'Show me candidates with Python skills'")
        
        if st.button("Search Talent Pool", type="primary"):
            if user_query:
                with st.spinner("AI is analyzing the candidate pool..."):
                    answer = hiring_pool_chatbot(user_query)
                    st.markdown("### 🤖 Hiring Assistant Response:")
                    st.write(answer)
            else:
                st.error("Please enter a question.")

    # --- TAB 4: Hiring Stats ---
    with tab_stats:
        st.header("Hiring Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Live Vacancies", len(st.session_state.admin_jd_list))
        with col2:
            approved_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Approved")
            st.metric("Approved Talent", approved_count)
        with col3:
            shortlisted_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Shortlisted")
            st.metric("Shortlisted", shortlisted_count)
