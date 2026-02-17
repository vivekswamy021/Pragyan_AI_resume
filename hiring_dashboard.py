import streamlit as st
import os
import json
import re
import pandas as pd
import tempfile
from groq import Groq
from dotenv import load_dotenv
from datetime import date
import pdfplumber
import docx

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

def extract_jd_metadata(jd_text):
    """Uses LLM to extract structured metadata from raw JD text."""
    prompt = f"""Analyze the Job Description and extract metadata in JSON:
    1. role: Job title
    2. job_type: Full-time, Contract, etc.
    3. key_skills: List of top 5 skills
    
    JD: {jd_text}"""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        return json.loads(match.group(0)) if match else {}
    except:
        return {"role": "N/A", "job_type": "Full-time", "key_skills": []}

def get_file_content(uploaded_file):
    """Extracts text from PDF or DOCX."""
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
        text = f"Error extracting content: {e}"
    return text

# -------------------------
# MAIN DASHBOARD FUNCTION
# -------------------------

def hiring_dashboard(go_to_func):
    col_title, nav_col = st.columns([10, 2])
    
    with col_title:
        st.title("🏢 Hiring Company Dashboard")
        st.caption("Manage Job Descriptions, candidate CVs, and track hiring metrics.")

    with nav_col:
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
    if 'company_cv_bank' not in st.session_state:
        st.session_state.company_cv_bank = []

    # --- Dashboard Tabs ---
    # Added "🔍 Explore CV" next to "Upload the CVs"
    tab_jd_mgmt, tab_upload_cvs, tab_explore_cv, tab_stats = st.tabs([
        "📄 JD Management", 
        "📁 Upload the CVs", 
        "🔍 Explore CV",
        "📊 Hiring Analytics"
    ])

    # --- TAB 1: JD Management ---
    with tab_jd_mgmt:
        st.header("Job Description Management")
        
        create_tab, view_tab = st.tabs(["➕ Create JD", "📋 View Active JDs"])
        
        with create_tab:
            st.subheader("Create New Job Description")
            method = st.selectbox("Choose Method", ["Upload Doc", "From Linkedin", "Paste Content", "AI Assisted Form Based"])
            
            # --- Method 1: Upload Doc ---
            if method == "Upload Doc":
                uploaded_file = st.file_uploader("Upload JD (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"])
                if st.button("Process & Save Document"):
                    if uploaded_file:
                        with st.spinner("Extracting content..."):
                            content = get_file_content(uploaded_file)
                            meta = extract_jd_metadata(content)
                            st.session_state.admin_jd_list.append({
                                "name": meta.get("role", uploaded_file.name),
                                "content": content,
                                "job_type": meta.get("job_type", "Full-time"),
                                "date_posted": date.today().strftime("%Y-%m-%d")
                            })
                            st.success("JD uploaded and processed successfully!")
                    else:
                        st.error("Please upload a file.")

            # --- Method 2: From Linkedin ---
            elif method == "From Linkedin":
                url = st.text_input("Paste Linkedin Job URL")
                if st.button("Import from Linkedin"):
                    if "linkedin.com/jobs" in url:
                        st.info("Simulating Linkedin extraction...")
                        # Mock extraction logic
                        content = f"Job imported from {url}. Required: Experience in Python and SQL."
                        st.session_state.admin_jd_list.append({
                            "name": "Linkedin Role",
                            "content": content,
                            "job_type": "Full-time",
                            "date_posted": date.today().strftime("%Y-%m-%d")
                        })
                        st.success("Linkedin JD imported!")
                    else:
                        st.error("Invalid URL format.")

            # --- Method 3: Paste Content ---
            elif method == "Paste Content":
                role_input = st.text_input("Role Title")
                content_input = st.text_area("Paste JD Text", height=250)
                if st.button("Save Pasted JD"):
                    if role_input and content_input:
                        st.session_state.admin_jd_list.append({
                            "name": role_input,
                            "content": content_input,
                            "job_type": "Full-time",
                            "date_posted": date.today().strftime("%Y-%m-%d")
                        })
                        st.success("JD saved!")
                    else:
                        st.error("Fields cannot be empty.")

            # --- Method 4: AI Assisted Form Based ---
            elif method == "AI Assisted Form Based":
                with st.form("ai_form"):
                    role_f = st.text_input("Target Role")
                    exp_f = st.slider("Min Experience (Years)", 0, 15, 2)
                    skills_f = st.text_input("Required Skills (comma separated)")
                    mission_f = st.text_area("Company Mission/Context")
                    
                    if st.form_submit_button("✨ Generate & Save with AI"):
                        with st.spinner("Generating detailed JD..."):
                            prompt = f"Create a professional JD for {role_f} with {exp_f} years exp. Skills: {skills_f}. Context: {mission_f}"
                            res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}])
                            ai_content = res.choices[0].message.content
                            st.session_state.admin_jd_list.append({
                                "name": role_f,
                                "content": ai_content,
                                "job_type": "Full-time",
                                "date_posted": date.today().strftime("%Y-%m-%d")
                            })
                            st.success("AI JD Generated and Saved!")

        with view_tab:
            if not st.session_state.admin_jd_list:
                st.info("No active JDs.")
            else:
                for i, jd in enumerate(st.session_state.admin_jd_list):
                    with st.container(border=True):
                        c1, c2 = st.columns([5, 1])
                        c1.subheader(jd['name'])
                        c1.caption(f"Posted: {jd.get('date_posted')} | Type: {jd.get('job_type')}")
                        if c2.button("🗑️", key=f"del_{i}"):
                            st.session_state.admin_jd_list.pop(i)
                            st.rerun()
                        with st.expander("Show Full Description"):
                            st.write(jd['content'])

    # --- TAB 2: Upload the CVs ---
    with tab_upload_cvs:
        st.header("Candidate CV Management")
        
        cv_ind_tab, cv_bulk_tab, cv_bank_tab = st.tabs(["👤 Individual", "📚 Bulk", "💾 Digital CV Bank"])
        
        # --- Individual Upload ---
        with cv_ind_tab:
            st.subheader("Upload a Single Candidate CV")
            ind_file = st.file_uploader("Select Candidate CV (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="ind_cv_upload")
            
            if st.button("Upload & Save CV", key="btn_ind_cv"):
                if ind_file:
                    with st.spinner("Processing CV..."):
                        content = get_file_content(ind_file)
                        st.session_state.company_cv_bank.append({
                            "File Name": ind_file.name,
                            "Content Length": len(content),
                            "Upload Type": "Individual",
                            "Date Uploaded": date.today().strftime("%Y-%m-%d"),
                            "Content": content # Storing raw text for LLM features
                        })
                        st.success(f"CV '{ind_file.name}' successfully added to the Digital Bank!")
                else:
                    st.error("Please choose a file to upload.")

        # --- Bulk Upload ---
        with cv_bulk_tab:
            st.subheader("Bulk Upload Candidate CVs")
            bulk_files = st.file_uploader("Select Multiple CVs (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="bulk_cv_upload")
            
            if st.button("Upload & Save All CVs", key="btn_bulk_cv"):
                if bulk_files:
                    with st.spinner(f"Processing {len(bulk_files)} CVs..."):
                        for file in bulk_files:
                            content = get_file_content(file)
                            st.session_state.company_cv_bank.append({
                                "File Name": file.name,
                                "Content Length": len(content),
                                "Upload Type": "Bulk",
                                "Date Uploaded": date.today().strftime("%Y-%m-%d"),
                                "Content": content # Storing raw text
                            })
                        st.success(f"Successfully added {len(bulk_files)} CVs to the Digital Bank!")
                else:
                    st.error("Please select at least one file to upload.")

        # --- Digital CV Bank ---
        with cv_bank_tab:
            st.subheader("Digital CV Bank")
            st.markdown("Overview of all locally uploaded candidate resumes.")
            
            if not st.session_state.company_cv_bank:
                st.info("Your Digital CV Bank is currently empty. Upload CVs using the Individual or Bulk tabs.")
            else:
                cv_df = pd.DataFrame(st.session_state.company_cv_bank)
                st.dataframe(cv_df[["File Name", "Upload Type", "Date Uploaded"]], use_container_width=True)
                
                if st.button("🗑️ Clear Digital CV Bank", type="secondary"):
                    st.session_state.company_cv_bank = []
                    st.rerun()

    # --- TAB 3: Explore CV ---
    with tab_explore_cv:
        st.header("Explore & Analyze CVs")
        st.markdown("Use advanced tools to query, filter, and summarize your Digital CV Bank.")

        if not st.session_state.company_cv_bank:
            st.warning("Please upload CVs in the 'Upload the CVs' tab to use these features.")
        else:
            explore_filter, explore_llm, explore_query, explore_organize, explore_summarise = st.tabs([
                "🔍 Filter CVs by", 
                "🧠 LLM Analysis", 
                "❓ Query Inform", 
                "📁 Organize CV", 
                "📝 Summarise CV"
            ])

            # 1. Filter CVs
            with explore_filter:
                st.subheader("Filter CVs")
                filter_keyword = st.text_input("Search by Keyword (e.g., Python, Manager)", key="filter_kw")
                filter_type = st.multiselect("Filter by Upload Type", ["Individual", "Bulk"], default=["Individual", "Bulk"])
                
                if st.button("Apply Filters", key="btn_apply_filter"):
                    filtered_cvs = []
                    for cv in st.session_state.company_cv_bank:
                        if cv['Upload Type'] in filter_type:
                            if not filter_keyword or filter_keyword.lower() in str(cv.get('Content', '')).lower():
                                filtered_cvs.append(cv)
                    
                    st.write(f"Found {len(filtered_cvs)} matching CV(s).")
                    if filtered_cvs:
                        st.dataframe(pd.DataFrame(filtered_cvs)[["File Name", "Upload Type", "Date Uploaded"]], use_container_width=True)

            # 2. LLM Analysis
            with explore_llm:
                st.subheader("Run LLM on CV Bank")
                st.markdown("Prompt the AI to analyze the entire CV bank for specific criteria.")
                llm_prompt = st.text_area("Custom AI Prompt", placeholder="e.g., Which of these candidates has the strongest background in cloud architecture?")
                
                if st.button("Run Global Analysis", key="btn_llm_run"):
                    if llm_prompt:
                        with st.spinner("AI is reviewing the CV Bank..."):
                            try:
                                # Prepare context (limiting to names and snippets if too large, but doing full text here for demo)
                                bank_context = [{"File": cv['File Name'], "Content": str(cv.get('Content', ''))[:1000] + "..."} for cv in st.session_state.company_cv_bank]
                                prompt = f"CV Data:\n{json.dumps(bank_context)}\n\nQuery: {llm_prompt}"
                                
                                res = client.chat.completions.create(
                                    model=GROQ_MODEL, 
                                    messages=[{"role": "user", "content": prompt}]
                                )
                                st.write(res.choices[0].message.content)
                            except Exception as e:
                                st.error(f"LLM Error: {e}")
                    else:
                        st.error("Please enter a prompt.")

            # 3. Query Inform
            with explore_query:
                st.subheader("Query Inform")
                query_target = st.radio("Target Selection", ["Individual CV", "Bulk (All CVs)"], horizontal=True)
                
                selected_cv_name = None
                if query_target == "Individual CV":
                    cv_names = [cv['File Name'] for cv in st.session_state.company_cv_bank]
                    selected_cv_name = st.selectbox("Select CV to query", cv_names, key="query_cv_select")

                query_text = st.text_input("What do you want to know?", placeholder="e.g., What is the candidate's highest degree?")
                
                if st.button("Run Query", key="btn_run_query"):
                    if query_text:
                        with st.spinner("Querying..."):
                            try:
                                if query_target == "Individual CV" and selected_cv_name:
                                    target_cv = next(cv for cv in st.session_state.company_cv_bank if cv['File Name'] == selected_cv_name)
                                    context = target_cv.get('Content', 'No content')
                                else:
                                    context = json.dumps([{"File": cv['File Name'], "Content": str(cv.get('Content', ''))[:500]} for cv in st.session_state.company_cv_bank])
                                
                                prompt = f"Context:\n{context}\n\nAnswer the following question based on the context: {query_text}"
                                res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}])
                                st.info(res.choices[0].message.content)
                            except Exception as e:
                                st.error(f"Error: {e}")
                    else:
                        st.error("Please enter a query.")

            # 4. Organize - CV
            with explore_organize:
                st.subheader("Organize CV Repository")
                sort_by = st.selectbox("Sort CVs By", ["Date Uploaded (Newest First)", "Date Uploaded (Oldest First)", "File Name (A-Z)"])
                
                cv_list = st.session_state.company_cv_bank.copy()
                if sort_by == "Date Uploaded (Newest First)":
                    cv_list.sort(key=lambda x: x['Date Uploaded'], reverse=True)
                elif sort_by == "Date Uploaded (Oldest First)":
                    cv_list.sort(key=lambda x: x['Date Uploaded'])
                elif sort_by == "File Name (A-Z)":
                    cv_list.sort(key=lambda x: x['File Name'])
                
                st.dataframe(pd.DataFrame(cv_list)[["File Name", "Upload Type", "Date Uploaded"]], use_container_width=True)

            # 5. Summarise CV - Analysis
            with explore_summarise:
                st.subheader("Summarise CV Analysis")
                cv_options = [cv['File Name'] for cv in st.session_state.company_cv_bank]
                cv_to_summarise = st.selectbox("Select CV to Summarize", cv_options, key="summarise_cv_select")
                
                if st.button("Generate Summary", key="btn_gen_summary"):
                    if cv_to_summarise:
                        with st.spinner("Generating summary..."):
                            try:
                                target_cv = next(cv for cv in st.session_state.company_cv_bank if cv['File Name'] == cv_to_summarise)
                                prompt = f"Provide a brief, professional 4-bullet point summary highlighting the key skills and experience in this CV:\n\n{target_cv.get('Content', '')}"
                                res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}])
                                
                                st.markdown(f"### Summary for {cv_to_summarise}")
                                st.write(res.choices[0].message.content)
                            except Exception as e:
                                st.error(f"Error generating summary: {e}")

    # --- TAB 4: Hiring Analytics ---
    with tab_stats:
        st.header("Hiring Metrics Overview")
        app_count = len(st.session_state.resume_statuses)
        approved = sum(1 for s in st.session_state.resume_statuses.values() if s == "Approved")
        shortlisted = sum(1 for s in st.session_state.resume_statuses.values() if s == "Shortlisted")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Vacancies", len(st.session_state.admin_jd_list))
        m2.metric("CVs in Bank", len(st.session_state.company_cv_bank))
        m3.metric("Approved Candidates", approved)
        m4.metric("Shortlisted", shortlisted)
        
        st.markdown("---")
        if st.session_state.resume_statuses:
            df = pd.DataFrame(list(st.session_state.resume_statuses.items()), columns=["Candidate", "Status"])
            st.bar_chart(df['Status'].value_counts())
        else:
            st.info("Awaiting candidate applications.")
