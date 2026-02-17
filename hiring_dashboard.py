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

@st.cache_data(show_spinner="Parsing CV with AI...")
def parse_cv_with_llm(text):
    """Sends CV text to the LLM for structured information extraction."""
    if not GROQ_API_KEY:
        return {"error": "API key missing.", "raw_output": ""}

    prompt = f"""Extract the following information from the resume in structured JSON.
    - name, - email, - phone, - skills (array of strings), - education (array of strings), 
    - experience (array of strings), - summary (brief 2-3 sentence overview of candidate)
    
    Resume Text: {text}
    
    Provide the output strictly as a JSON object.
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0).strip()
            return json.loads(json_str)
        else:
            return {"error": "Failed to parse JSON", "raw_output": content}
    except Exception as e:
        return {"error": f"LLM error: {str(e)}"}

def get_file_content(uploaded_file):
    """Extracts text from PDF, DOCX, or TXT files."""
    text = ""
    try:
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                text = "\n".join([page.extract_text() or "" for page in pdf.pages])
        elif "wordprocessingml" in uploaded_file.type:
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
        else:
            text = str(uploaded_file.read(), "utf-8")
    except Exception as e:
        text = f"Error extracting content: {e}"
    return text

def process_uploaded_cv(file):
    """Helper to process a single CV file, parse it, and store it in session state."""
    content = get_file_content(file)
    if content.startswith("Error"):
        st.error(f"Failed to read {file.name}")
        return False
        
    parsed_data = parse_cv_with_llm(content)
    
    # Store in the global resume pool
    candidate_name = parsed_data.get('name', file.name.split('.')[0])
    
    cv_record = {
        "name": candidate_name,
        "parsed": parsed_data,
        "applied_jd": "Direct Upload (Company)",
        "submitted_date": date.today().strftime("%Y-%m-%d"),
        "source": "Company Sourced"
    }
    
    st.session_state.resumes_to_analyze.append(cv_record)
    st.session_state.resume_statuses[candidate_name] = "Company Sourced"
    return candidate_name

# -------------------------
# MAIN DASHBOARD FUNCTION
# -------------------------

def hiring_dashboard(go_to_func):
    col_title, nav_col = st.columns([10, 2])
    
    with col_title:
        st.title("🏢 Hiring Company Dashboard")
        st.caption("Manage Job Descriptions, Candidates, and Hiring Metrics.")

    with nav_col:
        if st.button("🚪 Log Out", use_container_width=True, key="hiring_logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            go_to_func("login")
            st.rerun()
    
    st.markdown("---")

    # Safety session state initialization
    if 'admin_jd_list' not in st.session_state: 
        st.session_state.admin_jd_list = []
    if 'resumes_to_analyze' not in st.session_state: 
        st.session_state.resumes_to_analyze = []
    if 'resume_statuses' not in st.session_state: 
        st.session_state.resume_statuses = {}

    # --- Dashboard Tabs ---
    tab_jd_mgmt, tab_upload_cvs, tab_stats = st.tabs([
        "📄 JD Management", 
        "📤 Upload the CVs", 
        "📊 Hiring Analytics"
    ])

    # --- TAB 1: JD Management ---
    with tab_jd_mgmt:
        st.header("Job Description Management")
        
        create_tab, view_tab = st.tabs(["➕ Create JD", "📋 View Active JDs"])
        
        with create_tab:
            st.subheader("Create New Job Description")
            method = st.selectbox("Choose Method", ["Upload Doc", "From Linkedin", "Paste Content", "AI Assisted Form Based"])
            
            # Method 1: Upload Doc
            if method == "Upload Doc":
                uploaded_file = st.file_uploader("Upload JD (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="jd_upload")
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

            # Method 2: From Linkedin
            elif method == "From Linkedin":
                url = st.text_input("Paste Linkedin Job URL")
                if st.button("Import from Linkedin"):
                    if "linkedin.com/jobs" in url:
                        st.info("Simulating Linkedin extraction...")
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

            # Method 3: Paste Content
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

            # Method 4: AI Assisted Form Based
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
        
        ind_tab, bulk_tab, bank_tab = st.tabs(["👤 Individual", "📂 Bulk", "🗄️ Digital CV Bank"])
        
        # --- Section 1: Individual Upload ---
        with ind_tab:
            st.subheader("Upload Single Candidate CV")
            st.write("Upload a candidate's resume to automatically parse and add them to your CV bank.")
            
            single_file = st.file_uploader("Upload Document (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], key="single_cv_upload")
            
            if st.button("Process & Save CV", type="primary", key="btn_single_cv"):
                if single_file:
                    with st.spinner("Extracting and parsing CV data..."):
                        name = process_uploaded_cv(single_file)
                        if name:
                            st.success(f"Successfully processed CV for **{name}**!")
                else:
                    st.warning("Please upload a file first.")

        # --- Section 2: Bulk Upload ---
        with bulk_tab:
            st.subheader("Bulk Upload CVs")
            st.write("Upload multiple resumes at once to populate your talent pool.")
            
            bulk_files = st.file_uploader("Upload Multiple Documents", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="bulk_cv_upload")
            
            if st.button("Process All CVs", type="primary", key="btn_bulk_cv"):
                if bulk_files:
                    success_count = 0
                    progress_bar = st.progress(0)
                    
                    for idx, file in enumerate(bulk_files):
                        with st.spinner(f"Processing {file.name}..."):
                            name = process_uploaded_cv(file)
                            if name:
                                success_count += 1
                        progress_bar.progress((idx + 1) / len(bulk_files))
                    
                    if success_count > 0:
                        st.success(f"Successfully processed {success_count} out of {len(bulk_files)} CVs!")
                else:
                    st.warning("Please upload files first.")

        # --- Section 3: Digital CV Bank ---
        with bank_tab:
            st.subheader("Digital CV Bank")
            st.write("View all candidates currently stored in your system.")
            
            if not st.session_state.resumes_to_analyze:
                st.info("No CVs uploaded yet. Use the Individual or Bulk tabs to add candidates.")
            else:
                # Prepare data for display
                display_data = []
                for res in st.session_state.resumes_to_analyze:
                    parsed = res.get('parsed', {})
                    skills_list = parsed.get('skills', [])
                    skills_display = ", ".join(skills_list[:5]) + ("..." if len(skills_list) > 5 else "")
                    
                    display_data.append({
                        "Name": res.get('name', 'Unknown'),
                        "Email": parsed.get('email', 'N/A'),
                        "Source": res.get('source', 'Candidate Portal'),
                        "Applied/Assigned JD": res.get('applied_jd', 'N/A'),
                        "Top Skills": skills_display,
                        "Status": st.session_state.resume_statuses.get(res['name'], 'Pending')
                    })
                
                df_cvs = pd.DataFrame(display_data)
                
                # Filters
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    status_filter = st.selectbox("Filter by Status", ["All"] + list(df_cvs['Status'].unique()))
                with col_f2:
                    search_query = st.text_input("Search by Name or Skill")
                    
                # Apply Filters
                filtered_df = df_cvs.copy()
                if status_filter != "All":
                    filtered_df = filtered_df[filtered_df['Status'] == status_filter]
                if search_query:
                    filtered_df = filtered_df[
                        filtered_df['Name'].str.contains(search_query, case=False, na=False) |
                        filtered_df['Top Skills'].str.contains(search_query, case=False, na=False)
                    ]
                
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                
                # Detailed view expanders
                st.markdown("#### Candidate Details")
                for res in st.session_state.resumes_to_analyze:
                    # Only show details for candidates currently visible in the filtered table
                    if res['name'] in filtered_df['Name'].values:
                        with st.expander(f"📄 {res['name']} - {res.get('applied_jd', 'No JD')}"):
                            st.markdown(f"**Summary:** {res.get('parsed', {}).get('summary', 'N/A')}")
                            st.json(res.get('parsed', {}))

    # --- TAB 3: Hiring Analytics ---
    with tab_stats:
        st.header("Hiring Metrics Overview")
        app_count = len(st.session_state.resume_statuses)
        company_sourced = sum(1 for s in st.session_state.resume_statuses.values() if s == "Company Sourced")
        approved = sum(1 for s in st.session_state.resume_statuses.values() if s == "Approved")
        shortlisted = sum(1 for s in st.session_state.resume_statuses.values() if s == "Shortlisted")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Live Vacancies", len(st.session_state.admin_jd_list))
        m2.metric("Total CVs in Bank", app_count)
        m3.metric("Company Sourced", company_sourced)
        m4.metric("Shortlisted Talent", shortlisted)
        
        st.markdown("---")
        if st.session_state.resume_statuses:
            df_stats = pd.DataFrame(list(st.session_state.resume_statuses.items()), columns=["Candidate", "Status"])
            st.bar_chart(df_stats['Status'].value_counts())
        else:
            st.info("Awaiting candidate applications or uploads.")
