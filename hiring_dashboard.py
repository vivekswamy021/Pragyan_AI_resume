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
import base64

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
    """Deep match analysis of a CV against a JD using LLM (SWOT)."""
    prompt = f"""
    Act as a Senior Recruiter. Analyze the Candidate CV against the Job Description (JD).
    
    JD: {jd_text[:2000]}...
    CV: {cv_text[:3000]}...
    
    Output strictly JSON:
    {{
        "match_score": 0-100,
        "contact_info": {{"name": "", "email": "", "phone": ""}},
        "swot": {{"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}},
        "summary": "1 sentence summary"
    }}
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.1
        )
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        return json.loads(match.group(0)) if match else {"error": "JSON Error"}
    except Exception as e:
        return {"error": str(e)}

def evaluate_screening_data(screening_data, jd_text):
    """Evaluates screening responses against JD expectations."""
    prompt = f"""
    Evaluate this candidate based on their screening interview responses against the JD.
    
    Job Description: {jd_text[:1000]}...
    
    Screening Data:
    - Current Salary: {screening_data.get('curr_ctc')}
    - Expected Salary: {screening_data.get('exp_ctc')}
    - Notice Period: {screening_data.get('notice')} (Buyout available: {screening_data.get('buyout')})
    - Tech Skills Exp: {screening_data.get('tech_exp')}
    - Project Brief: {screening_data.get('projects')}
    - Roles & Resp: {screening_data.get('roles')}
    
    Output strictly JSON:
    {{
        "screening_score": 0-100,
        "recommendation": "Shortlist" or "Reject" or "Hold",
        "reasoning": "Brief explanation of the score based on salary fit, notice period, and technical depth."
    }}
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.2
        )
        content = response.choices[0].message.content
        match = re.search(r'\{.*\}', content, re.DOTALL)
        return json.loads(match.group(0)) if match else {"screening_score": 0, "recommendation": "Error", "reasoning": "LLM Parsing Failed"}
    except:
        return {"screening_score": 0, "recommendation": "Error", "reasoning": "LLM API Error"}

# -------------------------
# MAIN DASHBOARD FUNCTION
# -------------------------

def hiring_dashboard(go_to_func):
    col_title, nav_col = st.columns([10, 2])
    
    with col_title:
        st.title("🏢 Hiring Company Dashboard")
        st.caption("Manage JDs, CVs, Screening, and Hiring Analytics.")

    with nav_col:
        if st.button("🚪 Log Out", use_container_width=True, key="hiring_logout_btn"):
            st.session_state.logged_in = False
            st.session_state.user_type = None
            go_to_func("login")
            st.rerun()
    
    st.markdown("---")

    # --- Safety Initialization ---
    if 'admin_jd_list' not in st.session_state: st.session_state.admin_jd_list = []
    if 'company_cv_bank' not in st.session_state: st.session_state.company_cv_bank = []
    if 'match_results_cache' not in st.session_state: st.session_state.match_results_cache = []
    if 'screened_candidates' not in st.session_state: st.session_state.screened_candidates = [] # Stores screening results

    # --- Dashboard Tabs ---
    tab_jd_mgmt, tab_upload_cvs, tab_explore_cv, tab_specific_jd, tab_screening, tab_stats = st.tabs([
        "📄 JD Management", 
        "📁 Upload the CVs", 
        "🔍 Explore CV",
        "🎯 For Specific JD",
        "🕵️ Screen & Schedule", # NEW TAB
        "📊 Analytics"
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
                        content = get_file_content(uploaded_file)
                        meta = extract_jd_metadata(content)
                        st.session_state.admin_jd_list.append({
                            "name": meta.get("role", uploaded_file.name),
                            "content": content,
                            "job_type": meta.get("job_type", "Full-time"),
                            "date_posted": date.today().strftime("%Y-%m-%d")
                        })
                        st.success("JD saved!")

            elif method == "From Linkedin":
                url = st.text_input("Paste Linkedin Job URL")
                if st.button("Import from Linkedin"):
                    if "linkedin.com/jobs" in url:
                        content = f"Job imported from {url}. Required: Experience in Python and SQL."
                        st.session_state.admin_jd_list.append({
                            "name": "Linkedin Role",
                            "content": content,
                            "job_type": "Full-time",
                            "date_posted": date.today().strftime("%Y-%m-%d")
                        })
                        st.success("Linkedin JD imported!")

            elif method == "Paste Content":
                role_input = st.text_input("Role Title")
                content_input = st.text_area("Paste JD Text", height=250)
                if st.button("Save Pasted JD"):
                    st.session_state.admin_jd_list.append({
                        "name": role_input,
                        "content": content_input,
                        "job_type": "Full-time",
                        "date_posted": date.today().strftime("%Y-%m-%d")
                    })
                    st.success("JD saved!")

            elif method == "AI Assisted Form Based":
                with st.form("ai_form"):
                    role_f = st.text_input("Target Role")
                    exp_f = st.slider("Min Experience (Years)", 0, 15, 2)
                    skills_f = st.text_input("Required Skills (comma separated)")
                    mission_f = st.text_area("Company Mission/Context")
                    if st.form_submit_button("Generate & Save"):
                        with st.spinner("Generating..."):
                            prompt = f"Create a JD for {role_f}, {exp_f}yrs exp, Skills: {skills_f}. Context: {mission_f}"
                            res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}])
                            st.session_state.admin_jd_list.append({
                                "name": role_f,
                                "content": res.choices[0].message.content,
                                "job_type": "Full-time",
                                "date_posted": date.today().strftime("%Y-%m-%d")
                            })
                            st.success("AI JD Saved!")

        with view_tab:
            if not st.session_state.admin_jd_list: st.info("No active JDs.")
            for i, jd in enumerate(st.session_state.admin_jd_list):
                with st.container(border=True):
                    c1, c2 = st.columns([5, 1])
                    c1.subheader(jd['name'])
                    if c2.button("🗑️", key=f"del_{i}"):
                        st.session_state.admin_jd_list.pop(i)
                        st.rerun()
                    with st.expander("View"): st.write(jd['content'])

    # --- TAB 2: Upload the CVs ---
    with tab_upload_cvs:
        st.header("Candidate CV Management")
        cv_ind, cv_bulk, cv_bank = st.tabs(["👤 Individual", "📚 Bulk", "💾 Digital CV Bank"])
        
        with cv_ind:
            ind_file = st.file_uploader("Select CV", type=["pdf", "docx", "txt"], key="ind_cv")
            if st.button("Upload CV", key="btn_ind"):
                if ind_file:
                    content = get_file_content(ind_file)
                    st.session_state.company_cv_bank.append({
                        "File Name": ind_file.name, "Content": content, "Upload Type": "Individual", 
                        "Date Uploaded": date.today().strftime("%Y-%m-%d")
                    })
                    st.success("Uploaded!")

        with cv_bulk:
            bulk_files = st.file_uploader("Select Multiple CVs", type=["pdf", "docx", "txt"], accept_multiple_files=True, key="bulk_cv")
            if st.button("Upload All", key="btn_bulk"):
                if bulk_files:
                    for f in bulk_files:
                        content = get_file_content(f)
                        st.session_state.company_cv_bank.append({
                            "File Name": f.name, "Content": content, "Upload Type": "Bulk", 
                            "Date Uploaded": date.today().strftime("%Y-%m-%d")
                        })
                    st.success(f"{len(bulk_files)} CVs Uploaded!")

        with cv_bank:
            if st.session_state.company_cv_bank:
                st.dataframe(pd.DataFrame(st.session_state.company_cv_bank)[["File Name", "Date Uploaded"]], use_container_width=True)
                if st.button("Clear Bank"):
                    st.session_state.company_cv_bank = []
                    st.rerun()
            else: st.info("Empty Bank.")

    # --- TAB 3: Explore CV ---
    with tab_explore_cv:
        st.header("Explore CVs")
        if not st.session_state.company_cv_bank:
            st.warning("Upload CVs first.")
        else:
            exp_tabs = st.tabs(["Filter", "LLM", "Query", "Organize", "Summarise"])
            with exp_tabs[0]:
                kw = st.text_input("Keyword Search")
                if st.button("Filter"):
                    res = [cv for cv in st.session_state.company_cv_bank if kw.lower() in cv.get('Content','').lower()]
                    st.write(f"Found {len(res)}")
                    if res: st.dataframe(pd.DataFrame(res)[["File Name", "Date Uploaded"]])
            
            with exp_tabs[4]: # Summarise
                cv_sel = st.selectbox("Select CV", [cv['File Name'] for cv in st.session_state.company_cv_bank])
                if st.button("Summarize"):
                    target = next(c for c in st.session_state.company_cv_bank if c['File Name'] == cv_sel)
                    res = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role":"user", "content": f"Summarize:\n{target['Content'][:3000]}"}])
                    st.write(res.choices[0].message.content)

    # --- TAB 4: For Specific JD ---
    with tab_specific_jd:
        st.header("Match CVs to JD")
        if not st.session_state.company_cv_bank or not st.session_state.admin_jd_list:
            st.warning("Need both CVs and JDs.")
        else:
            jd_sel = st.selectbox("Select JD", [jd['name'] for jd in st.session_state.admin_jd_list])
            sel_jd_ content = next(jd['content'] for jd in st.session_state.admin_jd_list if jd['name'] == jd_sel)
            
            if st.button("🚀 Match & Rank"):
                results = []
                prog = st.progress(0)
                for i, cv in enumerate(st.session_state.company_cv_bank):
                    anl = evaluate_cv_against_jd_swot(cv.get('Content',''), sel_jd_content)
                    if "error" not in anl:
                        results.append({
                            "Name": anl.get('contact_info',{}).get('name','Unknown'),
                            "Email": anl.get('contact_info',{}).get('email','N/A'),
                            "Phone": anl.get('contact_info',{}).get('phone','N/A'),
                            "Match Score": anl.get('match_score', 0),
                            "Summary": anl.get('summary',''),
                            "SWOT": anl.get('swot',{}),
                            "CV Link": f"https://drive.google.com/search?q={cv['File Name']}" # Mock Link
                        })
                    prog.progress((i+1)/len(st.session_state.company_cv_bank))
                
                results.sort(key=lambda x: x['Match Score'], reverse=True)
                st.session_state.match_results_cache = results
                st.success("Done!")

            if st.session_state.match_results_cache:
                df = pd.DataFrame(st.session_state.match_results_cache)
                st.dataframe(df[["Name", "Match Score", "Email", "Summary"]], use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button("📥 Download Results CSV", csv, "matches.csv", "text/csv")

                for r in st.session_state.match_results_cache:
                    with st.expander(f"{r['Match Score']}% - {r['Name']}"):
                        st.write(f"**Strengths:** {', '.join(r['SWOT'].get('strengths',[]))}")
                        st.write(f"**Weaknesses:** {', '.join(r['SWOT'].get('weaknesses',[]))}")

    # --- TAB 5: Screen & Schedule (NEW) ---
    with tab_screening:
        st.header("🕵️ Screening & Scheduling")
        
        screen_ conduct, screen_manage, screen_export = st.tabs(["Conduct Screening", "Rank & Schedule", "Export Data"])
        
        # 1. Conduct Screening Form
        with screen_ conduct:
            if not st.session_state.company_cv_bank:
                st.warning("Upload CVs to start screening.")
            else:
                col_sel_cand, col_sel_jd = st.columns(2)
                with col_sel_cand:
                    cand_names = [cv['File Name'] for cv in st.session_state.company_cv_bank]
                    target_cand_file = st.selectbox("Select Candidate", cand_names)
                with col_sel_jd:
                    jd_opts = [jd['name'] for jd in st.session_state.admin_jd_list]
                    target_jd_name = st.selectbox("Select Position (JD)", jd_opts) if jd_opts else None

                st.markdown("### 📝 Profile & Basic Details")
                with st.form("screening_form"):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        curr_comp = st.text_input("Current Company")
                        curr_ctc = st.text_input("Current Salary (CTC)")
                    with c2:
                        exp_ctc = st.text_input("Expected Salary")
                        notice = st.selectbox("Notice Period", ["Immediate", "15 Days", "30 Days", "60 Days", "90 Days"])
                    with c3:
                        buyout = st.radio("Buyout Option Available?", ["Yes", "No"])
                        loc_pref = st.text_input("Current & Pref. Location")

                    st.markdown("### 🧠 Technical Quiz & Experience")
                    tech_exp = st.text_area("Duration of experience in Key Skills (e.g. Python: 3y, AWS: 2y)")
                    projects_brief = st.text_area("Brief on Key Projects Done (Type of projects)")
                    roles_resp = st.text_area("Key Roles & Responsibilities across companies")
                    achievements = st.text_area("Key Achievements")

                    submitted = st.form_submit_button("Submit & Evaluate Candidate")
                    
                    if submitted and target_jd_name:
                        # Find JD content
                        jd_txt = next(j['content'] for j in st.session_state.admin_jd_list if j['name'] == target_jd_name)
                        
                        # Prepare data payload
                        screen_payload = {
                            "candidate_file": target_cand_file,
                            "applied_for": target_jd_name,
                            "curr_ctc": curr_ctc, "exp_ctc": exp_ctc, "notice": notice, "buyout": buyout,
                            "tech_exp": tech_exp, "projects": projects_brief, "roles": roles_resp
                        }
                        
                        with st.spinner("AI is evaluating screening responses..."):
                            # Get Name/Email/Phone from CV Content using Regex or Mock
                            target_cv_content = next(c['Content'] for c in st.session_state.company_cv_bank if c['File Name'] == target_cand_file)
                            
                            # Simple extraction for demo (In prod, use LLM or specific regex)
                            name_match = re.search(r"Name:\s*(.*)", target_cv_content, re.IGNORECASE)
                            cand_real_name = name_match.group(1) if name_match else target_cand_file.split('.')[0]
                            
                            # AI Evaluation
                            eval_res = evaluate_screening_data(screen_payload, jd_txt)
                            
                            # Save result
                            final_record = {
                                "Name": cand_real_name,
                                "Applied Role": target_jd_name,
                                "Screening Score": eval_res.get('screening_score', 0),
                                "Recommendation": eval_res.get('recommendation', 'N/A'),
                                "Reasoning": eval_res.get('reasoning', ''),
                                "Email": "extracted@example.com", # Placeholder
                                "Phone": "+91 98765 43210", # Placeholder
                                "CV Link": f"https://drive.google.com/file/d/{target_cand_file}", # Mock Drive Link
                                "Profile Summary": f"Exp: {tech_exp[:50]}... | Notice: {notice}",
                                "Status": "Screened"
                            }
                            st.session_state.screened_candidates.append(final_record)
                            st.success(f"Candidate Evaluated! Score: {final_record['Screening Score']}/100 - {final_record['Recommendation']}")

        # 2. Rank & Schedule
        with screen_manage:
            st.subheader("Manage Screened Candidates")
            if not st.session_state.screened_candidates:
                st.info("No candidates screened yet.")
            else:
                # Convert to DF for sorting/filtering
                df_screen = pd.DataFrame(st.session_state.screened_candidates)
                df_screen = df_screen.sort_values(by="Screening Score", ascending=False)
                
                # Display Interactive Table
                st.dataframe(
                    df_screen[["Name", "Applied Role", "Screening Score", "Recommendation", "Notice Period", "Expected Salary"]],
                    use_container_width=True
                )
                
                # Action Buttons for Top Candidate
                st.markdown("### Actions")
                c1, c2 = st.columns(2)
                with c1:
                    cand_to_action = st.selectbox("Select Candidate to Action", df_screen["Name"].unique())
                
                with c2:
                    st.write("") # Spacer
                    st.write("") 
                    action_type = st.selectbox("Action Type", ["Schedule Tech Round", "Schedule F2F", "Schedule AI Interview"])
                
                if st.button(f"📅 Send Invite ({action_type})"):
                    # Mock Agentic Action
                    st.toast(f"✅ Agent Activated: Email sent to {cand_to_action} for {action_type}. Calendar blocked.")
                    st.balloons()

        # 3. Export Data
        with screen_export:
            st.subheader("Download Reports")
            if st.session_state.screened_candidates:
                df_export = pd.DataFrame(st.session_state.screened_candidates)
                csv_data = df_export.to_csv(index=False).encode('utf-8')
                
                st.download_button(
                    label="📥 Download Screened Candidates (CSV)",
                    data=csv_data,
                    file_name="Screened_Candidates_Report.csv",
                    mime="text/csv"
                )
                st.write("Includes: Name, Contact, Match Score, Profile Brief, and Drive Links.")
            else:
                st.warning("No data to export.")

    # --- TAB 6: Analytics ---
    with tab_stats:
        st.header("Overview")
        m1, m2 = st.columns(2)
        m1.metric("CVs in Bank", len(st.session_state.company_cv_bank))
        m2.metric("Candidates Screened", len(st.session_state.screened_candidates))
