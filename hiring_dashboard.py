import streamlit as st
import os
import json
import re
import pandas as pd
import tempfile
from groq import Groq
from dotenv import load_dotenv
from datetime import date, datetime
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

def evaluate_cv_against_jd_swot(cv_text, jd_text):
    """Performs a deep match analysis of a CV against a JD using LLM."""
    prompt = f"""
    Act as a Senior Recruiter. Analyze the Candidate CV against the Job Description (JD).
    JD: {jd_text[:2000]}... (truncated)
    CV: {cv_text[:3000]}... (truncated)
    Provide the output strictly as a valid JSON object with these keys:
    1. "match_score": Integer (0-100) representing fit.
    2. "contact_info": Object with keys "name", "email", "phone". Extract from CV or use "N/A".
    3. "swot": Object with keys "strengths" (list), "weaknesses" (list), "opportunities" (list), "threats" (list).
    4. "summary": A brief 1-sentence summary of the fit.
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        return json.loads(match.group(0)) if match else {"error": "Could not parse JSON"}
    except Exception as e:
        return {"error": str(e)}

def score_screening_response(screening_record):
    """Scores a candidate's screening data against general hiring expectations."""
    context = json.dumps(screening_record, indent=2)
    prompt = f"""
    Evaluate this screening candidate data for a generic software role.
    Data: {context}
    
    1. Check if Notice Period is < 30 days or Buyout available (High Score).
    2. Check if Tech Skills are populated (High Score).
    3. Check if Relocation is 'Yes' or 'N/A' (High Score).
    
    Return a single integer score from 0 to 100. Just the number.
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        score_text = response.choices[0].message.content.strip()
        match = re.search(r'\d+', score_text)
        return int(match.group(0)) if match else 50
    except:
        return 50

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
    if 'match_results_cache' not in st.session_state:
        st.session_state.match_results_cache = {}
    if 'screening_data' not in st.session_state: 
        st.session_state.screening_data = []

    # Initialize Screening Form Keys and Status
    if 'scr_status' not in st.session_state:
        st.session_state.scr_status = "Pending" # Pending, Approved, Rejected

    screening_keys = [
        "scr_name", "scr_email", "scr_phone", "scr_company", 
        "scr_curr_ctc", "scr_exp_ctc", "scr_notice", "scr_buyout", 
        "scr_curr_loc", "scr_job_loc", "scr_tech_skills", "scr_exp_dur", 
        "scr_proj_brief", "scr_roles_resp", "scr_achievements", "scr_relocate", "scr_ai_score"
    ]
    for key in screening_keys:
        if key not in st.session_state:
            st.session_state[key] = "" if "score" not in key else 0

    # Function to clear screening form
    def clear_screening_form():
        for k in screening_keys:
            st.session_state[k] = "" if "score" not in k else 0
        st.session_state.scr_status = "Pending"

    # --- Dashboard Tabs ---
    tab_jd_mgmt, tab_upload_cvs, tab_explore_cv, tab_specific_jd, tab_screening, tab_stats = st.tabs([
        "📄 JD Management", 
        "📁 Upload the CVs", 
        "🔍 Explore CV",
        "🎯 For Specific JD", 
        "📞 Basic Screening", 
        "📊 Hiring Analytics"
    ])

    # --- TAB 1: JD Management ---
    with tab_jd_mgmt:
        st.header("Job Description Management")
        create_tab, view_tab = st.tabs(["➕ Create JD", "📋 View Active JDs"])
        
        with create_tab:
            st.subheader("Create New Job Description")
            method = st.selectbox("Choose Method", ["Upload Doc", "From Linkedin", "Paste Content", "AI Assisted Form Based"])
            
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
                            "Content": content
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
                                "Content": content
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
                "🔍 Filter CVs by", "🧠 LLM Analysis", "❓ Query Inform", "📁 Organize CV", "📝 Summarise CV"
            ])

            with explore_filter:
                st.subheader("Filter CVs")
                filter_keyword = st.text_input("Search by Keyword", key="filter_kw")
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

            with explore_llm:
                st.subheader("Run LLM on CV Bank")
                llm_prompt = st.text_area("Custom AI Prompt", placeholder="e.g., Which of these candidates has experience in Fintech?")
                if st.button("Run Global Analysis", key="btn_llm_run"):
                    if llm_prompt:
                        with st.spinner("AI is reviewing the CV Bank..."):
                            try:
                                bank_context = [{"File": cv['File Name'], "Content": str(cv.get('Content', ''))[:1000] + "..."} for cv in st.session_state.company_cv_bank]
                                prompt = f"CV Data:\n{json.dumps(bank_context)}\n\nQuery: {llm_prompt}"
                                res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}])
                                st.write(res.choices[0].message.content)
                            except Exception as e:
                                st.error(f"LLM Error: {e}")

            with explore_query:
                st.subheader("Query Inform")
                query_target = st.radio("Target Selection", ["Individual CV", "Bulk (All CVs)"], horizontal=True)
                selected_cv_name = None
                if query_target == "Individual CV":
                    cv_names = [cv['File Name'] for cv in st.session_state.company_cv_bank]
                    selected_cv_name = st.selectbox("Select CV to query", cv_names, key="query_cv_select")
                query_text = st.text_input("What do you want to know?", placeholder="e.g., Degree details?")
                if st.button("Run Query", key="btn_run_query"):
                    if query_text:
                        with st.spinner("Querying..."):
                            try:
                                if query_target == "Individual CV" and selected_cv_name:
                                    target_cv = next(cv for cv in st.session_state.company_cv_bank if cv['File Name'] == selected_cv_name)
                                    context = target_cv.get('Content', 'No content')
                                else:
                                    context = json.dumps([{"File": cv['File Name'], "Content": str(cv.get('Content', ''))[:500]} for cv in st.session_state.company_cv_bank])
                                prompt = f"Context:\n{context}\n\nAnswer: {query_text}"
                                res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}])
                                st.info(res.choices[0].message.content)
                            except Exception as e:
                                st.error(f"Error: {e}")

            with explore_organize:
                st.subheader("Organize CV Repository")
                sort_by = st.selectbox("Sort CVs By", ["Date Uploaded (Newest First)", "Date Uploaded (Oldest First)", "File Name (A-Z)"])
                cv_list = st.session_state.company_cv_bank.copy()
                if sort_by == "Date Uploaded (Newest First)": cv_list.sort(key=lambda x: x['Date Uploaded'], reverse=True)
                elif sort_by == "Date Uploaded (Oldest First)": cv_list.sort(key=lambda x: x['Date Uploaded'])
                elif sort_by == "File Name (A-Z)": cv_list.sort(key=lambda x: x['File Name'])
                st.dataframe(pd.DataFrame(cv_list)[["File Name", "Upload Type", "Date Uploaded"]], use_container_width=True)

            with explore_summarise:
                st.subheader("Summarise CV Analysis")
                cv_options = [cv['File Name'] for cv in st.session_state.company_cv_bank]
                cv_to_summarise = st.selectbox("Select CV to Summarize", cv_options, key="summarise_cv_select")
                if st.button("Generate Summary", key="btn_gen_summary"):
                    if cv_to_summarise:
                        with st.spinner("Generating summary..."):
                            target_cv = next(cv for cv in st.session_state.company_cv_bank if cv['File Name'] == cv_to_summarise)
                            prompt = f"Summarize this CV in 4 bullet points:\n\n{target_cv.get('Content', '')}"
                            res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}])
                            st.write(res.choices[0].message.content)

    # --- TAB 4: For Specific JD ---
    with tab_specific_jd:
        st.header("🎯 Match CVs Against Specific JD")
        st.markdown("Select a job description to rank your CV bank, perform deep analysis, and export data.")

        if not st.session_state.company_cv_bank:
            st.warning("Please upload CVs in the 'Upload the CVs' tab first.")
        elif not st.session_state.admin_jd_list:
            st.warning("Please create Job Descriptions in the 'JD Management' tab first.")
        else:
            jd_names = [jd['name'] for jd in st.session_state.admin_jd_list]
            selected_jd_name = st.selectbox("Select Active Job Description", jd_names, key="match_jd_select")
            selected_jd = next((jd for jd in st.session_state.admin_jd_list if jd['name'] == selected_jd_name), None)
            
            if selected_jd:
                with st.expander("View Selected JD Content"):
                    st.text(selected_jd['content'])

                if st.button("🚀 Analyze & Rank CVs", type="primary"):
                    match_results = []
                    progress_bar = st.progress(0)
                    total_cvs = len(st.session_state.company_cv_bank)

                    for idx, cv in enumerate(st.session_state.company_cv_bank):
                        progress_bar.progress((idx + 1) / total_cvs)
                        analysis = evaluate_cv_against_jd_swot(cv.get('Content', ''), selected_jd.get('content', ''))
                        
                        if "error" not in analysis:
                            match_results.append({
                                "CV Name": cv['File Name'],
                                "Match Score": analysis.get('match_score', 0),
                                "Summary": analysis.get('summary', 'N/A'),
                                "Email": analysis.get('contact_info', {}).get('email', 'N/A'),
                                "Phone": analysis.get('contact_info', {}).get('phone', 'N/A'),
                                "SWOT": analysis.get('swot', {}),
                                "Name": analysis.get('contact_info', {}).get('name', 'N/A')
                            })
                    
                    match_results.sort(key=lambda x: x['Match Score'], reverse=True)
                    st.session_state.match_results_cache = match_results
                    st.success("Analysis Complete!")

                if st.session_state.get('match_results_cache'):
                    st.divider()
                    st.subheader(f"🏆 Ranking Results for: {selected_jd_name}")
                    results = st.session_state.match_results_cache
                    df_display = pd.DataFrame(results)[["Match Score", "Name", "CV Name", "Email", "Phone", "Summary"]]
                    st.dataframe(df_display, use_container_width=True)

                    csv = df_display.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Contact List (CSV)", data=csv, file_name=f"Matches_{selected_jd_name}.csv", mime='text/csv')

                    st.markdown("### 🧠 Deep Analysis: SWOT for Each Candidate")
                    for item in results:
                        with st.expander(f"{item['Match Score']}% Match | {item['Name']} ({item['CV Name']})"):
                            swot = item.get('SWOT', {})
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown(f":green[**Strengths**]")
                                for s in swot.get('strengths', []): st.markdown(f"- {s}")
                                st.markdown(f":red[**Weaknesses**]")
                                for w in swot.get('weaknesses', []): st.markdown(f"- {w}")
                            with c2:
                                st.markdown(f":blue[**Opportunities**]")
                                for o in swot.get('opportunities', []): st.markdown(f"- {o}")
                                st.markdown(f":orange[**Threats**]")
                                for t in swot.get('threats', []): st.markdown(f"- {t}")

    # --- TAB 5: Basic Screening (UPDATED) ---
    with tab_screening:
        st.header("📞 Candidate Screening Workflow")
        st.markdown("Record screenings, assess responses, and schedule next steps.")

        screen_tab_info, screen_tab_quiz, screen_tab_schedule = st.tabs([
            "📋 Basic Info", 
            "📝 Tech & Roles Quiz",
            "🗓️ Schedule & Evaluate" 
        ])

        # --- Subtab 1: Basic Info ---
        with screen_tab_info:
            with st.container(border=True):
                st.subheader("Candidate Details")
                st.caption(f"Status: **{st.session_state.scr_status}**")
                
                c1, c2, c3 = st.columns(3)
                st.text_input("Candidate Name", key="scr_name")
                st.text_input("Email ID", key="scr_email")
                st.text_input("Phone Number", key="scr_phone")

                st.subheader("Employment Details")
                c4, c5, c6 = st.columns(3)
                st.text_input("Current Company", key="scr_company")
                st.text_input("Current Salary (CTC)", key="scr_cur_ctc")
                st.text_input("Expected Salary (CTC)", key="scr_exp_ctc")

                st.subheader("Notice & Location")
                c7, c8 = st.columns(2)
                st.selectbox("Notice Period", ["Immediate", "15 Days", "30 Days", "60 Days", "90 Days", "Serving Notice"], key="scr_notice")
                st.radio("Notice Buyout Option?", ["Yes", "No", "Negotiable"], horizontal=True, key="scr_buyout")

                c9, c10 = st.columns(2)
                st.text_input("Current Working Location", key="scr_cur_loc")
                st.text_input("Job Location", key="scr_job_loc")

                if st.session_state.scr_curr_loc and st.session_state.scr_job_loc:
                    if st.session_state.scr_curr_loc.lower() != st.session_state.scr_job_loc.lower():
                        st.warning("Location Mismatch")
                        st.radio("Relocate?", ["Yes", "No"], horizontal=True, key="scr_relocate")
                    else:
                        st.session_state.scr_relocate = "N/A"

        # --- Subtab 2: Tech Quiz ---
        with screen_tab_quiz:
            with st.container(border=True):
                st.subheader("Technical & Role Assessment")
                st.text_area("Tech Skills", placeholder="e.g., Python, AWS", key="scr_tech_skills")
                st.text_input("Key Skill Duration", placeholder="e.g., 5 yrs Python", key="scr_exp_dur")
                st.text_area("Project Brief", height=100, key="scr_proj_brief")
                st.text_area("Roles & Responsibilities", height=100, key="scr_roles_resp")
                st.text_area("Achievements", height=100, key="scr_achievements")
            
            st.divider()
            col_reject, col_approve = st.columns(2)
            
            with col_reject:
                if st.button("❌ Reject Candidate", use_container_width=True):
                    st.session_state.scr_status = "Rejected"
                    
                    # Save Rejected Record
                    rec = {
                        "Name": st.session_state.scr_name, "Email": st.session_state.scr_email,
                        "Stage": "Screening", "Status": "Rejected", "Date": date.today().strftime("%Y-%m-%d")
                    }
                    st.session_state.screening_data.append(rec)
                    st.error(f"Candidate {st.session_state.scr_name} has been rejected.")
                    
                    # Reset form for next
                    if st.button("Clear Form & Next Candidate"):
                        clear_screening_form()
                        st.rerun()

            with col_approve:
                if st.button("✅ Approve for Tech Round", use_container_width=True):
                    if st.session_state.scr_name and st.session_state.scr_email:
                        st.session_state.scr_status = "Approved"
                        st.success(f"Candidate Approved! Proceed to the **'Schedule & Evaluate'** tab.")
                    else:
                        st.error("Please fill in basic Name/Email in Tab 1 first.")

        # --- Subtab 3: Schedule & Evaluate (NEW) ---
        with screen_tab_schedule:
            st.header("Schedule & Evaluate Candidate")
            
            if st.session_state.scr_status != "Approved":
                st.warning("🔒 This section is locked. Please complete screening and **Approve** the candidate in the previous tab first.")
            else:
                st.success(f"Processing Candidate: **{st.session_state.scr_name}**")
                
                # A. Scheduling
                with st.expander("🗓️ Schedule Interview Round", expanded=True):
                    sch_col1, sch_col2 = st.columns(2)
                    with sch_col1:
                        round_type = st.selectbox("Interview Type", ["Tech Round 1", "Tech Round 2", "Managerial Round", "Face to Face", "AI Automated Round"])
                        interview_date = st.date_input("Interview Date", min_value=date.today())
                        interview_time = st.time_input("Interview Time")
                    with sch_col2:
                        interviewer_email = st.text_input("Interviewer Email", placeholder="tech.lead@company.com")
                        meeting_link = st.text_input("Meeting Link (Zoom/Teams/Meet)")
                    
                    if st.button("📧 Schedule & Send Invite (Agentic Action)"):
                        st.success(f"✅ Invite Sent to **{st.session_state.scr_name}** ({st.session_state.scr_email}) for **{round_type}** on {interview_date} at {interview_time}.")
                        st.info("📅 Event added to Calendar (Simulated).")

                st.divider()

                # B. Evaluation & Ranking
                st.subheader("🤖 AI Evaluation & Ranking")
                if st.button("Run AI Score Analysis"):
                    # Construct data packet for scoring
                    candidate_packet = {
                        "Notice Period": st.session_state.scr_notice,
                        "Tech Skills": st.session_state.scr_tech_skills,
                        "Relocation": st.session_state.scr_relocate,
                        "Roles": st.session_state.scr_roles_resp
                    }
                    
                    with st.spinner("AI is analyzing screening responses against expectations..."):
                        ai_score = score_screening_response(candidate_packet)
                        st.session_state.scr_ai_score = ai_score
                    
                    st.metric("AI Match Score", f"{ai_score}/100", delta="Ready for Next Round" if ai_score > 70 else "Review Needed")

                # C. Save & Dump to CSV
                st.divider()
                if st.button("💾 Save & Add to Master List", type="primary"):
                    # Gather all data
                    full_record = {
                        "Name": st.session_state.scr_name,
                        "Email": st.session_state.scr_email,
                        "Phone": st.session_state.scr_phone,
                        "Company": st.session_state.scr_company,
                        "Notice Period": st.session_state.scr_notice,
                        "Current Loc": st.session_state.scr_curr_loc,
                        "Brief Profile": f"Exp in {st.session_state.scr_tech_skills}. {st.session_state.scr_exp_dur}",
                        "Match Score (AI)": st.session_state.get('scr_ai_score', 'N/A'),
                        "CV Link": "https://drive.google.com/...", # Placeholder or link to uploaded file
                        "Date": date.today().strftime("%Y-%m-%d"),
                        "Status": "Tech Round Scheduled"
                    }
                    st.session_state.screening_data.append(full_record)
                    st.success(f"Candidate {st.session_state.scr_name} added to Master List!")
                    
                    if st.button("Start New Screening"):
                        clear_screening_form()
                        st.rerun()

            # D. Download Master List (Always Visible)
            if st.session_state.screening_data:
                st.divider()
                st.markdown("### 📥 Export Master Data")
                df_master = pd.DataFrame(st.session_state.screening_data)
                st.dataframe(df_master, use_container_width=True)
                
                csv_master = df_master.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Master CSV (Contact & Scores)",
                    data=csv_master,
                    file_name="Master_Screening_List.csv",
                    mime="text/csv"
                )

    # --- TAB 6: Hiring Analytics ---
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
