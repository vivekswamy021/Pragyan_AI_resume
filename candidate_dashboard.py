import streamlit as st
import os
import pdfplumber
import docx
import openpyxl
import json
import tempfile
from groq import Groq
from gtts import gTTS 
import traceback
import re 
from dotenv import load_dotenv 
from datetime import date 
import csv 
from streamlit.runtime.uploaded_file_manager import UploadedFile 
# (Note: Imports must be defined globally in a real Streamlit app, 
# but are included here for completeness of context.)

# --- Global Configurations (Assume these are defined outside this function) ---
GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'MOCK_KEY') 
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY != 'MOCK_KEY' else None

section_options = ["name", "email", "phone", "skills", "education", "experience", "certifications", "projects", "strength", "personal_details", "github", "linkedin", "full resume"]
question_section_options = ["skills","experience", "certifications", "projects", "education"] 

DEFAULT_JOB_TYPES = ["Full-time", "Contract", "Internship", "Remote", "Part-time"]
DEFAULT_ROLES = ["Software Engineer", "Data Scientist", "Product Manager", "HR Manager", "Marketing Specialist", "Operations Analyst"]

# Helper functions (Assumed to be defined and available):
# go_to(page_name)
# clear_interview_state()
# extract_jd_metadata(jd_text)
# extract_content(file_type, file_path)
# get_file_type(file_path)
# parse_with_llm(text, return_type='json')
# extract_jd_from_linkedin_url(url: str)
# evaluate_jd_fit(job_description, parsed_json)
# evaluate_interview_answers(qa_list, parsed_json)
# generate_interview_questions(parsed_json, section)
# qa_on_jd(question, selected_jd_name)
# parse_and_store_resume(file_input, file_name_key='default', source_type='file')
# qa_on_resume(question)
# generate_cv_html(parsed_data)
# format_parsed_json_to_markdown(parsed_data)
# (For a complete, runnable example, you must ensure all these dependencies are met.)

# -------------------------
# HELPER FUNCTIONS USED ONLY WITHIN CANDIDATE DASHBOARD
# (These would be defined globally in the main app file)
# -------------------------

def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def clear_interview_state():
    """Clears all generated questions, answers, and the evaluation report."""
    st.session_state.interview_qa = []
    st.session_state.iq_output = ""
    st.session_state.evaluation_report = ""
    st.toast("Practice answers cleared.")

def qa_on_jd(question, selected_jd_name):
    """Chatbot for JD (Q&A) using LLM."""
    if not GROQ_API_KEY or GROQ_API_KEY == 'MOCK_KEY':
        return "AI Chatbot Disabled: GROQ_API_KEY not set."

    # Find the JD content from the stored list
    jd_item = next((jd for jd in st.session_state.candidate_jd_list if jd['name'] == selected_jd_name), None)

    if not jd_item:
        return "Error: Could not find the selected Job Description in the loaded list."

    jd_text = jd_item['content']
    jd_metadata = {k: v for k, v in jd_item.items() if k not in ['name', 'content']}

    prompt = f"""Given the following Job Description and its extracted metadata:
    
    Job Description Title: {selected_jd_name}
    JD Metadata (JSON): {json.dumps(jd_metadata, indent=2)}
    JD Full Text:
    ---
    {jd_text}
    ---
    
    Answer the following question about the Job Description concisely and directly.
    If the information is not present in the provided text, state that clearly.
    
    Question: {question}
    """
    
    # Mocking the client interaction since the actual Groq client is not available in this snippet
    if client is None:
        return f"Mock Answer (JD): The {selected_jd_name} JD requires expertise in {jd_metadata.get('key_skills', ['Python'])[0]} and is a {jd_metadata.get('job_type', 'Full-time')} role."

    response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.4)
    return response.choices[0].message.content.strip()

def qa_on_resume(question):
    """Chatbot for Resume (Q&A) using LLM."""
    if not GROQ_API_KEY or GROQ_API_KEY == 'MOCK_KEY':
        return "AI Chatbot Disabled: GROQ_API_KEY not set."
        
    parsed_json = st.session_state.parsed
    full_text = st.session_state.full_text
    prompt = f"""Given the following resume information:
    Resume Text: {full_text}
    Parsed Resume Data (JSON): {json.dumps(parsed_json, indent=2)}
    Answer the following question about the resume concisely and directly.
    If the information is not present, state that clearly.
    Question: {question}
    """
    
    # Mocking the client interaction
    if client is None:
        name = parsed_json.get('name', 'The candidate')
        skill = parsed_json.get('skills', ['none listed'])[0]
        return f"Mock Answer (Resume): {name} has experience with {skill} and is looking for a new role."


    response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.4)
    return response.choices[0].message.content.strip()


# Placeholder/Stub functions for dependencies that require complex logic or external APIs
def extract_jd_metadata(jd_text):
    """Placeholder for metadata extraction."""
    return {"role": "General Analyst", "job_type": "Full-time", "key_skills": ["Python", "SQL", "Teamwork"]}

def extract_jd_from_linkedin_url(url: str) -> str:
    """Simulates JD content extraction."""
    return f"""
        --- Simulated JD for: Data Scientist ---
        **Company:** Quantum Analytics Inc.
        **Role:** Data Scientist
        **Requirements:** 3+ years of experience. Expertise in Python and AWS.
        """
        
def parse_and_store_resume(file_input, file_name_key='default', source_type='file'):
    """Simulates resume parsing and returns mock data structure."""
    if source_type == 'file':
        file_name = file_input.name.split('.')[0]
    else:
        file_name = f"Pasted Text ({date.today().strftime('%Y-%m-%d')})"
        
    # Mock parsed output
    mock_parsed = {
        "name": file_name.replace('_', ' '),
        "email": "mock@example.com",
        "phone": "123-456-7890",
        "skills": ["Python", "Streamlit", "LLM Integration", "Data Analysis"],
        "experience": ["Lead Developer at Tech Corp (2020-Present)"],
        "education": ["M.S. Computer Science, University X"],
        "certifications": [], "projects": [], "strength": ["Problem Solver"],
        "personal_details": "Highly motivated and results-driven individual.",
        "github": "http://github.com/mock", "linkedin": "http://linkedin.com/mock"
    }
    
    return {
        "parsed": mock_parsed,
        "full_text": "This is simulated full resume text.",
        "excel_data": b"mock_excel_data",
        "name": file_name.replace('_', ' ')
    }

def evaluate_jd_fit(job_description, parsed_json):
    """Simulates JD fit evaluation."""
    if client is None:
        return f"""
        Overall Fit Score: 8/10
        
        --- Section Match Analysis ---
        Skills Match: 85%
        Experience Match: 90%
        Education Match: 75%
        
        Strengths/Matches:
        - Strong background in Python and data tools.
        - Experience section aligns well with required seniority.
        
        Gaps/Areas for Improvement:
        - Missing explicit mention of specific cloud platforms (e.g., Azure).
        - Educational background is relevant but lacks specific research projects mentioned in JD.
        
        Overall Summary: Excellent candidate fit, highly recommended for shortlisting.
        """
    # In a real scenario, this would call the actual LLM function
    return "LLM API Call Successful (Actual LLM output would be here)"

def generate_interview_questions(parsed_json, section):
    """Simulates question generation."""
    if client is None:
        return f"""
        [Generic]
        Q1: Can you walk me through your experience in the {section} area?
        Q2: What is the most challenging task you faced related to {section}?
        [Basic]
        Q1: How did you acquire the skill of '{parsed_json.get('skills', ['Python'])[0]}'?
        [Intermediate]
        Q1: Describe a scenario where your experience (from {section}) directly led to a business result.
        [Difficult]
        Q1: Based on your education (from {section}), how would you design a system to solve [complex, unstated problem]?
        """
    # In a real scenario, this would call the actual LLM function
    return "LLM API Call Successful (Actual LLM output would be here)"

def evaluate_interview_answers(qa_list, parsed_json):
    """Simulates interview evaluation."""
    if client is None:
        total_score = sum(3 for _ in qa_list) 
        return f"""
        ## Evaluation Results
        
        ### Question 1: {qa_list[0]['question'] if qa_list else 'N/A'}
        Score: 7/10
        Feedback:
        - **Clarity & Accuracy:** Answer was clear but failed to connect back to the 'Tech Corp' experience mentioned in the resume.
        - **Gaps & Improvements:** Candidate should use the STAR method and reference the specific projects listed.
        
        ---
        
        ## Final Assessment
        Total Score: {total_score}/30
        Overall Summary: Good foundational knowledge, but needs practice in tailoring answers to the content of the resume for stronger credibility.
        """
    # In a real scenario, this would call the actual LLM function
    return "LLM API Call Successful (Actual LLM output would be here)"

def generate_cv_html(parsed_data):
    """Simulates HTML generation."""
    return f"<html><body><h1>{parsed_data.get('name', 'CV Preview')}</h1><p>...Simulated CV HTML Content...</p></body></html>"

def format_parsed_json_to_markdown(parsed_data):
    """Simulates Markdown generation."""
    return f"# {parsed_data.get('name', 'CV Preview')}\n\n## Skills\n- {parsed_data.get('skills', ['N/A'])[0]}\n\n..."

# -------------------------
# TAB CONTENT FUNCTIONS (EXTRACTED)
# -------------------------

def cv_management_tab_content():
    # ... (Logic from the main app) ...
    # This function is long and complex, using st.form and session state 
    # (cv_form_data, parsed, full_text, etc.).
    st.header("📝 Prepare Your CV")
    st.markdown("### 1. Form Based CV Builder")
    st.info("Fill out the details below to generate a parsed CV that can be used immediately for matching and interview prep, or start by parsing a file in the 'Resume Parsing' tab.")

    default_parsed = {
        "name": "", "email": "", "phone": "", "linkedin": "", "github": "",
        "skills": [], "experience": [], "education": [], "certifications": [], 
        "projects": [], "strength": [], "personal_details": ""
    }
    
    if "cv_form_data" not in st.session_state:
        if st.session_state.get('parsed', {}).get('name'):
            st.session_state.cv_form_data = st.session_state.parsed.copy()
        else:
            st.session_state.cv_form_data = default_parsed
    
    with st.form("cv_builder_form"):
        # Simplified form for brevity of this isolated snippet
        st.subheader("Personal & Contact Details")
        st.session_state.cv_form_data['name'] = st.text_input("Full Name", value=st.session_state.cv_form_data['name'], key="cv_name")
        st.session_state.cv_form_data['email'] = st.text_input("Email Address", value=st.session_state.cv_form_data['email'], key="cv_email")
        
        st.markdown("---")
        st.subheader("Technical Sections (One Item per Line)")
        
        # Skills
        skills_text = "\n".join(st.session_state.cv_form_data.get('skills', []))
        new_skills_text = st.text_area("Key Skills (e.g., Python, SQL, Cloud)", value=skills_text, height=100, key="cv_skills")
        st.session_state.cv_form_data['skills'] = [s.strip() for s in new_skills_text.split('\n') if s.strip()]
        
        submit_form_button = st.form_submit_button("Generate and Load CV Data", use_container_width=True)

    if submit_form_button:
        if not st.session_state.cv_form_data['name'] or not st.session_state.cv_form_data['email']:
            st.error("Please fill in at least your **Full Name** and **Email Address**.")
            return

        st.session_state.parsed = st.session_state.cv_form_data.copy()
        # Mock full text creation
        st.session_state.full_text = f"Name: {st.session_state.parsed['name']}\nSkills: {', '.join(st.session_state.parsed['skills'])}"
        
        st.session_state.candidate_match_results = []
        st.session_state.interview_qa = []
        st.session_state.evaluation_report = ""

        st.success(f"✅ CV data for **{st.session_state.parsed['name']}** successfully generated and loaded!")
        
    st.markdown("---")
    st.subheader("2. Loaded CV Data Preview and Download")
    
    if st.session_state.get('parsed', {}).get('name'):
        
        filled_data_for_preview = {k: v for k, v in st.session_state.parsed.items() if v}
        
        tab_markdown, tab_json, tab_pdf = st.tabs(["📝 Markdown View", "💾 JSON View", "⬇️ PDF/HTML Download"])

        with tab_markdown:
            cv_markdown_preview = format_parsed_json_to_markdown(filled_data_for_preview)
            st.markdown(cv_markdown_preview)

        with tab_json:
            st.json(st.session_state.parsed)

        with tab_pdf:
            st.download_button(
                label="⬇️ Download CV as Print-Ready HTML File",
                data=generate_cv_html(filled_data_for_preview),
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_CV_Document.html",
                mime="text/html",
                key="download_cv_html_final"
            )
    else:
        st.info("Please generate or parse a CV to see the preview and download options.")


def resume_parsing_tab_content():
    # ... (Logic from the main app) ...
    st.header("Resume Upload and Parsing")
    
    input_method = st.radio("Select Input Method", ["Upload File", "Paste Text"], key="parsing_input_method")
    st.markdown("---")

    if input_method == "Upload File":
        st.markdown("### 1. Upload Resume File") 
        uploaded_file = st.file_uploader( 
            "Choose PDF, DOCX, TXT, JSON, MD, CSV, XLSX file", 
            type=["pdf", "docx", "txt", "json", "md", "csv", "xlsx", "markdown", "rtf"], 
            accept_multiple_files=False, 
            key='candidate_file_upload_main'
        )
        if uploaded_file is not None:
            if not st.session_state.get('candidate_uploaded_resumes') or st.session_state.candidate_uploaded_resumes[0].name != uploaded_file.name:
                st.session_state.candidate_uploaded_resumes = [uploaded_file] 
                st.session_state.pasted_cv_text = "" 
        
        file_to_parse = st.session_state.candidate_uploaded_resumes[0] if st.session_state.get('candidate_uploaded_resumes') else None
        
        st.markdown("### 2. Parse Uploaded File")
        if file_to_parse:
            if st.button(f"Parse and Load: **{file_to_parse.name}**", use_container_width=True):
                with st.spinner(f"Parsing {file_to_parse.name}..."):
                    result = parse_and_store_resume(file_to_parse, file_name_key='single_resume_candidate', source_type='file')
                    
                    if "error" not in result:
                        st.session_state.parsed = result['parsed']
                        st.session_state.full_text = result['full_text']
                        st.session_state.parsed['name'] = result['name'] 
                        clear_interview_state()
                        st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                    else:
                        st.error(f"Parsing failed: {result['error']}")
                        st.session_state.parsed = {"error": result['error'], "name": result['name']}

    else: # Paste Text
        st.markdown("### 1. Paste Your CV Text")
        pasted_text = st.text_area(
            "Copy and paste your entire CV or resume text here.",
            value=st.session_state.get('pasted_cv_text', ''),
            height=300,
            key='pasted_cv_text_input'
        )
        st.session_state.pasted_cv_text = pasted_text
        
        st.markdown("### 2. Parse Pasted Text")
        if pasted_text.strip():
            if st.button("Parse and Load Pasted Text", use_container_width=True):
                with st.spinner("Parsing pasted text..."):
                    st.session_state.candidate_uploaded_resumes = []
                    
                    result = parse_and_store_resume(pasted_text, file_name_key='single_resume_candidate', source_type='text')
                    
                    if "error" not in result:
                        st.session_state.parsed = result['parsed']
                        st.session_state.full_text = result['full_text']
                        st.session_state.parsed['name'] = result['name'] 
                        clear_interview_state()
                        st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                    else:
                        st.error(f"Parsing failed: {result['error']}")
                        st.session_state.parsed = {"error": result['error'], "name": result['name']}
        else:
            st.info("Please paste your CV text into the box above.")

# (JD Management, Batch Match, Filter JD, Chatbot Q&A, Interview Prep functions would also be defined here)
# ...

def jd_management_tab_content():
    # ... (Logic from the main app) ...
    st.header("📚 Manage Job Descriptions for Matching")
    
    if "candidate_jd_list" not in st.session_state:
         st.session_state.candidate_jd_list = []
    
    jd_type = st.radio("Select JD Type", ["Single JD", "Multiple JD"], key="jd_type_candidate")
    method = st.radio("Choose Method", ["Upload File", "Paste Text", "LinkedIn URL"], key="jd_add_method_candidate") 

    if method == "LinkedIn URL":
        url_list = st.text_area("Enter URL(s)", key="url_list_candidate")
        if st.button("Add JD(s) from URL", key="add_jd_url_btn_candidate"):
            if url_list:
                urls = [u.strip() for u in url_list.split(",")]
                count = 0
                for url in urls:
                    jd_text = extract_jd_from_linkedin_url(url)
                    metadata = extract_jd_metadata(jd_text)
                    name = f"JD from URL: {url.split('/')[-1]}"
                    st.session_state.candidate_jd_list.append({"name": name, "content": jd_text, **metadata})
                    count += 1
                st.success(f"✅ {count} JD(s) added successfully!")
    elif method == "Paste Text":
        text_list = st.text_area("Paste JD text here", key="text_list_candidate")
        if st.button("Add JD(s) from Text", key="add_jd_text_btn_candidate"):
            if text_list:
                texts = [text_list]
                for i, text in enumerate(texts):
                    metadata = extract_jd_metadata(text)
                    st.session_state.candidate_jd_list.append({"name": f"Pasted JD {len(st.session_state.candidate_jd_list) + i + 1}", "content": text, **metadata})
                st.success(f"✅ {len(texts)} JD(s) added successfully!")
    elif method == "Upload File":
        uploaded_files = st.file_uploader("Upload JD file(s)", type=["pdf", "txt", "docx"], accept_multiple_files=(jd_type == "Multiple JD"), key="jd_file_uploader_candidate")
        if st.button("Add JD(s) from File", key="add_jd_file_btn_candidate"):
            st.warning("File upload logic skipped for brevity in this snippet.")


    if st.session_state.candidate_jd_list:
        if st.button("🗑️ Clear All JDs", key="clear_jds_candidate"):
            st.session_state.candidate_jd_list = []
            st.session_state.candidate_match_results = [] 
            st.success("All JDs cleared.")
            st.rerun() 

        for idx, jd_item in enumerate(st.session_state.candidate_jd_list, 1):
            with st.expander(f"JD {idx}: {jd_item['name']}"):
                st.text(jd_item['content'])


def batch_jd_match_tab_content():
    # ... (Logic from the main app) ...
    st.header("🎯 Batch JD Match: Best Matches")
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name'))

    if not is_resume_parsed:
        st.warning("Please **upload and parse your resume** first.")
    elif not st.session_state.get('candidate_jd_list'):
        st.error("Please **add Job Descriptions** first.")
    else:
        if "candidate_match_results" not in st.session_state:
            st.session_state.candidate_match_results = []
            
        all_jd_names = [item['name'] for item in st.session_state.candidate_jd_list]
        selected_jd_names = st.multiselect("Select Job Descriptions", options=all_jd_names, default=all_jd_names, key='candidate_batch_jd_select')
        jds_to_match = [jd_item for jd_item in st.session_state.candidate_jd_list if jd_item['name'] in selected_jd_names]
        
        if st.button(f"Run Match Analysis on {len(jds_to_match)} Selected JD(s)"):
            st.session_state.candidate_match_results = []
            results_with_score = []
            
            with st.spinner("Matching..."):
                for jd_item in jds_to_match:
                    fit_output = evaluate_jd_fit(jd_item['content'], st.session_state.parsed)
                    score_match = re.search(r'Overall Fit Score:\s*(\d+)/10', fit_output)
                    overall_score = score_match.group(1) if score_match else '5' # Mock score 
                    
                    results_with_score.append({
                        "jd_name": jd_item['name'],
                        "overall_score": overall_score,
                        "numeric_score": int(overall_score),
                        "full_analysis": fit_output
                    })
                
                results_with_score.sort(key=lambda x: x['numeric_score'], reverse=True)
                
                # Assign Rank
                for i, item in enumerate(results_with_score):
                    item['rank'] = i + 1
                    del item['numeric_score']
                
                st.session_state.candidate_match_results = results_with_score
                st.success("Batch analysis complete!")

        if st.session_state.get('candidate_match_results'):
            st.markdown("#### Match Results for Your Resume")
            display_data = []
            for item in st.session_state.candidate_match_results:
                display_data.append({
                    "Rank": item.get("rank", "N/A"),
                    "Job Description (Ranked)": item["jd_name"],
                    "Fit Score (out of 10)": item["overall_score"],
                })
            st.dataframe(display_data, use_container_width=True)

            st.markdown("##### Detailed Reports")
            for item in st.session_state.candidate_match_results:
                with st.expander(f"Rank {item.get('rank', 'N/A')} | {item['jd_name']}"):
                    st.markdown(item['full_analysis'])


def filter_jd_tab_content():
    # ... (Logic from the main app) ...
    st.header("🔍 Filter Job Descriptions by Criteria")
    if not st.session_state.get('candidate_jd_list'):
        st.info("No Job Descriptions are currently loaded.")
        return

    unique_roles = ["All Roles"] + sorted(list(set([item.get('role', 'General Analyst') for item in st.session_state.candidate_jd_list])))
    
    with st.form(key="jd_filter_form"):
        selected_role = st.selectbox("Role Title", options=unique_roles, key="filter_role_select")
        apply_filters_button = st.form_submit_button("✅ Apply Filters", type="primary", use_container_width=True)

    if apply_filters_button:
        filtered_jds = [
            jd for jd in st.session_state.candidate_jd_list 
            if (selected_role == "All Roles") or (selected_role == jd.get('role'))
        ]
        st.session_state.filtered_jds_display = filtered_jds
        st.success(f"Found {len(filtered_jds)} matching Job Descriptions.")
    
    if st.session_state.get('filtered_jds_display'):
        st.subheader(f"Matching Job Descriptions ({len(st.session_state.filtered_jds_display)} found)")
        for idx, jd in enumerate(st.session_state.filtered_jds_display, 1):
            with st.expander(f"JD {idx}: {jd['name']} ({jd.get('role', 'N/A')})"):
                st.text(jd['content'])
    

def resume_jd_chatbot_tab_content():
    # ... (Logic from the main app) ...
    st.header("Resume/JD Chatbot (Q&A) 💬")
    sub_tab_resume, sub_tab_jd = st.tabs(["👤 Chat about Your Resume", "📄 Chat about Saved JDs"])
    
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name'))

    with sub_tab_resume:
        st.markdown("### Ask any question about the currently loaded resume.")
        if not is_resume_parsed:
            st.warning("Please upload and parse a resume first.")
        else:
            if 'qa_answer_resume' not in st.session_state: st.session_state.qa_answer_resume = ""
            question = st.text_input("Your Question (about Resume)", key="resume_qa_question")
            
            if st.button("Get Answer (Resume)", key="qa_btn_resume"):
                with st.spinner("Generating answer..."):
                    st.session_state.qa_answer_resume = qa_on_resume(question)
            if st.session_state.get('qa_answer_resume'):
                st.text_area("Answer (Resume)", st.session_state.qa_answer_resume, height=150)
    
    with sub_tab_jd:
        st.markdown("### Ask any question about a saved Job Description.")
        if not st.session_state.get('candidate_jd_list'):
            st.warning("Please add Job Descriptions first.")
        else:
            if 'qa_answer_jd' not in st.session_state: st.session_state.qa_answer_jd = ""
            jd_names = [jd['name'] for jd in st.session_state.candidate_jd_list]
            selected_jd_name = st.selectbox("Select Job Description to Query", options=jd_names, key="jd_qa_select")
            question = st.text_input("Your Question (about JD)", key="jd_qa_question")
            
            if st.button("Get Answer (JD)", key="qa_btn_jd"):
                with st.spinner("Generating answer..."):
                    st.session_state.qa_answer_jd = qa_on_jd(question, selected_jd_name)

            if st.session_state.get('qa_answer_jd'):
                st.text_area("Answer (JD)", st.session_state.qa_answer_jd, height=150)


def interview_prep_tab_content():
    # ... (Logic from the main app) ...
    st.header("Interview Preparation Tools")
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name'))

    if not is_resume_parsed:
        st.warning("Please upload and successfully parse a resume first.")
    else:
        if 'iq_output' not in st.session_state: st.session_state.iq_output = ""
        if 'interview_qa' not in st.session_state: st.session_state.interview_qa = [] 
        if 'evaluation_report' not in st.session_state: st.session_state.evaluation_report = "" 
        
        st.subheader("1. Generate Interview Questions")
        section_choice = st.selectbox("Select Section", question_section_options, key='iq_section_c')
        
        if st.button("Generate Interview Questions", key='iq_btn_c'):
            with st.spinner("Generating questions..."):
                raw_questions_response = generate_interview_questions(st.session_state.parsed, section_choice)
                st.session_state.iq_output = raw_questions_response
                st.session_state.interview_qa = [] 
                
                # Mock parsing of questions
                q_list = []
                for i in range(3): 
                    q_list.append({"question": f"(Mock Level) Question about {section_choice} #{i+1}", "answer": "", "level": "Mock Level"})
                st.session_state.interview_qa = q_list
                st.success(f"Generated {len(q_list)} mock questions.")

        if st.session_state.get('interview_qa'):
            st.markdown("---")
            st.subheader("2. Practice and Record Answers")
            
            with st.form("interview_practice_form"):
                for i, qa_item in enumerate(st.session_state.interview_qa):
                    st.markdown(f"**Question {i+1}:** {qa_item['question']}")
                    answer = st.text_area(f"Your Answer for Q{i+1}", value=st.session_state.interview_qa[i]['answer'], height=100, key=f'answer_q_{i}', label_visibility='collapsed')
                    st.session_state.interview_qa[i]['answer'] = answer 
                
                submit_button = st.form_submit_button("Submit & Evaluate Answers", use_container_width=True)

                if submit_button:
                    if all(item['answer'].strip() for item in st.session_state.interview_qa):
                        with st.spinner("Sending answers to AI Evaluator..."):
                            report = evaluate_interview_answers(st.session_state.interview_qa, st.session_state.parsed)
                            st.session_state.evaluation_report = report
                            st.success("Evaluation complete! See the report below.")
                    else:
                        st.error("Please answer all generated questions before submitting.")
            
            if st.session_state.get('evaluation_report'):
                st.markdown("---")
                st.subheader("3. AI Evaluation Report")
                st.markdown(st.session_state.evaluation_report)


# -------------------------
# THE CANDIDATE DASHBOARD FUNCTION (with REARRANGED TABS)
# -------------------------

def candidate_dashboard():
    st.header("👩‍🎓 Candidate Dashboard")
    st.markdown("Welcome! Use the tabs below to manage your CV and access AI preparation tools.")

    # --- Navigation Block ---
    nav_col, _ = st.columns([1, 1]) 
    with nav_col:
        if st.button("🚪 Log Out", key="candidate_logout_btn", use_container_width=True):
            go_to("login") 

    # --- Sidebar for Status ---
    with st.sidebar:
        st.header("Resume/CV Status")
        if st.session_state.get('parsed', {}).get("name"):
            st.success(f"Currently loaded: **{st.session_state.parsed['name']}**")
        else:
            st.info("Please upload a file or use the CV builder to begin.")

    # Main Content Tabs (REARRANGED TABS)
    # The Resume/JD Chatbot (Q&A) and Interview Prep tabs are moved to the end.
    tab_cv_mgmt, tab_parsing, tab_jd_mgmt, tab_batch_match, tab_filter_jd, tab_chatbot, tab_interview_prep = st.tabs([
        "✍️ CV Management", 
        "📄 Resume Parsing", 
        "📚 JD Management", 
        "🎯 Batch JD Match",
        "🔍 Filter JD",
        "💬 Resume/JD Chatbot (Q&A)",   # MOVED TO THE LAST TWO
        "❓ Interview Prep"             # MOVED TO THE LAST TWO
    ])
    
    # --- Tab Contents ---
    with tab_cv_mgmt:
        cv_management_tab_content()

    with tab_parsing:
        resume_parsing_tab_content()

    with tab_jd_mgmt:
        jd_management_tab_content()

    with tab_batch_match:
        batch_jd_match_tab_content()

    with tab_filter_jd:
        filter_jd_tab_content()

    with tab_chatbot:
        resume_jd_chatbot_tab_content()

    with tab_interview_prep:
        interview_prep_tab_content()


# -------------------------
# MAIN EXECUTION CONTEXT (Needed for session state setup)
# -------------------------

if 'page' not in st.session_state: st.session_state.page = "login"
if 'parsed' not in st.session_state: st.session_state.parsed = {}
if 'full_text' not in st.session_state: st.session_state.full_text = ""
if 'candidate_jd_list' not in st.session_state: st.session_state.candidate_jd_list = []
if 'candidate_uploaded_resumes' not in st.session_state: st.session_state.candidate_uploaded_resumes = []
if 'pasted_cv_text' not in st.session_state: st.session_state.pasted_cv_text = "" 
if 'cv_form_data' not in st.session_state: 
    st.session_state.cv_form_data = {"name": "", "email": "", "skills": []} 
if 'candidate_match_results' not in st.session_state: st.session_state.candidate_match_results = []
if 'interview_qa' not in st.session_state: st.session_state.interview_qa = []
if 'evaluation_report' not in st.session_state: st.session_state.evaluation_report = ""
if 'filtered_jds_display' not in st.session_state: st.session_state.filtered_jds_display = []
