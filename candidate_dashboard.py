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

# --- 0. INITIAL SETUP AND CONFIGURATION ---

# Load environment variables
load_dotenv() 

# Groq Configuration
GROQ_MODEL = "llama-3.1-8b-instant"
# Use a mock key if the real one isn't set, and disable the client
GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'MOCK_KEY') 
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY != 'MOCK_KEY' else None

# Constants for UI
section_options = ["name", "email", "phone", "skills", "education", "experience", "certifications", "projects", "strength", "personal_details", "github", "linkedin", "full resume"]
question_section_options = ["skills","experience", "certifications", "projects", "education"] 

DEFAULT_JOB_TYPES = ["Full-time", "Contract", "Internship", "Remote", "Part-time"]
DEFAULT_ROLES = ["Software Engineer", "Data Scientist", "Product Manager", "HR Manager", "Marketing Specialist", "Operations Analyst"]


# --- 1. HELPER FUNCTIONS ---

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
        return "**AI Chatbot Disabled:** GROQ_API_KEY not set. Cannot run Q&A."

    jd_item = next((jd for jd in st.session_state.candidate_jd_list if jd['name'] == selected_jd_name), None)
    if not jd_item:
        return "Error: Could not find the selected Job Description."

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
    
    try:
        response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.4)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM Error: Could not generate answer. Details: {e}"


def qa_on_resume(question):
    """Chatbot for Resume (Q&A) using LLM."""
    if not GROQ_API_KEY or GROQ_API_KEY == 'MOCK_KEY':
        return "**AI Chatbot Disabled:** GROQ_API_KEY not set. Cannot run Q&A."
        
    parsed_json = st.session_state.parsed
    full_text = st.session_state.full_text
    
    prompt = f"""Given the following resume information:
    Resume Text: {full_text}
    Parsed Resume Data (JSON): {json.dumps(parsed_json, indent=2)}
    Answer the following question about the resume concisely and directly.
    If the information is not present, state that clearly.
    Question: {question}
    """
    
    try:
        response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.4)
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"LLM Error: Could not generate answer. Details: {e}"


# --- 2. MOCK/PLACEHOLDER LLM/PARSING FUNCTIONS ---
# NOTE: These functions simulate complex LLM operations and file parsing. 
# For a production app, you would replace these with your actual implementation.

def extract_jd_metadata(jd_text):
    """Placeholder for metadata extraction."""
    # LLM call or regex to extract role, type, and key skills
    if 'data scientist' in jd_text.lower():
        role = "Data Scientist"
        skills = ["Python", "Machine Learning", "Cloud"]
    else:
        role = "Software Engineer"
        skills = ["Java", "SQL", "Agile"]
        
    return {"role": role, "job_type": "Full-time", "key_skills": skills}

def extract_jd_from_linkedin_url(url: str) -> str:
    """Simulates JD content extraction from a URL."""
    return f"""
        --- Simulated Job Description for: {url.split('/')[-1]} ---
        **Company:** Tech Global Solutions
        **Role:** Senior Software Engineer
        **Requirements:** 5+ years of experience. Expertise in Python, Kubernetes, and Microservices. 
        Focus on cloud deployments (AWS preferred).
        """
        
def parse_and_store_resume(file_input, file_name_key='default', source_type='file'):
    """Simulates resume parsing and returns mock data structure."""
    if source_type == 'file':
        file_name = file_input.name.split('.')[0]
        # In a real app, logic to handle PDF/DOCX/TXT extraction goes here
        full_text = f"Simulated full text from file: {file_input.name}"
    else:
        file_name = f"Pasted Text ({date.today().strftime('%Y-%m-%d')})"
        full_text = file_input
        
    # Mock parsed output based on the input type
    mock_parsed = {
        "name": file_name.replace('_', ' ').replace('(Mock)', ''),
        "email": "mock@example.com",
        "phone": "123-456-7890",
        "skills": ["Python", "Streamlit", "LLM Integration", "Data Analysis", "SQL"],
        "experience": ["Lead Developer at Tech Corp (2020-Present)", "Software Engineer at Startup X (2018-2020)"],
        "education": ["M.S. Computer Science, University X"],
        "certifications": ["AWS Certified Developer"], "projects": ["AI Chatbot Project", "Data Pipeline System"], "strength": ["Problem Solver"],
        "personal_details": "Highly motivated and results-driven individual.",
        "github": "http://github.com/mock", "linkedin": "http://linkedin.com/mock"
    }
    
    return {
        "parsed": mock_parsed,
        "full_text": full_text,
        "excel_data": b"mock_excel_data",
        "name": file_name.replace('_', ' ')
    }

def evaluate_jd_fit(job_description, parsed_json):
    """Simulates JD fit evaluation using LLM."""
    if client is None:
        # Mock result based on a simple check
        score = 7 if "Python" in parsed_json.get("skills", []) and "Engineer" in job_description else 5
        return f"""
        Overall Fit Score: **{score}/10**
        
        --- Section Match Analysis ---
        Skills Match: 85%
        Experience Match: 90%
        
        Strengths/Matches:
        - Strong background in **Python** and data tools.
        - Experience section aligns well with required seniority.
        
        Gaps/Areas for Improvement:
        - Missing explicit mention of specific cloud platforms (e.g., Azure).
        
        Overall Summary: Good candidate fit, recommended for shortlisting.
        """
    # In a real scenario, this would call the actual LLM function with a detailed prompt
    return "LLM API Call Successful (Actual LLM output would be here)"

def generate_interview_questions(parsed_json, section):
    """Simulates question generation using LLM."""
    if client is None:
        return f"""
        ## Generated Interview Questions (Mock)
        
        ### Based on {section.capitalize()}
        Q1: Can you walk me through your experience in the **{section}** area as listed on your resume?
        Q2: Describe the most challenging project you faced related to {section}.
        Q3: How did you acquire the skill of '{parsed_json.get('skills', ['Python'])[0]}'?
        """
    # In a real scenario, this would call the actual LLM function
    return "LLM API Call Successful (Actual LLM output would be here)"

def evaluate_interview_answers(qa_list, parsed_json):
    """Simulates interview evaluation using LLM."""
    if client is None:
        answered_count = sum(1 for item in qa_list if item['answer'].strip())
        total_score = answered_count * 3 
        
        report_parts = [f"## AI Evaluation Report\n\n**Candidate:** {parsed_json.get('name', 'N/A')}\n"]
        
        for i, item in enumerate(qa_list, 1):
            if item['answer'].strip():
                report_parts.append(f"### Question {i}: {item['question']}\n\n**Candidate Answer:** {item['answer'][:50]}...\n\n**Score:** 7/10\n**Feedback:** Answer was clear but could use more specific metrics or STAR method details.")
            else:
                report_parts.append(f"### Question {i}: {item['question']}\n\n**Candidate Answer:** (Not answered)\n\n**Score:** 0/10")

        report_parts.append(f"\n---\n## Final Assessment\nTotal Score: **{total_score}/30**\nOverall Summary: Good foundational knowledge, but practice using the STAR method for stronger, structured answers is recommended.")
        return "\n\n".join(report_parts)
    
    # In a real scenario, this would call the actual LLM function
    return "LLM API Call Successful (Actual LLM output would be here)"

def generate_cv_html(parsed_data):
    """Simulates HTML generation for download."""
    name = parsed_data.get('name', 'CV Preview')
    skills = "<li>" + "</li><li>".join(parsed_data.get('skills', ['N/A'])) + "</li>"
    return f"""
        <html>
        <head><title>{name} CV</title></head>
        <body style='font-family: Arial; padding: 20px;'>
            <h1 style='border-bottom: 2px solid #ccc;'>{name}</h1>
            <p><strong>Email:</strong> {parsed_data.get('email', 'N/A')}</p>
            <p><strong>LinkedIn:</strong> <a href='{parsed_data.get('linkedin', '#')}'>{parsed_data.get('linkedin', 'N/A')}</a></p>
            <h2>Key Skills</h2>
            <ul>{skills}</ul>
            <h2>Experience</h2>
            <p>{'<br>'.join(parsed_data.get('experience', ['N/A']))}</p>
        </body>
        </html>
        """

def format_parsed_json_to_markdown(parsed_data):
    """Formats parsed resume data into a readable Markdown string."""
    markdown_output = f"# 👤 {parsed_data.get('name', 'CV Preview')}\n\n"
    
    markdown_output += f"**Email:** {parsed_data.get('email', 'N/A')} | "
    markdown_output += f"**Phone:** {parsed_data.get('phone', 'N/A')}\n"
    if parsed_data.get('linkedin'):
        markdown_output += f"**LinkedIn:** [{parsed_data['linkedin']}]({parsed_data['linkedin']}) | "
    if parsed_data.get('github'):
        markdown_output += f"**GitHub:** [{parsed_data['github']}]({parsed_data['github']})\n"
        
    markdown_output += "\n---\n"
    
    sections = ['personal_details', 'skills', 'experience', 'education', 'certifications', 'projects']
    for section in sections:
        data = parsed_data.get(section)
        if data:
            title = section.replace('_', ' ').title()
            markdown_output += f"## {title}\n"
            if isinstance(data, list):
                markdown_output += "\n".join([f"* {item}" for item in data]) + "\n\n"
            else:
                markdown_output += f"{data}\n\n"
                
    return markdown_output

# --- 3. TAB CONTENT FUNCTIONS ---

def cv_management_tab_content():
    st.header("📝 Prepare Your CV")
    st.markdown("### 1. Form-Based CV Builder")
    st.info("Use this form to quickly input your data. This data is instantly used for matching and interview prep.")

    default_parsed = {
        "name": "", "email": "", "phone": "", "linkedin": "", "github": "",
        "skills": [], "experience": [], "education": [], "certifications": [], 
        "projects": [], "strength": [], "personal_details": ""
    }
    
    # Initialize form data from session state if available
    if "cv_form_data" not in st.session_state:
        # Load existing parsed data into the form if a resume was already parsed
        st.session_state.cv_form_data = st.session_state.get('parsed', default_parsed).copy()
    
    with st.form("cv_builder_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Personal Details")
            st.session_state.cv_form_data['name'] = st.text_input("Full Name", value=st.session_state.cv_form_data.get('name', ''), key="cv_name")
            st.session_state.cv_form_data['email'] = st.text_input("Email Address", value=st.session_state.cv_form_data.get('email', ''), key="cv_email")
            st.session_state.cv_form_data['phone'] = st.text_input("Phone Number", value=st.session_state.cv_form_data.get('phone', ''), key="cv_phone")
        with col2:
            st.subheader("Links")
            st.session_state.cv_form_data['linkedin'] = st.text_input("LinkedIn URL", value=st.session_state.cv_form_data.get('linkedin', ''), key="cv_linkedin")
            st.session_state.cv_form_data['github'] = st.text_input("GitHub URL", value=st.session_state.cv_form_data.get('github', ''), key="cv_github")
            
        st.markdown("---")
        st.subheader("Key Sections (One Entry per Line)")
        
        # Skills
        skills_text = "\n".join(st.session_state.cv_form_data.get('skills', []))
        new_skills_text = st.text_area("Key Skills (e.g., Python, SQL, Cloud)", value=skills_text, height=100, key="cv_skills")
        st.session_state.cv_form_data['skills'] = [s.strip() for s in new_skills_text.split('\n') if s.strip()]
        
        # Experience
        experience_text = "\n".join(st.session_state.cv_form_data.get('experience', []))
        new_experience_text = st.text_area("Work Experience (e.g., Role @ Company, 2020-Present)", value=experience_text, height=150, key="cv_experience")
        st.session_state.cv_form_data['experience'] = [s.strip() for s in new_experience_text.split('\n') if s.strip()]
        
        submit_form_button = st.form_submit_button("Generate and Load CV Data", use_container_width=True, type="primary")

    if submit_form_button:
        if not st.session_state.cv_form_data.get('name') or not st.session_state.cv_form_data.get('email'):
            st.error("Please fill in at least your **Full Name** and **Email Address**.")
            return

        # Update the main parsed data for the app
        st.session_state.parsed = st.session_state.cv_form_data.copy()
        st.session_state.full_text = f"Name: {st.session_state.parsed['name']}\nSkills: {', '.join(st.session_state.parsed['skills'])}\nExperience: {', '.join(st.session_state.parsed['experience'])}"
        
        clear_interview_state() # Clear previous interview prep
        st.session_state.candidate_match_results = [] # Clear previous match results

        st.success(f"✅ CV data for **{st.session_state.parsed['name']}** successfully generated and loaded!")
        
    st.markdown("---")
    st.subheader("2. Loaded CV Data Preview and Download")
    
    if st.session_state.get('parsed', {}).get('name'):
        
        filled_data_for_preview = {k: v for k, v in st.session_state.parsed.items() if v}
        
        tab_markdown, tab_json, tab_pdf = st.tabs(["📝 Markdown View", "💾 JSON View", "⬇️ HTML/PDF Download"])

        with tab_markdown:
            cv_markdown_preview = format_parsed_json_to_markdown(filled_data_for_preview)
            st.markdown(cv_markdown_preview)

        with tab_json:
            st.json(st.session_state.parsed)

        with tab_pdf:
            st.info("The generated HTML file is a basic, print-ready document. Use dedicated CV tools for advanced design.")
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
    st.header("📄 Resume Upload and Parsing")
    
    input_method = st.radio("Select Input Method", ["Upload File", "Paste Text"], key="parsing_input_method", horizontal=True)
    st.markdown("---")

    if input_method == "Upload File":
        st.markdown("### 1. Upload Resume File") 
        uploaded_file = st.file_uploader( 
            "Choose PDF, DOCX, TXT, or other file type", 
            type=["pdf", "docx", "txt", "json", "md", "csv", "xlsx"], 
            accept_multiple_files=False, 
            key='candidate_file_upload_main'
        )
        
        file_to_parse = uploaded_file
        
        st.markdown("### 2. Parse Uploaded File")
        if file_to_parse:
            if st.button(f"Parse and Load: **{file_to_parse.name}**", use_container_width=True, type="primary"):
                with st.spinner(f"Parsing {file_to_parse.name} using LLM..."):
                    try:
                        result = parse_and_store_resume(file_to_parse, file_name_key='single_resume_candidate', source_type='file')
                        
                        if "error" not in result:
                            st.session_state.parsed = result['parsed']
                            st.session_state.full_text = result['full_text']
                            st.session_state.parsed['name'] = result['name'] 
                            clear_interview_state()
                            st.session_state.candidate_match_results = []
                            st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                        else:
                            st.error(f"Parsing failed: {result['error']}")
                            st.session_state.parsed = {"error": result['error'], "name": result['name']}
                    except Exception as e:
                        st.error(f"An unexpected error occurred during parsing: {e}")
                        st.exception(e)
        else:
            st.info("Please upload a file above.")

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
            if st.button("Parse and Load Pasted Text", use_container_width=True, type="primary"):
                with st.spinner("Parsing pasted text using LLM..."):
                    try:
                        result = parse_and_store_resume(pasted_text, file_name_key='single_resume_candidate', source_type='text')
                        
                        if "error" not in result:
                            st.session_state.parsed = result['parsed']
                            st.session_state.full_text = result['full_text']
                            st.session_state.parsed['name'] = result['name'] 
                            clear_interview_state()
                            st.session_state.candidate_match_results = []
                            st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                        else:
                            st.error(f"Parsing failed: {result['error']}")
                            st.session_state.parsed = {"error": result['error'], "name": result['name']}
                    except Exception as e:
                         st.error(f"An unexpected error occurred during parsing: {e}")
                         st.exception(e)
        else:
            st.info("Please paste your CV text into the box above.")


def jd_management_tab_content():
    st.header("📚 Manage Job Descriptions for Matching")
    
    if "candidate_jd_list" not in st.session_state:
         st.session_state.candidate_jd_list = []
    
    st.info(f"Currently loaded **{len(st.session_state.candidate_jd_list)}** Job Descriptions.")
    
    method = st.radio("Choose Method to Add JD", ["Paste Text", "LinkedIn URL", "Upload File"], key="jd_add_method_candidate", horizontal=True) 

    with st.container(border=True):
        if method == "LinkedIn URL":
            url_list = st.text_area("Enter JD URL(s) (one per line)", key="url_list_candidate", height=100)
            if st.button("Add JD(s) from URL", key="add_jd_url_btn_candidate"):
                if url_list:
                    urls = [u.strip() for u in url_list.split('\n') if u.strip()]
                    count = 0
                    with st.spinner(f"Extracting JDs from {len(urls)} URLs..."):
                        for url in urls:
                            jd_text = extract_jd_from_linkedin_url(url)
                            metadata = extract_jd_metadata(jd_text)
                            name = f"JD from URL: {metadata.get('role', 'N/A')} - {url.split('/')[-1]}"
                            st.session_state.candidate_jd_list.append({"name": name, "content": jd_text, **metadata})
                            count += 1
                    st.success(f"✅ {count} JD(s) added successfully!")
                else:
                    st.warning("Please enter at least one URL.")
        elif method == "Paste Text":
            text_list = st.text_area("Paste JD text here", key="text_list_candidate", height=200)
            if st.button("Add JD from Text", key="add_jd_text_btn_candidate"):
                if text_list.strip():
                    metadata = extract_jd_metadata(text_list)
                    name = f"Pasted JD: {metadata.get('role', 'N/A')} ({date.today().strftime('%m-%d')})"
                    st.session_state.candidate_jd_list.append({"name": name, "content": text_list, **metadata})
                    st.success(f"✅ JD '{name}' added successfully!")
                else:
                    st.warning("Please paste the JD text.")
        elif method == "Upload File":
            st.warning("File upload logic is highly complex and environment-dependent. Using placeholder logic to simulate adding a JD from a file.")
            uploaded_file = st.file_uploader("Upload single JD file (PDF, DOCX, TXT)", type=["pdf", "docx", "txt"], accept_multiple_files=False, key="jd_file_uploader_candidate")
            if st.button("Simulate Add JD from File", key="add_jd_file_btn_candidate"):
                if uploaded_file:
                    jd_text = "This is simulated content extracted from the uploaded file."
                    metadata = extract_jd_metadata(jd_text)
                    name = f"File JD: {uploaded_file.name} ({metadata.get('role', 'N/A')})"
                    st.session_state.candidate_jd_list.append({"name": name, "content": jd_text, **metadata})
                    st.success(f"✅ JD '{name}' added successfully!")
                else:
                    st.warning("Please upload a file.")

    st.markdown("---")
    
    if st.session_state.candidate_jd_list:
        if st.button("🗑️ Clear All JDs", key="clear_jds_candidate"):
            st.session_state.candidate_jd_list = []
            st.session_state.candidate_match_results = [] 
            st.success("All JDs cleared.")
            st.rerun() 

        st.subheader("Loaded Job Descriptions:")
        for idx, jd_item in enumerate(st.session_state.candidate_jd_list, 1):
            with st.expander(f"**{idx}. {jd_item['name']}** - *{jd_item.get('role', 'N/A')}*"):
                st.markdown(f"**Job Type:** {jd_item.get('job_type', 'N/A')}")
                st.markdown(f"**Key Skills:** {', '.join(jd_item.get('key_skills', ['N/A']))}")
                st.text_area("Full Job Description Content", jd_item['content'], height=200, key=f"jd_content_view_{idx}", disabled=True)


def batch_jd_match_tab_content():
    st.header("🎯 Batch JD Match: Best Matches")
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name'))

    if not is_resume_parsed:
        st.warning("Please **upload and parse your resume** or build a CV in the 'CV Management' tab first.")
    elif not st.session_state.get('candidate_jd_list'):
        st.error("Please **add Job Descriptions** in the 'JD Management' tab first.")
    else:
        if "candidate_match_results" not in st.session_state:
            st.session_state.candidate_match_results = []
            
        st.markdown(f"Matching **{st.session_state.parsed['name']}** against loaded JDs.")
            
        all_jd_names = [item['name'] for item in st.session_state.candidate_jd_list]
        selected_jd_names = st.multiselect("Select Job Descriptions", options=all_jd_names, default=all_jd_names, key='candidate_batch_jd_select')
        jds_to_match = [jd_item for jd_item in st.session_state.candidate_jd_list if jd_item['name'] in selected_jd_names]
        
        if st.button(f"Run Match Analysis on {len(jds_to_match)} Selected JD(s)", type="primary", use_container_width=True):
            if not jds_to_match:
                st.warning("Please select at least one JD to match.")
                return
                
            st.session_state.candidate_match_results = []
            results_with_score = []
            
            with st.spinner("Running AI Match Analysis... This may take a moment per JD."):
                for jd_item in jds_to_match:
                    fit_output = evaluate_jd_fit(jd_item['content'], st.session_state.parsed)
                    score_match = re.search(r'Overall Fit Score:\s*(\d+)/10', fit_output)
                    # Extract the score from the mock output
                    overall_score = score_match.group(1) if score_match else str(5) 
                    
                    results_with_score.append({
                        "jd_name": jd_item['name'],
                        "overall_score": overall_score,
                        "numeric_score": int(overall_score),
                        "full_analysis": fit_output
                    })
                
                # Sort by score (highest first)
                results_with_score.sort(key=lambda x: x['numeric_score'], reverse=True)
                
                # Assign Rank and clean up
                for i, item in enumerate(results_with_score):
                    item['rank'] = i + 1
                    del item['numeric_score']
                
                st.session_state.candidate_match_results = results_with_score
                st.success("Batch analysis complete! Results are ranked below.")

        if st.session_state.get('candidate_match_results'):
            st.markdown("#### Match Results Ranked by Fit Score")
            display_data = []
            for item in st.session_state.candidate_match_results:
                display_data.append({
                    "Rank": item.get("rank", "N/A"),
                    "Job Description (Ranked)": item["jd_name"],
                    "Fit Score (out of 10)": item["overall_score"],
                })
            
            st.dataframe(display_data, use_container_width=True, hide_index=True)

            st.markdown("##### Detailed Reports")
            for item in st.session_state.candidate_match_results:
                with st.expander(f"Rank {item.get('rank', 'N/A')} | {item['jd_name']} (Score: {item['overall_score']}/10)"):
                    st.markdown(item['full_analysis'])


def filter_jd_tab_content():
    st.header("🔍 Filter Job Descriptions by Criteria")
    if not st.session_state.get('candidate_jd_list'):
        st.info("No Job Descriptions are currently loaded in the 'JD Management' tab.")
        return

    # Extract unique roles and job types from loaded JDs
    unique_roles = ["All Roles"] + sorted(list(set([item.get('role', 'General Analyst') for item in st.session_state.candidate_jd_list])))
    unique_types = ["All Types"] + sorted(list(set([item.get('job_type', 'Full-time') for item in st.session_state.candidate_jd_list])))
    
    with st.form(key="jd_filter_form"):
        col1, col2 = st.columns(2)
        with col1:
            selected_role = st.selectbox("Filter by Role Title", options=unique_roles, key="filter_role_select")
        with col2:
            selected_type = st.selectbox("Filter by Job Type", options=unique_types, key="filter_type_select")
            
        filter_text = st.text_input("Filter by Keyword (e.g., 'Kubernetes', 'AWS')", key="filter_keyword_input")
        
        apply_filters_button = st.form_submit_button("✅ Apply Filters", type="primary", use_container_width=True)

    if apply_filters_button:
        filtered_jds = st.session_state.candidate_jd_list
        
        # 1. Filter by Role
        if selected_role != "All Roles":
            filtered_jds = [jd for jd in filtered_jds if selected_role == jd.get('role')]
            
        # 2. Filter by Type
        if selected_type != "All Types":
            filtered_jds = [jd for jd in filtered_jds if selected_type == jd.get('job_type')]
            
        # 3. Filter by Keyword
        if filter_text.strip():
            keyword = filter_text.strip().lower()
            filtered_jds = [jd for jd in filtered_jds if keyword in jd['content'].lower()]

        st.session_state.filtered_jds_display = filtered_jds
        st.success(f"Found **{len(filtered_jds)}** matching Job Descriptions.")
    
    if st.session_state.get('filtered_jds_display'):
        st.subheader(f"Matching Job Descriptions ({len(st.session_state.filtered_jds_display)} found)")
        for idx, jd in enumerate(st.session_state.filtered_jds_display, 1):
            with st.expander(f"JD {idx}: **{jd['name']}** (*{jd.get('role', 'N/A')}* / {jd.get('job_type', 'N/A')})"):
                st.text(jd['content'])
    

def resume_jd_chatbot_tab_content():
    st.header("💬 Resume/JD Chatbot (Q&A) 🤖")
    
    sub_tab_resume, sub_tab_jd = st.tabs(["👤 Chat about Your Resume", "📄 Chat about Saved JDs"])
    
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name'))

    with sub_tab_resume:
        st.markdown("### Ask any question about the currently loaded resume.")
        if not is_resume_parsed:
            st.warning("Please upload and parse a resume first.")
        else:
            if 'qa_answer_resume' not in st.session_state: st.session_state.qa_answer_resume = ""
            question = st.text_input("Your Question (about Resume)", key="resume_qa_question")
            
            if st.button("Get Answer (Resume)", key="qa_btn_resume", type="primary"):
                with st.spinner("Generating answer..."):
                    st.session_state.qa_answer_resume = qa_on_resume(question)
            
            if st.session_state.get('qa_answer_resume'):
                st.markdown("#### AI Answer")
                st.info(st.session_state.qa_answer_resume)
    
    with sub_tab_jd:
        st.markdown("### Ask any question about a saved Job Description.")
        if not st.session_state.get('candidate_jd_list'):
            st.warning("Please add Job Descriptions in the 'JD Management' tab first.")
        else:
            if 'qa_answer_jd' not in st.session_state: st.session_state.qa_answer_jd = ""
            jd_names = [jd['name'] for jd in st.session_state.candidate_jd_list]
            selected_jd_name = st.selectbox("Select Job Description to Query", options=jd_names, key="jd_qa_select")
            question = st.text_input("Your Question (about JD)", key="jd_qa_question")
            
            if st.button("Get Answer (JD)", key="qa_btn_jd", type="primary"):
                with st.spinner(f"Generating answer for {selected_jd_name}..."):
                    st.session_state.qa_answer_jd = qa_on_jd(question, selected_jd_name)

            if st.session_state.get('qa_answer_jd'):
                st.markdown(f"#### AI Answer for *{selected_jd_name}*")
                st.info(st.session_state.qa_answer_jd)


def interview_prep_tab_content():
    st.header("❓ Interview Preparation Tools")
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name'))

    if not is_resume_parsed:
        st.warning("Please upload and successfully parse a resume first.")
    else:
        if 'iq_output' not in st.session_state: st.session_state.iq_output = ""
        if 'interview_qa' not in st.session_state: st.session_state.interview_qa = [] 
        if 'evaluation_report' not in st.session_state: st.session_state.evaluation_report = "" 
        
        st.subheader("1. Generate Resume-Specific Questions")
        st.info("The AI will generate questions based on the content of the selected section in your loaded CV.")
        
        section_choice = st.selectbox("Select Section to Focus On", question_section_options, key='iq_section_c')
        
        if st.button("Generate Interview Questions", key='iq_btn_c', type="primary", use_container_width=True):
            with st.spinner(f"Generating questions based on your **{section_choice}** section..."):
                raw_questions_response = generate_interview_questions(st.session_state.parsed, section_choice)
                st.session_state.iq_output = raw_questions_response
                st.session_state.interview_qa = [] 
                
                # Mock parsing of questions for the UI
                q_list = []
                # Use the raw output if possible, otherwise use mock
                if "LLM API Call Successful" in raw_questions_response:
                    for i in range(3): 
                        q_list.append({"question": f"Question about {section_choice} #{i+1} (from LLM)", "answer": "", "level": "Intermediate"})
                else:
                    st.session_state.iq_output = raw_questions_response # Display the mock/error message
                    for i in range(3): 
                        q_list.append({"question": f"Question about {section_choice} #{i+1} (Mock)", "answer": "", "level": "Basic"})
                        
                st.session_state.interview_qa = q_list
                st.session_state.evaluation_report = "" # Clear previous report
                st.success(f"Generated {len(q_list)} questions. Scroll down to practice.")

        if st.session_state.get('interview_qa'):
            st.markdown("---")
            st.subheader("2. Practice and Record Answers")
            
            if st.button("🗑️ Clear Practice Answers and Report", on_click=clear_interview_state):
                 pass # The on_click handler does the work
            
            with st.form("interview_practice_form"):
                for i, qa_item in enumerate(st.session_state.interview_qa):
                    st.markdown(f"**Question {i+1}:** *{qa_item['question']}*")
                    answer = st.text_area(f"Your Answer for Q{i+1}", value=st.session_state.interview_qa[i]['answer'], height=100, key=f'answer_q_{i}', label_visibility='collapsed')
                    st.session_state.interview_qa[i]['answer'] = answer 
                
                submit_button = st.form_submit_button("Submit & Evaluate Answers", use_container_width=True, type="primary")

                if submit_button:
                    if all(item['answer'].strip() for item in st.session_state.interview_qa):
                        with st.spinner("Sending answers to AI Evaluator..."):
                            report = evaluate_interview_answers(st.session_state.interview_qa, st.session_state.parsed)
                            st.session_state.evaluation_report = report
                            st.success("Evaluation complete! Scroll down to see the report.")
                    else:
                        st.error("Please answer all generated questions before submitting.")
            
            if st.session_state.get('evaluation_report'):
                st.markdown("---")
                st.subheader("3. AI Evaluation Report")
                st.markdown(st.session_state.evaluation_report)


# --- 4. THE MAIN DASHBOARD FUNCTION ---

def candidate_dashboard():
    st.header("👩‍🎓 Candidate Dashboard")
    st.markdown("Welcome! Use the tabs below to manage your CV and access AI preparation tools.")

    # --- Navigation Block ---
    if st.button("🚪 Log Out", key="candidate_logout_btn"):
        go_to("login") 
    
    st.markdown("---")

    # --- Sidebar for Status ---
    with st.sidebar:
        st.header("Resume/CV Status")
        if GROQ_API_KEY == 'MOCK_KEY':
             st.warning("⚠️ **AI Disabled:** GROQ_API_KEY not set.")
        
        st.markdown("---")
        
        if st.session_state.get('parsed', {}).get("name"):
            st.success(f"Loaded CV: **{st.session_state.parsed['name']}**")
        else:
            st.info("Please upload a file or use the CV builder to begin.")
            
        if st.session_state.get('candidate_jd_list'):
            st.success(f"Loaded JDs: **{len(st.session_state.candidate_jd_list)}**")


    # Main Content Tabs (Revised Order)
    tab_cv_mgmt, tab_parsing, tab_jd_mgmt, tab_batch_match, tab_filter_jd, tab_chatbot, tab_interview_prep = st.tabs([
        "✍️ CV Management", 
        "📄 Resume Parsing", 
        "📚 JD Management", 
        "🎯 Batch JD Match",
        "🔍 Filter JD",
        "💬 Resume/JD Chatbot (Q&A)",   
        "❓ Interview Prep"             
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

# --- 5. STREAMLIT APP EXECUTION AND STATE INITIALIZATION ---
# This block simulates the main running file structure.

# Initialize Session State Variables (Crucial for Streamlit)
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
if 'qa_answer_resume' not in st.session_state: st.session_state.qa_answer_resume = ""
if 'qa_answer_jd' not in st.session_state: st.session_state.qa_answer_jd = ""


# Conditional rendering based on page state (Simulated routing)
if st.session_state.page == "candidate_dashboard":
    candidate_dashboard()
else:
    # Simulating a login screen or initial view
    st.title("Welcome to the AI Career Prep Tool")
    st.info("This is the main entry point. Since the full application routing logic is not provided, we will jump straight to the dashboard for demonstration.")
    if st.button("Go to Candidate Dashboard"):
        st.session_state.page = "candidate_dashboard"
        st.rerun()
