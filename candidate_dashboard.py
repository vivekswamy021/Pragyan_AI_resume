import streamlit as st
import os
import json
import re 
from datetime import date 
import traceback
import tempfile
from groq import Groq 
import openpyxl 
from streamlit.runtime.uploaded_file_manager import UploadedFile 
from io import BytesIO

# --- CONFIGURATION ---
GROQ_MODEL = "llama-3.1-8b-instant"
question_section_options = ["skills","experience", "certifications", "projects", "education"] 
DEFAULT_JOB_TYPES = ["Full-time", "Contract", "Internship", "Remote", "Part-time"]
DEFAULT_ROLES = ["Software Engineer", "Data Scientist", "Product Manager", "HR Manager", "Marketing Specialist", "Operations Analyst"]

# --- GLOBAL API/UTILITY FUNCTIONS ---

# Global client and key placeholder (will be initialized in main)
GROQ_API_KEY = ""
client = None
# Mock client class if key is missing to prevent errors during object instantiation
class MockGroqClient:
    def chat(self):
        class Completions:
            def create(self, **kwargs):
                raise ValueError("GROQ_API_KEY not set. AI functions disabled.")
        return Completions()

# 1. Page Navigation
def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def clear_interview_state():
    """Clears all generated questions, answers, and the evaluation report."""
    st.session_state.interview_qa = []
    st.session_state.iq_output = ""
    st.session_state.evaluation_report = ""
    st.toast("Practice answers cleared.")

# 2. File/LLM Utility Helpers 
def dump_to_excel(parsed_json):
    """Dumps parsed JSON data to an Excel file in memory (BytesIO)."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Profile Data"
    ws.append(["Category", "Details"])
    section_order = ['name', 'email', 'phone', 'github', 'linkedin', 'experience', 'education', 'skills', 'projects', 'certifications', 'strength', 'personal_details']
    
    for section_key in section_order:
        if section_key in parsed_json and parsed_json[section_key]:
            content = parsed_json[section_key]
            
            # Simple values (Name, Email)
            if not isinstance(content, list) and not isinstance(content, dict):
                 ws.append([section_key.replace('_', ' ').title(), str(content)])
                 
            # List values (Skills, Experience)
            elif isinstance(content, list):
                ws.append([section_key.replace('_', ' ').title(), f"({len(content)} entries)"])
                for item in content:
                    ws.append(["", str(item)])

    bio = BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio.getvalue()

def get_file_type(file_name):
    """Identifies the file type based on its extension."""
    ext = os.path.splitext(file_name)[1].lower().strip('.')
    if ext in ['pdf', 'docx', 'xlsx', 'txt', 'json', 'md']: return ext
    else: return 'txt'

def extract_content(file_input):
    """Extracts text content from uploaded file (simplified for this context)."""
    try:
        # For actual implementation, use libraries like pdfplumber/python-docx here
        return file_input.getvalue().decode("utf-8", errors="ignore")
    except Exception:
        return f"[Simulated Content Extraction Failed for {file_input.name}]"
    
@st.cache_data(show_spinner="Analyzing content with Groq LLM...")
def parse_with_llm(text, return_type='json'):
    """Mocks sending resume text to the LLM for structured information extraction."""
    if not GROQ_API_KEY:
        st.error("AI functionality disabled: GROQ_API_KEY not set.")
        return {"error": "GROQ_API_KEY not set.", "raw_output": text}
    
    # Minimal mock data for functionality without a live API call
    mock_data = {
        "name": "Alex Candidate", 
        "email": "alex@example.com", 
        "phone": "555-1234",
        "skills": ["Python", "Streamlit", "SQL", "Project Management"],
        "experience": ["3 years at TechCorp (Senior Dev)", "2 years at StartupX (Data Analyst)"],
        "education": ["M.S. Computer Science"],
        "certifications": ["AWS Certified Developer"],
        "projects": ["AI Dashboard App", "E-commerce Tracker"],
        "strength": ["Problem Solver", "Team Player"],
        "personal_details": "Highly motivated individual."
    }
    
    try:
        # In a real app, you'd make the client.chat.completions.create call here
        # For this complete code snippet, we'll return the mock data for speed and stability
        # response = client.chat.completions.create(...)
        return mock_data
    except Exception as e:
        return {"error": f"LLM parsing failed: {e}", "raw_output": text}


def parse_and_store_resume(file_input, source_type='file'):
    """Handles file/text input, parsing, and stores results."""
    
    if source_type == 'file':
        text = extract_content(file_input)
        file_name = file_input.name.split('.')[0]
    else: # source_type == 'text'
        text = file_input
        file_name = f"Pasted Text ({date.today().strftime('%Y-%m-%d')})"
    
    parsed = parse_with_llm(text, return_type='json')
    
    if "error" in parsed:
        return {"error": parsed.get('error', 'Unknown error'), "full_text": text, "name": file_name}
    
    excel_data = dump_to_excel(parsed)
    final_name = parsed.get('name', file_name)

    return {
        "parsed": parsed,
        "full_text": text,
        "excel_data": excel_data,
        "name": final_name
    }

@st.cache_data(show_spinner="Extracting JD metadata...")
def extract_jd_metadata(jd_text):
    """Mocks extraction of structured metadata (Role, Job Type, Key Skills) from raw JD text."""
    if not GROQ_API_KEY:
        return {"role": "N/A", "job_type": "N/A", "key_skills": []}
    
    # Simple mock extraction
    role_match = re.search(r'Role:\s*([^\n]+)', jd_text, re.IGNORECASE)
    role = role_match.group(1).strip() if role_match else "General Analyst"
    
    return {"role": role, "job_type": "Full-time", "key_skills": ["SQL", "Python", "Teamwork"]}

def extract_jd_from_linkedin_url(url: str) -> str:
    """Simulates JD content extraction from a LinkedIn URL."""
    job_title = "Data Scientist"
    try:
        match = re.search(r'/jobs/view/([^/]+)', url) or re.search(r'/jobs/(\w+)', url)
        if match:
            job_title = match.group(1).split('?')[0].replace('-', ' ').title()
    except:
        pass
        
    return f"--- Simulated JD for: {job_title} ---\n**Role:** {job_title}\n**Requirements:** 3+ years experience, Python, SQL, Cloud Architecture.\n--- End Simulated JD ---"

@st.cache_data(show_spinner="Evaluating JD fit...")
def evaluate_jd_fit(job_description, parsed_json):
    """Mocks evaluation of resume fit against a job description."""
    if not GROQ_API_KEY: return "AI Evaluation Disabled."
    
    # Mock scores based on the assumed candidate skills
    score = 8 
    skills = 90
    exp = 75
    edu = 95

    return f"""## **Job Fit Analysis Report**

**Overall Fit Score:** [{score}]/10

--- 
### **Section Match Analysis**
* **Skills Match:** [{skills}]% (High)
* **Experience Match:** [{exp}]% (Good)
* **Education Match:** [{edu}]% (Excellent)

---
### **Strengths/Matches (Based on Resume)**
* Strong overlap in **Python** and **SQL** skills, directly meeting primary JD requirements.
* Relevant professional experience (Senior Dev/Data Analyst) aligns with the required seniority level.

### **Gaps/Areas for Improvement**
* The JD mentions **Cloud Architecture**, which is not explicitly listed in the 'Certifications' section. Recommend adding relevant cloud experience to the resume.

**Overall Summary:** A **strong candidate** with highly relevant technical skills. Focus on elaborating cloud architecture experience during the interview.
"""

def generate_interview_questions(parsed_json, section):
    """Mocks generation of categorized interview questions using LLM."""
    if not GROQ_API_KEY: return "AI Functions Disabled."
    
    return f"""[Behavioral]
Q1: Describe a challenging project where you had to use your **{section}** skills.
Q2: Give an example of a time you received constructive criticism on your **{section}** approach and how you responded.
[Technical/Deep Dive]
Q3: Detail the architecture of your 'AI Dashboard App' project and the specific **{section}** libraries you utilized.
Q4: If you were to start your **{section}** journey over, what is one thing you would learn earlier?
[Experience]
Q5: Elaborate on your biggest achievement at TechCorp related to **{section}**.
"""

def evaluate_interview_answers(qa_list, parsed_json):
    """Mocks evaluation of the user's answers against the resume content."""
    if not GROQ_API_KEY: return "AI Evaluation Disabled."
    
    q1 = qa_list[0]['question']
    a1 = qa_list[0]['answer'] if qa_list and qa_list[0]['answer'] else "[No Answer Provided]"
    
    return f"""## **AI Interview Evaluation Report**

### **Question 1 (Example):** {q1}
**Candidate Answer:** "{a1[:50]}..."
**Score:** 9/10
**Feedback:**
-   **Clarity & Accuracy:** The answer was precise and highly consistent with the 'Project Management' skill listed on the resume. Excellent use of the STAR method.
-   **Gaps & Improvements:** Ensure project outcomes are quantified with metrics (e.g., "saved 10 hours per week").

---
### **Final Assessment**
**Consistency with Resume:** High.
**Overall Recommendation:** The candidate is well-prepared, articulate, and demonstrates deep knowledge aligned with their profile.
"""

def qa_on_resume(question):
    """Mocks Chatbot for Resume (Q&A) using LLM."""
    if not GROQ_API_KEY: return "AI Chatbot Disabled: GROQ_API_KEY not set."
    
    return f"**AI Answer:** The resume indicates proficiency in **Python, SQL, and Streamlit**. It also lists 3 years of experience as a Senior Developer at TechCorp. The most relevant section for this question has been analyzed."

def qa_on_jd(question, selected_jd_name):
    """Mocks Chatbot for JD (Q&A) using LLM."""
    if not GROQ_API_KEY: return "AI Chatbot Disabled: GROQ_API_KEY not set."

    return f"**AI Answer:** The Job Description for '{selected_jd_name}' clearly states the primary technology requirements are **Python** and **SQL** for data processing, and experience with **Cloud Architecture** is highly desirable."


# --- UI HELPERS ---

def generate_cv_html(parsed_data):
    """Generates a simple, print-friendly HTML string from parsed data for PDF conversion."""
    css = """
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }
        .header { background-color: #f4f4f4; padding: 10px; margin-bottom: 20px; border-radius: 5px; }
        h1, h2 { color: #333; }
        h1 { border-bottom: 3px solid #ccc; padding-bottom: 5px; }
        .section { margin-bottom: 15px; }
        .item { margin-left: 20px; }
    </style>
    """
    
    html_content = f"<html><head>{css}<title>{parsed_data.get('name', 'CV')}</title></head><body>"
    
    # Header
    html_content += f'<div class="header"><h1>{parsed_data.get("name", "Candidate Name")}</h1>'
    html_content += f'<p>Email: {parsed_data.get("email", "")} | Phone: {parsed_data.get("phone", "")}</p></div>'
    
    # Skills
    html_content += '<div class="section"><h2>Skills</h2><ul>'
    for skill in parsed_data.get('skills', []):
         html_content += f'<li>{skill}</li>'
    html_content += '</ul></div>'
    
    # Experience (Simplified)
    html_content += '<div class="section"><h2>Experience</h2><ul>'
    for exp in parsed_data.get('experience', []):
         html_content += f'<li>{exp}</li>'
    html_content += '</ul></div>'

    html_content += '</body></html>'
    return html_content

def format_parsed_json_to_markdown(parsed_data):
    """Formats the parsed JSON data into a clean, CV-like Markdown structure."""
    md = f"# **{parsed_data.get('name', 'CANDIDATE NAME')}**\n\n"
    
    # Contact
    md += f"**{parsed_data.get('email', 'N/A')}** | **{parsed_data.get('phone', 'N/A')}**\n"
    
    # Skills
    md += "\n## **SKILLS**\n---\n"
    md += " | ".join(parsed_data.get('skills', ['No Skills Listed']))
    
    # Experience
    md += "\n\n## **EXPERIENCE**\n---\n"
    for exp in parsed_data.get('experience', []):
         md += f"* **{exp}**\n"

    md += "\n\n(Generated from Parsed Data)\n"
    return md

# --- TAB CONTENT FUNCTIONS (DEPENDENCIES) ---

def cv_management_tab_content():
    """Content for the CV Management tab (Form and Preview)."""
    st.header("📝 Prepare Your CV")
    st.markdown("### 1. Form Based CV Builder")
    st.info("Fill out the details below, or use the 'Resume Parsing' tab to load data from a file.")

    default_parsed = {
        "name": "", "email": "", "phone": "", "linkedin": "", "github": "",
        "skills": [], "experience": [], "education": [], "certifications": [], 
        "projects": [], "strength": [], "personal_details": ""
    }
    
    if "cv_form_data" not in st.session_state:
        # Load existing parsed data if available
        st.session_state.cv_form_data = st.session_state.get('parsed', default_parsed).copy()
    
    with st.form("cv_builder_form"):
        st.subheader("Personal & Contact Details")
        
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.cv_form_data['name'] = st.text_input(
                "Full Name", value=st.session_state.cv_form_data.get('name', ''), key="cv_name"
            )
        with col2:
            st.session_state.cv_form_data['email'] = st.text_input(
                "Email Address", value=st.session_state.cv_form_data.get('email', ''), key="cv_email"
            )
        
        st.markdown("---")
        st.subheader("Technical Sections (One Item per Line)")

        # Handle list fields for text area
        skills_text = "\n".join(st.session_state.cv_form_data.get('skills', []))
        new_skills_text = st.text_area(
            "Key Skills (Technical and Soft)", value=skills_text, height=100, key="cv_skills"
        )
        st.session_state.cv_form_data['skills'] = [s.strip() for s in new_skills_text.split('\n') if s.strip()]
        
        # Experience
        exp_text = "\n".join(st.session_state.cv_form_data.get('experience', []))
        new_exp_text = st.text_area(
            "Experience (Role, Company, Dates)", value=exp_text, height=100, key="cv_experience"
        )
        st.session_state.cv_form_data['experience'] = [s.strip() for s in new_exp_text.split('\n') if s.strip()]
        
        submit_form_button = st.form_submit_button("Generate and Load CV Data", type="primary", use_container_width=True)

    if submit_form_button:
        if not st.session_state.cv_form_data['name'] or not st.session_state.cv_form_data['email']:
            st.error("Please fill in at least your **Full Name** and **Email Address**.")
            return

        # Update the main parsed state with the form data
        st.session_state.parsed = st.session_state.cv_form_data.copy()
        # Reset dependent states
        st.session_state.candidate_match_results = []
        clear_interview_state()

        st.success(f"✅ CV data for **{st.session_state.parsed['name']}** successfully generated and loaded!")
        
    st.markdown("---")
    st.subheader("2. Loaded CV Data Preview and Download")
    
    if st.session_state.get('parsed', {}).get('name'):
        
        filled_data_for_preview = st.session_state.parsed 
        
        tab_markdown, tab_json, tab_excel, tab_pdf = st.tabs(["📝 Markdown View", "💾 JSON View", "📊 Excel Download", "⬇️ HTML/PDF Download"])

        with tab_markdown:
            cv_markdown_preview = format_parsed_json_to_markdown(filled_data_for_preview)
            st.markdown(cv_markdown_preview)

        with tab_json:
            st.json(st.session_state.parsed)
            
        with tab_excel:
            excel_data_bytes = dump_to_excel(st.session_state.parsed)
            st.download_button(
                label="⬇️ Download CV Data as Excel (xlsx)",
                data=excel_data_bytes,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_Data.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_data"
            )

        with tab_pdf:
            st.info("Download HTML for Print-to-PDF conversion (best quality).")
            html_output = generate_cv_html(filled_data_for_preview)
            st.download_button(
                label="⬇️ Download CV as Print-Ready HTML File",
                data=html_output,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_CV_Document.html",
                mime="text/html",
                key="download_cv_html"
            )
    else:
        st.info("Please fill out the form above or parse a resume to see the preview.")


def filter_jd_tab_content():
    """Content for the Filter JD tab."""
    st.header("🔍 Filter Job Descriptions by Criteria")
    st.markdown("Use the filters below to narrow down your saved Job Descriptions.")

    if not st.session_state.candidate_jd_list:
        st.info("No Job Descriptions are currently loaded. Please add JDs in the 'JD Management' tab.")
        if 'filtered_jds_display' not in st.session_state:
            st.session_state.filtered_jds_display = []
        return
    
    # Dynamic options for filters
    unique_roles = sorted(list(set(
        [item.get('role', 'General Analyst') for item in st.session_state.candidate_jd_list] + DEFAULT_ROLES
    )))
    unique_job_types = sorted(list(set(
        [item.get('job_type', 'Full-time') for item in st.session_state.candidate_jd_list] + DEFAULT_JOB_TYPES
    )))
    
    all_skills = set()
    for jd in st.session_state.candidate_jd_list:
        all_skills.update(jd.get('key_skills', []))
    unique_skills_list = sorted(list(all_skills))

    all_jd_data = st.session_state.candidate_jd_list

    with st.form(key="jd_filter_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_skills = st.multiselect("Skills Keywords", options=unique_skills_list, default=st.session_state.get('last_selected_skills', []), key="candidate_filter_skills_multiselect")
        with col2:
            selected_job_type = st.selectbox("Job Type", options=["All Job Types"] + unique_job_types, index=0, key="filter_job_type_select")
        with col3:
            selected_role = st.selectbox("Role Title", options=["All Roles"] + unique_roles, index=0, key="filter_role_select")

        apply_filters_button = st.form_submit_button("✅ Apply Filters", type="primary", use_container_width=True)

    if apply_filters_button:
        st.session_state.last_selected_skills = selected_skills

        # Filtering Logic
        filtered_jds = [
            jd for jd in all_jd_data
            if (selected_role == "All Roles" or selected_role == jd.get('role', '')) and
               (selected_job_type == "All Job Types" or selected_job_type == jd.get('job_type', '')) and
               (not selected_skills or all(s.lower() in [ks.lower() for ks in jd.get('key_skills',[])] for s in selected_skills))
        ]
                
        st.session_state.filtered_jds_display = filtered_jds
        st.success(f"Filter applied! Found **{len(filtered_jds)}** matching Job Descriptions.")

    st.markdown("---")
    
    filtered_jds = st.session_state.get('filtered_jds_display', [])
    
    st.subheader(f"Matching Job Descriptions ({len(filtered_jds)} found)")
    
    if filtered_jds:
        display_data = []
        for jd in filtered_jds:
            display_data.append({
                "Job Description Title": jd['name'].replace("--- Simulated JD for: ", ""),
                "Role": jd.get('role', 'N/A'),
                "Job Type": jd.get('job_type', 'N/A'),
                "Key Skills (Top 3)": ", ".join(jd.get('key_skills', ['N/A'])[:3]) + "...",
            })
            
        st.dataframe(display_data, use_container_width=True)

    elif st.session_state.candidate_jd_list and apply_filters_button:
        st.info("No Job Descriptions match the selected criteria. Try adjusting your filters.")
    elif st.session_state.candidate_jd_list and not apply_filters_button:
        st.info("Use the filters above and click **'Apply Filters'** to view matching Job Descriptions.")

# --- CANDIDATE DASHBOARD FUNCTION ---

def candidate_dashboard():
    st.header("👩‍🎓 Candidate AI Dashboard")
    st.markdown("Welcome! Use the tabs below to manage your CV and access AI preparation tools.")

    # --- Navigation ---
    if st.button("🚪 Log Out", key="candidate_logout_btn"):
        go_to("login") 
    
    # --- Sidebar ---
    with st.sidebar:
        st.header("Resume/CV Status")
        if st.session_state.parsed.get("name"):
            st.success(f"Currently loaded: **{st.session_state.parsed['name']}**")
        else:
            st.info("Please upload a file or use the CV builder in 'CV Management' to begin.")
        
        st.markdown("---")
        st.header("JD Count")
        st.info(f"Saved Job Descriptions: **{len(st.session_state.candidate_jd_list)}**")


    # Main Content Tabs (The requested updated order)
    tab_cv_mgmt, tab_parsing, tab_jd_mgmt, tab_batch_match, tab_filter_jd, tab_chatbot, tab_interview_prep = st.tabs([
        "✍️ CV Management", 
        "📄 Resume Parsing", 
        "📚 JD Management", 
        "🎯 Batch JD Match",
        "🔍 Filter JD",
        "💬 Resume/JD Chatbot (Q&A)", 
        "❓ Interview Prep"            
    ])
    
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name'))
    
    # --- TAB 1: CV Management ---
    with tab_cv_mgmt:
        cv_management_tab_content()

    # --- TAB 2: Resume Parsing ---
    with tab_parsing:
        st.header("Resume Upload and Parsing")
        
        input_method = st.radio(
            "Select Input Method",
            ["Upload File", "Paste Text"],
            key="parsing_input_method",
            horizontal=True
        )
        
        st.markdown("---")
        
        uploaded_file = None
        pasted_text = ""

        if input_method == "Upload File":
            st.markdown("### 1. Upload Resume File") 
            uploaded_file = st.file_uploader( 
                "Choose PDF, DOCX, TXT, or other file formats.", 
                type=["pdf", "docx", "txt", "json", "md", "csv", "xlsx"], 
                accept_multiple_files=False, 
                key='candidate_file_upload_main'
            )
            
            file_to_parse = uploaded_file
            
            st.markdown("### 2. Parse Uploaded File")
            
            if file_to_parse:
                if st.button(f"Parse and Load: **{file_to_parse.name}**", type="primary", use_container_width=True):
                    with st.spinner(f"Parsing {file_to_parse.name} with AI..."):
                        result = parse_and_store_resume(file_to_parse, source_type='file')
                        
                        if "error" not in result:
                            st.session_state.parsed = result['parsed']
                            st.session_state.full_text = result['full_text']
                            clear_interview_state()
                            st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                        else:
                            st.error(f"Parsing failed for {file_to_parse.name}: {result['error']}")
                            st.session_state.parsed = {"error": result['error'], "name": result['name']}
            else:
                st.info("No resume file is currently uploaded.")

        else: # Paste Text
            st.markdown("### 1. Paste Your CV Text")
            pasted_text = st.text_area(
                "Copy and paste your entire CV or resume text here.",
                value=st.session_state.get('pasted_cv_text', ''),
                height=300,
                key='pasted_cv_text_input'
            )
            st.session_state.pasted_cv_text = pasted_text 
            
            st.markdown("---")
            st.markdown("### 2. Parse Pasted Text")
            
            if pasted_text.strip():
                if st.button("Parse and Load Pasted Text", type="primary", use_container_width=True):
                    with st.spinner("Parsing pasted text with AI..."):
                        result = parse_and_store_resume(pasted_text, source_type='text')
                        
                        if "error" not in result:
                            st.session_state.parsed = result['parsed']
                            st.session_state.full_text = result['full_text']
                            clear_interview_state()
                            st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                        else:
                            st.error(f"Parsing failed: {result['error']}")
                            st.session_state.parsed = {"error": result['error'], "name": result['name']}
            else:
                st.info("Please paste your CV text into the box above.")

    # --- TAB 3: JD Management ---
    with tab_jd_mgmt:
        st.header("📚 Manage Job Descriptions for Matching")
        
        if "candidate_jd_list" not in st.session_state:
             st.session_state.candidate_jd_list = []
        
        method = st.radio("Choose Input Method", ["Paste Text", "LinkedIn URL"], key="jd_add_method_candidate", horizontal=True) 

        col_input, col_button = st.columns([3, 1])

        if method == "LinkedIn URL":
            url_input = col_input.text_input("Enter LinkedIn Job URL(s) (one per line or comma-separated)", key="url_list_candidate")
            
            if col_button.button("Add JD(s) from URL", key="add_jd_url_btn_candidate", use_container_width=True, type="primary"):
                urls = [u.strip() for u in re.split(r'[\n,]', url_input) if u.strip()]
                if not urls:
                    st.warning("Please enter at least one URL.")
                else:
                    new_jds_count = 0
                    for url in urls:
                        jd_text = extract_jd_from_linkedin_url(url)
                        metadata = extract_jd_metadata(jd_text)
                        
                        # Generate a unique name
                        name_base = url.split('/')[-1].split('?')[0].replace('-', ' ').title()
                        name = f"JD: {name_base} ({date.today().strftime('%m/%d')})" 
                        
                        st.session_state.candidate_jd_list.append({"name": name, "content": jd_text, **metadata}) 
                        new_jds_count += 1
                    st.success(f"✅ {new_jds_count} JD(s) added successfully!")
                    
        else: # Paste Text
            text_input = col_input.text_area("Paste Full Job Description Text Here", key="jd_text_input_candidate", height=150)
            
            if col_button.button("Add JD from Text", key="add_jd_text_btn_candidate", use_container_width=True, type="primary"):
                if not text_input.strip():
                    st.warning("Please paste the JD text.")
                else:
                    metadata = extract_jd_metadata(text_input)
                    role_name = metadata.get('role', 'Untitled JD')
                    jd_name = f"JD: {role_name} ({date.today().strftime('%m/%d')})"
                    
                    st.session_state.candidate_jd_list.append({"name": jd_name, "content": text_input, **metadata}) 
                    st.success(f"✅ JD for **{role_name}** added successfully!")


        st.markdown("---")
        
        if st.session_state.candidate_jd_list:
            col_display_header, col_clear_button = st.columns([3, 1])
            with col_display_header:
                st.markdown("### ✅ Current Saved Job Descriptions:")
            with col_clear_button:
                if st.button("🗑️ Clear All JDs", key="clear_jds_candidate", help="Removes all saved JDs"):
                    st.session_state.candidate_jd_list = []
                    st.session_state.candidate_match_results = [] 
                    st.session_state.filtered_jds_display = [] 
                    st.success("All JDs cleared.")
                    st.rerun() 

            for idx, jd_item in enumerate(st.session_state.candidate_jd_list, 1):
                title = jd_item['name']
                with st.expander(f"JD {idx}: **{title}** | Type: {jd_item.get('job_type', 'N/A')}"):
                    st.markdown(f"**Role:** {jd_item.get('role', 'N/A')}")
                    st.markdown(f"**Key Skills:** {', '.join(jd_item.get('key_skills', ['N/A']))}")
                    st.text_area("JD Content Preview", jd_item['content'], height=150, key=f"jd_content_{idx}", disabled=True)
        else:
            st.info("No Job Descriptions added yet. Use the input methods above to save JDs for analysis.")

    # --- TAB 4: Batch JD Match ---
    with tab_batch_match:
        st.header("🎯 Batch JD Match: Best Matches")
        
        if not is_resume_parsed:
            st.warning("Prerequisite: Please **upload and parse your resume** first in the 'Resume Parsing' tab.")
        elif not st.session_state.candidate_jd_list:
            st.error("Prerequisite: Please **add Job Descriptions** first in the 'JD Management' tab.")
        elif not GROQ_API_KEY:
             st.error("Cannot use JD Match: GROQ_API_KEY is not configured.")
        else:
            if "candidate_match_results" not in st.session_state:
                st.session_state.candidate_match_results = []

            all_jd_names = [item['name'] for item in st.session_state.candidate_jd_list]
            selected_jd_names = st.multiselect(
                "Select Job Descriptions to Match Against",
                options=all_jd_names,
                default=all_jd_names, 
                key='candidate_batch_jd_select'
            )
            
            jds_to_match = [jd_item for jd_item in st.session_state.candidate_jd_list if jd_item['name'] in selected_jd_names]
            
            if st.button(f"Run Match Analysis on {len(jds_to_match)} Selected JD(s)", type="primary"):
                st.session_state.candidate_match_results = []
                if not jds_to_match: st.warning("No JDs selected.")
                else:
                    with st.spinner(f"Analyzing {len(jds_to_match)} JD(s) against {st.session_state.parsed['name']}..."):
                        results_with_score = []
                        for jd_item in jds_to_match:
                            fit_output = evaluate_jd_fit(jd_item['content'], st.session_state.parsed)
                            
                            # Simple extraction of the mock score
                            score_match = re.search(r'Overall Fit Score:\s*\[(\d+)]/10', fit_output)
                            score = score_match.group(1) if score_match else '5' # Default to 5 if not found
                            
                            results_with_score.append({
                                "jd_name": jd_item['name'],
                                "overall_score": score,
                                "numeric_score": int(score),
                                "full_analysis": fit_output
                            })
                            
                        results_with_score.sort(key=lambda x: x['numeric_score'], reverse=True)
                        for i, item in enumerate(results_with_score): item['Rank'] = i + 1 
                        st.session_state.candidate_match_results = results_with_score
                        st.success("Batch analysis complete!")

            if st.session_state.get('candidate_match_results'):
                st.markdown("#### **Ranked Match Results**")
                display_data = []
                for item in st.session_state.candidate_match_results:
                    full_jd_item = next((jd for jd in st.session_state.candidate_jd_list if jd['name'] == item['jd_name']), {})
                    display_data.append({
                        "Rank": item.get("Rank", "N/A"),
                        "Job Description": item["jd_name"],
                        "Role": full_jd_item.get('role', 'N/A'),
                        "Fit Score (out of 10)": item["overall_score"],
                    })
                
                # Show top 5 matches in a dataframe
                st.dataframe(display_data[:5], use_container_width=True)
                
                st.markdown("#### Detailed Reports")
                for item in st.session_state.candidate_match_results:
                     with st.expander(f"Rank {item.get('Rank', 'N/A')} | Report for **{item['jd_name']}** (Score: **{item['overall_score']}/10**)"):
                        st.markdown(item['full_analysis'])

    # --- TAB 5: Filter JD ---
    with tab_filter_jd:
        filter_jd_tab_content()

    # --- TAB 6: Resume/JD Chatbot (Q&A) ---
    with tab_chatbot:
        st.header("Resume/JD Chatbot (Q&A) 💬")
        
        if not GROQ_API_KEY:
             st.error("AI Chatbot disabled: GROQ_API_KEY is not configured.")
        else:
            sub_tab_resume, sub_tab_jd = st.tabs([
                "👤 Chat about Your Resume",
                "📄 Chat about Saved JDs"
            ])
            
            # --- RESUME CHATBOT ---
            with sub_tab_resume:
                st.markdown("### Ask any question about the currently loaded resume.")
                if not is_resume_parsed:
                    st.warning("Prerequisite: Parse resume in the 'Resume Parsing' tab.")
                else:
                    if 'qa_answer_resume' not in st.session_state: st.session_state.qa_answer_resume = ""
                    
                    question = st.text_input("Your Question (e.g., 'What are my top 3 skills?')", key="resume_qa_question")
                    
                    if st.button("Get Answer (Resume)", key="qa_btn_resume", type="primary"):
                        with st.spinner("Generating answer..."):
                            st.session_state.qa_answer_resume = qa_on_resume(question)

                    if st.session_state.get('qa_answer_resume'):
                        st.text_area("AI Answer", st.session_state.qa_answer_resume, height=150, disabled=True)
            
            # --- JD CHATBOT ---
            with sub_tab_jd:
                st.markdown("### Ask any question about a saved Job Description.")
                
                if not st.session_state.candidate_jd_list:
                    st.warning("Prerequisite: Add JDs in 'JD Management'.")
                else:
                    if 'qa_answer_jd' not in st.session_state: st.session_state.qa_answer_jd = ""

                    jd_names = [jd['name'] for jd in st.session_state.candidate_jd_list]
                    selected_jd_name = st.selectbox("Select JD to Query", options=jd_names, key="jd_qa_select")
                    
                    question = st.text_input("Your Question (e.g., 'What are the required years of experience?')", key="jd_qa_question")
                    
                    if st.button("Get Answer (JD)", key="qa_btn_jd", type="primary"):
                        if selected_jd_name and question.strip():
                            with st.spinner(f"Generating answer for {selected_jd_name}..."):
                                st.session_state.qa_answer_jd = qa_on_jd(question, selected_jd_name)
                        else:
                            st.error("Please select a JD and enter a question.")

                    if st.session_state.get('qa_answer_jd'):
                        st.text_area("AI Answer", st.session_state.qa_answer_jd, height=150, disabled=True)

    # --- TAB 7: Interview Prep ---
    with tab_interview_prep:
        st.header("Interview Preparation Tools")
        if not is_resume_parsed:
            st.warning("Prerequisite: Upload/Parse resume in the 'Resume Parsing' tab.")
        elif not GROQ_API_KEY:
             st.error("AI Interview Prep disabled: GROQ_API_KEY is not configured.")
        else:
            if 'iq_output' not in st.session_state: st.session_state.iq_output = ""
            if 'interview_qa' not in st.session_state: st.session_state.interview_qa = [] 
            if 'evaluation_report' not in st.session_state: st.session_state.evaluation_report = "" 
            
            st.subheader("1. Generate Interview Questions")
            
            section_choice = st.selectbox(
                "Select Resume Section to Focus On", 
                question_section_options, 
                key='iq_section_c',
                on_change=clear_interview_state 
            )
            
            if st.button("Generate Targeted Interview Questions", key='iq_btn_c', type="primary"):
                with st.spinner(f"Generating questions focused on your **{section_choice}**..."):
                    raw_questions_response = generate_interview_questions(st.session_state.parsed, section_choice)
                    
                    st.session_state.iq_output = raw_questions_response
                    st.session_state.evaluation_report = "" 
                    
                    # Parse the mock question output into a list of dicts
                    q_list = []
                    current_level = "General"
                    for line in raw_questions_response.splitlines():
                        if line.startswith('['): current_level = line.strip('[]')
                        elif line.lower().startswith('q') and ':' in line:
                            question_text = line[line.find(':') + 1:].strip()
                            q_list.append({"question": f"({current_level}) {question_text}", "answer": "", "level": current_level})
                    
                    st.session_state.interview_qa = q_list
                    st.success(f"Generated **{len(q_list)}** questions.")

            if st.session_state.get('interview_qa'):
                st.markdown("---")
                st.subheader("2. Practice and Record Answers")
                
                with st.form("interview_practice_form"):
                    for i, qa_item in enumerate(st.session_state.interview_qa):
                        st.markdown(f"**Question {i+1}:** *{qa_item['question']}*")
                        answer = st.text_area(f"Your Answer for Q{i+1}", value=st.session_state.interview_qa[i]['answer'], height=100, key=f'answer_q_{i}', label_visibility='collapsed')
                        st.session_state.interview_qa[i]['answer'] = answer 
                        st.markdown("---") 
                        
                    submit_button = st.form_submit_button("Submit & Get AI Evaluation", type="primary", use_container_width=True)

                    if submit_button:
                        if all(item['answer'].strip() for item in st.session_state.interview_qa):
                            with st.spinner("Sending answers to AI Evaluator..."):
                                report = evaluate_interview_answers(st.session_state.interview_qa, st.session_state.parsed)
                                st.session_state.evaluation_report = report
                                st.success("Evaluation complete! Scroll down for the report.")
                        else:
                            st.error("Please answer all generated questions before submitting for evaluation.")
                
                if st.session_state.get('evaluation_report'):
                    st.markdown("---")
                    st.subheader("3. AI Evaluation Report")
                    st.markdown(st.session_state.evaluation_report)

# --- INITIALIZATION AND MAIN APP ENTRY POINT ---

def initialize_session_state():
    """Initializes all necessary session state variables."""
    # Core app flow control
    if 'page' not in st.session_state:
        st.session_state.page = "candidate_dashboard" 
    
    # Candidate data state
    if 'parsed' not in st.session_state:
        st.session_state.parsed = {} 
    if 'full_text' not in st.session_state:
        st.session_state.full_text = ""
    if 'cv_form_data' not in st.session_state:
        st.session_state.cv_form_data = {}
        
    # JD state
    if 'candidate_jd_list' not in st.session_state:
        st.session_state.candidate_jd_list = [] 
    if 'candidate_match_results' not in st.session_state:
        st.session_state.candidate_match_results = []
    if 'filtered_jds_display' not in st.session_state:
        st.session_state.filtered_jds_display = []
        
    # Interview/Chat state
    if 'interview_qa' not in st.session_state:
        st.session_state.interview_qa = []
    if 'evaluation_report' not in st.session_state:
        st.session_state.evaluation_report = ""
    if 'pasted_cv_text' not in st.session_state:
        st.session_state.pasted_cv_text = ""
    if 'last_selected_skills' not in st.session_state:
        st.session_state.last_selected_skills = []


def main():
    """Main application loop."""
    st.set_page_config(layout="wide", page_title="Candidate AI Dashboard")
    initialize_session_state()

    # Access API Key and initialize client
    global GROQ_API_KEY, client
    try:
        # Check environment variable (for local/testing)
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY") 
        # Check Streamlit secrets (for cloud deployment)
        if not GROQ_API_KEY and 'GROQ_API_KEY' in st.secrets:
            GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
    except:
        GROQ_API_KEY = "" # Ensure it's empty if secrets access fails

    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
    else:
        client = MockGroqClient() # Use mock client to prevent crash on instantiation

    
    # --- Navigation Logic (Simplified) ---
    if st.session_state.page == "candidate_dashboard":
        candidate_dashboard()
    else:
        # Mock Login/Landing page
        st.title("Welcome to the Candidate AI App")
        st.warning("This is a simplified environment. Click below to proceed.")
        if st.button("Start Dashboard Session"):
            go_to("candidate_dashboard")

if __name__ == "__main__":
    main()
