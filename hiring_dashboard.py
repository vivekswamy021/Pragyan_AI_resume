import streamlit as st
import os
import json
import re
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from datetime import date
import tempfile
import docx
import pdfplumber

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
# HELPER FUNCTIONS
# -------------------------

def extract_text_from_file(uploaded_file):
    """Helper to extract text from PDF or DOCX."""
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
        else:
            text = str(uploaded_file.read(), "utf-8")
    except Exception as e:
        st.error(f"Error reading file: {e}")
    return text

# -------------------------
# MAIN DASHBOARD FUNCTION
# -------------------------

def hiring_dashboard(go_to_func):
    """
    Main function for the Hiring Manager Dashboard.
    """
    
    col_title, nav_col = st.columns([10, 2])
    
    with col_title:
        st.title("🏢 Hiring Company Dashboard")
        st.caption("Manage your job vacancies and track hiring metrics.")

    with nav_col:
        if st.button("🚪 Log Out", use_container_width=True, key="hiring_logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            go_to_func("login")
            st.rerun()
    
    st.markdown("---")

    if 'admin_jd_list' not in st.session_state: 
        st.session_state.admin_jd_list = []
    if 'resume_statuses' not in st.session_state: 
        st.session_state.resume_statuses = {}

    # Define the primary tabs
    tab_jd_manage, tab_stats = st.tabs([
        "📄 JD Management", 
        "📊 Hiring Analytics"
    ])

    # --- TAB 1: JD MANAGEMENT ---
    with tab_jd_manage:
        st.header("Create and Manage Job Descriptions")
        
        # Sub-navigation within JD Management
        creation_mode = st.radio(
            "Select JD Creation Method",
            ["Upload Doc", "From Linkedin", "Paste Content", "AI Assisted Form Based"],
            horizontal=True
        )
        
        st.markdown("---")

        # 1. Upload Doc
        if creation_mode == "Upload Doc":
            st.subheader("📁 Create JD from Document")
            uploaded_jd = st.file_uploader("Upload JD (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
            role_name = st.text_input("Enter Job Title", placeholder="e.g. Java Developer")
            
            if st.button("Extract and Save JD"):
                if uploaded_jd and role_name:
                    content = extract_text_from_file(uploaded_jd)
                    if content:
                        st.session_state.admin_jd_list.append({
                            "name": role_name, "content": content, "date": str(date.today())
                        })
                        st.success("JD Created successfully from document!")
                        st.rerun()
                else:
                    st.error("Please provide both the file and a job title.")

        # 2. From Linkedin
        elif creation_mode == "From Linkedin":
            st.subheader("🔗 Create JD from LinkedIn")
            li_url = st.text_input("LinkedIn Job URL")
            st.info("Note: System will simulate extraction based on URL pattern.")
            
            if st.button("Import from LinkedIn"):
                if li_url:
                    # Simulated logic
                    simulated_title = li_url.split('/')[-1].replace('-', ' ').title()
                    st.session_state.admin_jd_list.append({
                        "name": simulated_title if simulated_title else "LinkedIn Role",
                        "content": f"Imported from {li_url}\nResponsibilities: [Simulated Content]",
                        "date": str(date.today())
                    })
                    st.success("LinkedIn JD imported!")
                    st.rerun()

        # 3. Paste Content
        elif creation_mode == "Paste Content":
            st.subheader("📋 Paste JD Content")
            p_title = st.text_input("Job Title")
            p_content = st.text_area("Paste the JD here", height=250)
            
            if st.button("Save Pasted JD"):
                if p_title and p_content:
                    st.session_state.admin_jd_list.append({
                        "name": p_title, "content": p_content, "date": str(date.today())
                    })
                    st.success("JD saved successfully!")
                    st.rerun()

        # 4. AI Assisted Form Based
        elif creation_mode == "AI Assisted Form Based":
            st.subheader("🤖 AI Assisted JD Builder")
            with st.form("ai_jd_form"):
                f_role = st.text_input("Role Name")
                f_exp = st.text_input("Years of Experience Required")
                f_skills = st.text_input("Top 5 Required Skills (comma separated)")
                f_resp = st.text_area("Key Responsibilities")
                
                if st.form_submit_button("Generate AI JD"):
                    if f_role and f_skills:
                        prompt = f"Create a professional Job Description for a {f_role} with {f_exp} experience. Skills: {f_skills}. Responsibilities: {f_resp}."
                        try:
                            response = client.chat.completions.create(
                                model=GROQ_MODEL,
                                messages=[{"role": "user", "content": prompt}],
                                temperature=0.5
                            )
                            ai_content = response.choices[0].message.content
                            st.session_state.admin_jd_list.append({
                                "name": f_role, "content": ai_content, "date": str(date.today())
                            })
                            st.success("AI JD Generated and Saved!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"AI Generation failed: {e}")

        st.markdown("### Active Postings")
        if not st.session_state.admin_jd_list:
            st.info("No active JDs.")
        else:
            for i, jd in enumerate(st.session_state.admin_jd_list):
                with st.container(border=True):
                    col_a, col_b = st.columns([4, 1])
                    with col_a:
                        st.subheader(jd['name'])
                        st.caption(f"Created on: {jd.get('date', 'N/A')}")
                        with st.expander("View Details"):
                            st.write(jd['content'])
                    with col_b:
                        if st.button("🗑️ Delete", key=f"del_jd_{i}"):
                            st.session_state.admin_jd_list.pop(i)
                            st.rerun()

    # --- TAB 2: HIRING STATS ---
    with tab_stats:
        st.header("Hiring Metrics Overview")
        
        approved_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Approved")
        shortlisted_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Shortlisted")
        rejected_count = sum(1 for s in st.session_state.resume_statuses.values() if s == "Rejected")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Live Vacancies", len(st.session_state.admin_jd_list))
        c2.metric("Approved Talent", approved_count)
        c3.metric("Shortlisted", shortlisted_count)
        c4.metric("Rejected", rejected_count)
            
        st.markdown("---")
        st.subheader("Application Funnel")
        funnel_data = pd.DataFrame({
            "Stage": ["Approved", "Shortlisted", "Rejected"],
            "Count": [approved_count, shortlisted_count, rejected_count]
        })
        st.bar_chart(funnel_data.set_index("Stage"))
