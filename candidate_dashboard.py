import streamlit as st
import os
import re
import tempfile
import traceback
import json
import pandas as pd
# Add any other imports your helper functions use (e.g., from pypdf2, docx, groq)
# from groq import Groq 

# --- 1. GLOBAL CONFIGURATION & SESSION STATE INITIALIZATION ---

# Initialize your API key from Streamlit Secrets
try:
    # Use st.secrets if deploying on Streamlit Cloud
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY") 
except:
    # Fallback for local testing or if st.secrets is not used
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Initialize session state variables (CRITICAL for Streamlit apps)
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'login' # Start on a 'login' or 'home' page
if 'parsed' not in st.session_state:
    st.session_state.parsed = {} # Stores the parsed JSON resume data
if 'full_text' not in st.session_state:
    st.session_state.full_text = "" # Stores the raw text of the uploaded resume
if 'pasted_cv_text' not in st.session_state:
    st.session_state.pasted_cv_text = ""
if 'excel_data' not in st.session_state:
    st.session_state.excel_data = {}
if 'candidate_uploaded_resumes' not in st.session_state:
    st.session_state.candidate_uploaded_resumes = []
if 'candidate_jd_list' not in st.session_state:
    st.session_state.candidate_jd_list = [] # List of JDs for matching
if 'candidate_match_results' not in st.session_state:
    st.session_state.candidate_match_results = []
if 'filtered_jds_display' not in st.session_state:
    st.session_state.filtered_jds_display = []
if 'iq_output' not in st.session_state: st.session_state.iq_output = ""
if 'interview_qa' not in st.session_state: st.session_state.interview_qa = [] 
if 'evaluation_report' not in st.session_state: st.session_state.evaluation_report = "" 


# Static list for interview prep section
question_section_options = ["Overall", "Experience", "Skills", "Education"] 

# --- 2. PLACEHOLDER / HELPER FUNCTIONS (REPLACE WITH YOUR CODE) ---

def go_to(page_name):
    """Function to change the application page."""
    st.session_state.current_page = page_name
    # Optional: st.rerun() if the page change doesn't trigger automatically
    # st.rerun() 

def login_page():
    """Placeholder for your login logic."""
    st.title("Welcome to the AI Career Assistant")
    if st.button("Continue to Candidate Dashboard"):
        go_to("candidate")

def cv_management_tab_content():
    """PLACEHOLDER: Implement the logic for CV Management (building, editing, downloading)."""
    st.header("✍️ CV Management")
    st.info("The CV Management logic must be implemented here.")
    if st.session_state.get('parsed', {}).get('name'):
        st.write(f"Parsed Resume Loaded: **{st.session_state.parsed['name']}**")
        # Add your CV builder/editor code here

def parse_and_store_resume(file_or_text, file_name_key, source_type):
    """
    PLACEHOLDER: Implements the logic to read a file/text and call the AI/parser.
    
    Should return a dictionary like: 
    {'parsed': {'name': '...', 'skills': [...]}, 'full_text': '...', 'excel_data': {}, 'name': '...'}
    """
    if source_type == 'text':
        name = "Pasted Text CV"
        # Implement your AI parsing logic here using file_or_text
        return {"parsed": {"name": name, "summary": "Parsed from text.", "skills": ["Python", "Streamlit"]}, 
                "full_text": file_or_text, "excel_data": {}, "name": name}
    elif source_type == 'file':
        # Implement your file reading and AI parsing logic here
        name = file_or_text.name
        return {"parsed": {"name": name, "summary": "Parsed from file.", "skills": ["Data Analysis", "API Calls"]}, 
                "full_text": "Content extracted from file...", "excel_data": {}, "name": name}
    
    return {"error": "Parsing logic not implemented yet."}


def get_file_type(path):
    """PLACEHOLDER: Function to determine file type based on extension."""
    return path.split('.')[-1].lower()

def extract_content(file_type, temp_path):
    """PLACEERHOLDER: Function to extract text from pdf/docx/txt files."""
    if file_type in ['pdf', 'docx', 'txt']:
        return "Content extracted from file..."
    return f"Error: Unsupported file type {file_type}"

def extract_jd_from_linkedin_url(url):
    """PLACEHOLDER: Function to scrape/extract JD from a LinkedIn URL."""
    return f"Simulated JD content for {url}..."

def extract_jd_metadata(text):
    """PLACEHOLDER: Function to use AI to extract role, job_type, key_skills from JD text."""
    return {"role": "Software Engineer", "job_type": "Full-Time", "key_skills": ["Python", "Streamlit"]}

def evaluate_jd_fit(jd_content, parsed_json):
    """PLACEHOLDER: Function to call AI (Groq) for JD match analysis."""
    # Simulate a full analysis report structure
    return f"""
    --- Overall Fit Score ---
    Overall Fit Score: 7/10

    --- Section Match Analysis ---
    Skills Match: 80%
    Experience Match: 65%
    Education Match: 90%

    Strengths/Matches: Candidate excels in Python and Streamlit. Experience aligns well with junior-mid level.
    Gaps/Suggestions: Needs more cloud computing experience. Answer: This is a placeholder report.
    """

def filter_jd_tab_content():
    """PLACEHOLDER: Implement the logic for the Filter JD tab."""
    st.header("🔍 Filter Job Descriptions")
    st.info("The JD filtering logic must be implemented here.")
    if st.session_state.get('candidate_jd_list'):
        st.write(f"Total JDs Loaded: {len(st.session_state.candidate_jd_list)}")
        # Add your filtering controls (e.g., multiselect by role, type)

def qa_on_resume(question):
    """PLACEHOLDER: Function to call AI (Groq) to answer questions about the resume."""
    return f"The AI will analyze the resume and answer: '{question}'."

def qa_on_jd(question, jd_name):
    """PLACEHOLDER: Function to call AI (Groq) to answer questions about the JD."""
    return f"The AI will analyze JD '{jd_name}' and answer: '{question}'."

def clear_interview_state():
    """Clears all related interview practice state when inputs change."""
    st.session_state.iq_output = ""
    st.session_state.interview_qa = [] 
    st.session_state.evaluation_report = "" 

def generate_interview_questions(parsed_resume, section):
    """PLACEHOLDER: Function to generate interview questions using AI (Groq)."""
    # Simulate the expected output format
    return f"""
    [Beginner]
    Q1: Tell me about a project where you used your skills in {section}.
    [Intermediate]
    Q2: How would you optimize the performance of the {section} section based on your experience?
    """

def evaluate_interview_answers(qa_list, parsed_resume):
    """PLACEHOLDER: Function to evaluate recorded answers using AI (Groq)."""
    return f"""
    --- Evaluation Report ---
    Overall Score: 8/10.
    Feedback for Q1: Strong and relevant experience was provided.
    Feedback for Q2: Answer was technically sound but lacked real-world examples.
    """

# --- 3. CANDIDATE DASHBOARD FUNCTION (The main UI code you requested) ---

def candidate_dashboard():
    st.header("👩‍🎓 Candidate Dashboard")
    st.markdown("Welcome! Use the tabs below to manage your CV and access AI preparation tools.")

    # --- NAVIGATION BLOCK ---
    nav_col, _ = st.columns([1, 1]) 

    with nav_col:
        if st.button("🚪 Log Out", key="candidate_logout_btn", use_container_width=True):
            go_to("login") 
    # --- END NAVIGATION BLOCK ---
    
    # Sidebar for Status Only
    with st.sidebar:
        st.header("Resume/CV Status")
        
        if st.session_state.parsed.get("name"):
            st.success(f"Currently loaded: **{st.session_state.parsed['name']}**")
        elif st.session_state.full_text:
            st.warning("Resume content is loaded, but parsing may have errors.")
        else:
            st.info("Please upload a file or use the CV builder in 'CV Management' to begin.")

    # Main Content Tabs (REARRANGED TABS HERE)
    # The order requested: CV Mgmt, Parsing, JD Mgmt, Batch Match, Filter JD, Chatbot, Interview Prep
    tab_cv_mgmt, tab_parsing, tab_jd_mgmt, tab_batch_match, tab_filter_jd, tab_chatbot, tab_interview_prep = st.tabs([
        "✍️ CV Management", 
        "📄 Resume Parsing", 
        "📚 JD Management", 
        "🎯 Batch JD Match",
        "🔍 Filter JD",
        "💬 Resume/JD Chatbot (Q&A)", 
        "❓ Interview Prep"            
    ])
    
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name')) or bool(st.session_state.get('full_text'))
    
    # --- TAB 0: CV Management ---
    with tab_cv_mgmt:
        cv_management_tab_content()

    # --- TAB 1: Resume Parsing ---
    with tab_parsing:
        st.header("Resume Upload and Parsing")
        
        # 1. Input Method Selection
        input_method = st.radio(
            "Select Input Method",
            ["Upload File", "Paste Text"],
            key="parsing_input_method"
        )
        
        st.markdown("---")

        # --- A. Upload File Method ---
        if input_method == "Upload File":
            st.markdown("### 1. Upload Resume File") 
            
            # File types
            uploaded_file = st.file_uploader( 
                "Choose PDF, DOCX, TXT, JSON, MD, CSV, XLSX file", 
                type=["pdf", "docx", "txt", "json", "md", "csv", "xlsx", "markdown", "rtf"], 
                accept_multiple_files=False, 
                key='candidate_file_upload_main'
            )
            
            st.markdown(
                """
                <div style='font-size: 10px; color: grey;'>
                Supported File Types: PDF, DOCX, TXT, JSON, MARKDOWN, CSV, XLSX, RTF
                </div>
                """, 
                unsafe_allow_html=True
            )
            st.markdown("---")

            # --- File Management Logic ---
            if uploaded_file is not None:
                if not st.session_state.candidate_uploaded_resumes or st.session_state.candidate_uploaded_resumes[0].name != uploaded_file.name:
                    st.session_state.candidate_uploaded_resumes = [uploaded_file] 
                    st.session_state.pasted_cv_text = ""
                    st.toast("Resume file uploaded successfully.")
            elif st.session_state.candidate_uploaded_resumes and uploaded_file is None:
                st.session_state.candidate_uploaded_resumes = []
                st.session_state.parsed = {}
                st.session_state.full_text = ""
                st.toast("Upload cleared.")
            
            file_to_parse = st.session_state.candidate_uploaded_resumes[0] if st.session_state.candidate_uploaded_resumes else None
            
            st.markdown("### 2. Parse Uploaded File")
            
            if file_to_parse:
                if st.button(f"Parse and Load: **{file_to_parse.name}**", use_container_width=True):
                    with st.spinner(f"Parsing {file_to_parse.name}..."):
                        # Ensure the file is saved temporarily for parsing if needed
                        temp_dir = tempfile.mkdtemp()
                        temp_path = os.path.join(temp_dir, file_to_parse.name)
                        with open(temp_path, "wb") as f:
                            f.write(file_to_parse.getbuffer())
                            
                        # Pass the path to your parsing function
                        result = parse_and_store_resume(temp_path, file_name_key='single_resume_candidate', source_type='file')
                        
                        if "error" not in result:
                            st.session_state.parsed = result['parsed']
                            st.session_state.full_text = result['full_text']
                            st.session_state.excel_data = result['excel_data'] 
                            st.session_state.parsed['name'] = result['name'] 
                            clear_interview_state()
                            st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                            st.info("View, edit, and download the parsed data in the **CV Management** tab.") 
                        else:
                            st.error(f"Parsing failed for {file_to_parse.name}: {result['error']}")
                            st.session_state.parsed = {"error": result['error'], "name": result['name']}
                            st.session_state.full_text = result['full_text'] or ""
                        # Clean up temp file
                        os.remove(temp_path)
                        os.rmdir(temp_dir)
            else:
                st.info("No resume file is currently uploaded. Please upload a file above.")

        # --- B. Paste Text Method ---
        else: # input_method == "Paste Text"
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
                if st.button("Parse and Load Pasted Text", use_container_width=True):
                    with st.spinner("Parsing pasted text..."):
                        st.session_state.candidate_uploaded_resumes = []
                        
                        result = parse_and_store_resume(pasted_text, file_name_key='single_resume_candidate', source_type='text')
                        
                        if "error" not in result:
                            st.session_state.parsed = result['parsed']
                            st.session_state.full_text = result['full_text']
                            st.session_state.excel_data = result['excel_data'] 
                            st.session_state.parsed['name'] = result['name'] 
                            clear_interview_state()
                            st.success(f"✅ Successfully loaded and parsed **{result['name']}**.")
                            st.info("View, edit, and download the parsed data in the **CV Management** tab.") 
                        else:
                            st.error(f"Parsing failed: {result['error']}")
                            st.session_state.parsed = {"error": result['error'], "name": result['name']}
                            st.session_state.full_text = result['full_text'] or ""
            else:
                st.info("Please paste your CV text into the box above.")

    # --- TAB 2: JD Management (Candidate) ---
    with tab_jd_mgmt:
        st.header("📚 Manage Job Descriptions for Matching")
        st.markdown("Add multiple JDs here to compare your resume against them in the next tabs.")
        
        jd_type = st.radio("Select JD Type", ["Single JD", "Multiple JD"], key="jd_type_candidate")
        st.markdown("### Add JD by:")
        
        method = st.radio("Choose Method", ["Upload File", "Paste Text", "LinkedIn URL"], key="jd_add_method_candidate") 

        # URL
        if method == "LinkedIn URL":
            url_list = st.text_area(
                "Enter one or more URLs (comma separated)" if jd_type == "Multiple JD" else "Enter URL", key="url_list_candidate"
            )
            if st.button("Add JD(s) from URL", key="add_jd_url_btn_candidate"):
                if url_list:
                    urls = [u.strip() for u in url_list.split(",")] if jd_type == "Multiple JD" else [url_list.strip()]
                    
                    count = 0
                    for url in urls:
                        if not url: continue
                        
                        with st.spinner(f"Attempting JD extraction and metadata analysis for: {url}"):
                            jd_text = extract_jd_from_linkedin_url(url)
                            metadata = extract_jd_metadata(jd_text) 
                        
                        name_base = url.split('/jobs/view/')[-1].split('/')[0] if '/jobs/view/' in url else f"URL {count+1}"
                        name = f"JD from URL: {name_base}" 
                        if name in [item['name'] for item in st.session_state.candidate_jd_list]:
                            name = f"JD from URL: {name_base} ({len(st.session_state.candidate_jd_list) + 1})" 

                        st.session_state.candidate_jd_list.append({"name": name, "content": jd_text, **metadata}) 
                        
                        if not jd_text.startswith("[Error"):
                            count += 1
                                
                    if count > 0:
                        st.success(f"✅ {count} JD(s) added successfully!")
                    else:
                        st.error("No JDs were added successfully.")


        # Paste Text
        elif method == "Paste Text":
            text_list = st.text_area(
                "Paste one or more JD texts (separate by '---')" if jd_type == "Multiple JD" else "Paste JD text here", key="text_list_candidate"
            )
            if st.button("Add JD(s) from Text", key="add_jd_text_btn_candidate"):
                if text_list:
                    texts = [t.strip() for t in text_list.split("---")] if jd_type == "Multiple JD" else [text_list.strip()]
                    for i, text in enumerate(texts):
                         if text:
                            name_base = text.splitlines()[0].strip()
                            if len(name_base) > 30: name_base = f"{name_base[:27]}..."
                            if not name_base: name_base = f"Pasted JD {len(st.session_state.candidate_jd_list) + i + 1}"
                            
                            metadata = extract_jd_metadata(text) 
                            st.session_state.candidate_jd_list.append({"name": name_base, "content": text, **metadata}) 
                    st.success(f"✅ {len(texts)} JD(s) added successfully!")

        # Upload File
        elif method == "Upload File":
            uploaded_files = st.file_uploader(
                "Upload JD file(s)",
                type=["pdf", "txt", "docx"],
                accept_multiple_files=(jd_type == "Multiple JD"), 
                key="jd_file_uploader_candidate"
            )
            if st.button("Add JD(s) from File", key="add_jd_file_btn_candidate"):
                if uploaded_files is None:
                    st.warning("Please upload file(s).")
                    
                files_to_process = uploaded_files if isinstance(uploaded_files, list) else ([uploaded_files] if uploaded_files else [])
                
                count = 0
                for file in files_to_process:
                    if file:
                        temp_dir = tempfile.mkdtemp()
                        temp_path = os.path.join(temp_dir, file.name)
                        with open(temp_path, "wb") as f:
                            f.write(file.getbuffer())
                            
                        file_type = get_file_type(temp_path)
                        jd_text = extract_content(file_type, temp_path)
                        
                        if not jd_text.startswith("Error"):
                            metadata = extract_jd_metadata(jd_text) 
                            st.session_state.candidate_jd_list.append({"name": file.name, "content": jd_text, **metadata})
                            count += 1
                        else:
                            st.error(f"Error extracting content from {file.name}: {jd_text}")
                            
                        os.remove(temp_path)
                        os.rmdir(temp_dir)
                            
                if count > 0:
                    st.success(f"✅ {count} JD(s) added successfully!")
                elif uploaded_files:
                    st.error("No valid JD files were uploaded or content extraction failed.")


        # Display Added JDs
        if st.session_state.candidate_jd_list:
            
            col_display_header, col_clear_button = st.columns([3, 1])
            
            with col_display_header:
                st.markdown("### ✅ Current JDs Added:")
                
            with col_clear_button:
                if st.button("🗑️ Clear All JDs", key="clear_jds_candidate", use_container_width=True, help="Removes all currently loaded JDs."):
                    st.session_state.candidate_jd_list = []
                    st.session_state.candidate_match_results = [] 
                    st.session_state.filtered_jds_display = [] 
                    st.success("All JDs and associated match results have been cleared.")
                    st.rerun() 

            for idx, jd_item in enumerate(st.session_state.candidate_jd_list, 1):
                title = jd_item['name']
                display_title = title.replace("--- Simulated JD for: ", "")
                with st.expander(f"JD {idx}: {display_title} | Role: {jd_item.get('role', 'N/A')}"):
                    st.markdown(f"**Job Type:** {jd_item.get('job_type', 'N/A')} | **Key Skills:** {', '.join(jd_item.get('key_skills', ['N/A']))}") 
                    st.markdown("---")
                    st.text(jd_item['content'])
        else:
            st.info("No Job Descriptions added yet.")

    # --- TAB 3: Batch JD Match (Candidate) ---
    with tab_batch_match:
        st.header("🎯 Batch JD Match: Best Matches")
        st.markdown("Compare your current resume against all saved job descriptions.")

        if not is_resume_parsed:
            st.warning("Please **upload and parse your resume** in the 'Resume Parsing' tab or **build your CV** in the 'CV Management' tab first.")
        
        elif not st.session_state.candidate_jd_list:
            st.error("Please **add Job Descriptions** in the 'JD Management' tab (Tab 3) before running batch analysis.")
            
        elif not GROQ_API_KEY:
             st.error("Cannot use JD Match: **GROQ_API_KEY** is not configured in Streamlit Secrets.")
             
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
            
            jds_to_match = [
                jd_item for jd_item in st.session_state.candidate_jd_list 
                if jd_item['name'] in selected_jd_names
            ]
            
            if st.button(f"Run Match Analysis on {len(jds_to_match)} Selected JD(s)"):
                st.session_state.candidate_match_results = []
                
                if not jds_to_match:
                    st.warning("Please select at least one Job Description to run the analysis.")
                    
                else:
                    resume_name = st.session_state.parsed.get('name', 'Uploaded Resume')
                    parsed_json = st.session_state.parsed
                    results_with_score = []

                    with st.spinner(f"Matching {resume_name}'s resume against {len(jds_to_match)} selected JD(s)..."):
                        
                        for jd_item in jds_to_match:
                            
                            jd_name = jd_item['name']
                            jd_content = jd_item['content']

                            try:
                                fit_output = evaluate_jd_fit(jd_content, parsed_json)
                                
                                # Use regex to extract data from the analysis report (adjust patterns if needed)
                                overall_score_match = re.search(r'Overall Fit Score:\s*[^\d]*(\d+)\s*/10', fit_output, re.IGNORECASE)
                                section_analysis_match = re.search(
                                    r'--- Section Match Analysis ---\s*(.*?)\s*Strengths/Matches:', 
                                    fit_output, re.DOTALL
                                )

                                skills_percent, experience_percent, education_percent = 'N/A', 'N/A', 'N/A'
                                
                                if section_analysis_match:
                                    section_text = section_analysis_match.group(1)
                                    skills_match = re.search(r'Skills Match:\s*\[?(\d+)%\]?', section_text, re.IGNORECASE)
                                    experience_match = re.search(r'Experience Match:\s*\[?(\d+)%\]?', section_text, re.IGNORECASE)
                                    education_match = re.search(r'Education Match:\s*\[?(\d+)%\]?', section_text, re.IGNORECASE)
                                    
                                    if skills_match: skills_percent = skills_match.group(1)
                                    if experience_match: experience_percent = experience_match.group(1)
                                    if education_match: education_percent = education_match.group(1)
                                
                                overall_score = overall_score_match.group(1) if overall_score_match else 'N/A'

                                results_with_score.append({
                                    "jd_name": jd_name,
                                    "overall_score": overall_score,
                                    "numeric_score": int(overall_score) if overall_score.isdigit() else -1, 
                                    "skills_percent": skills_percent,
                                    "experience_percent": experience_percent, 
                                    "education_percent": education_percent,   
                                    "full_analysis": fit_output
                                })
                            except Exception as e:
                                results_with_score.append({
                                    "jd_name": jd_name,
                                    "overall_score": "Error",
                                    "numeric_score": -1, 
                                    "skills_percent": "Error",
                                    "experience_percent": "Error", 
                                    "education_percent": "Error",   
                                    "full_analysis": f"Error running analysis for {jd_name}: {e}\n{traceback.format_exc()}"
                                })
                                
                        # Ranking Logic
                        results_with_score.sort(key=lambda x: x['numeric_score'], reverse=True)
                        
                        current_rank = 1
                        current_score = -1 
                        
                        for i, item in enumerate(results_with_score):
                            if item['numeric_score'] > current_score:
                                current_rank = i + 1
                                current_score = item['numeric_score']
                            
                            item['rank'] = current_rank
                            del item['numeric_score'] 
                            
                        st.session_state.candidate_match_results = results_with_score
                        st.success("Batch analysis complete!")


            # Display Results 
            if st.session_state.get('candidate_match_results'):
                st.markdown("#### Match Results for Your Resume")
                results_df = st.session_state.candidate_match_results
                
                display_data = []
                for item in results_df:
                    full_jd_item = next((jd for jd in st.session_state.candidate_jd_list if jd['name'] == item['jd_name']), {})
                    
                    display_data.append({
                        "Rank": item.get("rank", "N/A"),
                        "Job Description (Ranked)": item["jd_name"].replace("--- Simulated JD for: ", ""),
                        "Role": full_jd_item.get('role', 'N/A'), 
                        "Job Type": full_jd_item.get('job_type', 'N/A'), 
                        "Fit Score (out of 10)": item["overall_score"],
                        "Skills (%)": item.get("skills_percent", "N/A"),
                        "Experience (%)": item.get("experience_percent", "N/A"), 
                        "Education (%)": item.get("education_percent", "N/A"),   
                    })

                st.dataframe(display_data, use_container_width=True)

                st.markdown("##### Detailed Reports")
                for item in results_df:
                    rank_display = f"Rank {item.get('rank', 'N/A')} | "
                    header_text = f"{rank_display}Report for **{item['jd_name'].replace('--- Simulated JD for: ', '')}** (Score: **{item['overall_score']}/10** | S: **{item.get('skills_percent', 'N/A')}%** | E: **{item.get('experience_percent', 'N/A')}%** | Edu: **{item.get('education_percent', 'N/A')}%**)"
                    with st.expander(header_text):
                        st.markdown(item['full_analysis'])

    # --- TAB 4: Filter JD ---
    with tab_filter_jd:
        filter_jd_tab_content()

    # --- TAB 5: Resume/JD Chatbot (Q&A) ---
    with tab_chatbot:
        st.header("Resume/JD Chatbot (Q&A) 💬")
        
        # --- NESTED TABS ---
        sub_tab_resume, sub_tab_jd = st.tabs([
            "👤 Chat about Your Resume",
            "📄 Chat about Saved JDs"
        ])
        
        # --- 5A. RESUME CHATBOT CONTENT ---
        with sub_tab_resume:
            st.markdown("### Ask any question about the currently loaded resume.")
            if not is_resume_parsed:
                st.warning("Please upload and parse a resume in the 'Resume Parsing' tab or use the 'CV Management' tab first.")
            elif "error" in st.session_state.parsed:
                 st.error("Cannot use Resume Chatbot: Resume data has parsing errors.")
            elif not GROQ_API_KEY:
                 st.error("Cannot use Chatbot: **GROQ_API_KEY** is not configured.")
            else:
                if 'qa_answer_resume' not in st.session_state: st.session_state.qa_answer_resume = ""
                
                question = st.text_input(
                    "Your Question (about Resume)", 
                    placeholder="e.g., What are the candidate's key skills?",
                    key="resume_qa_question"
                )
                
                if st.button("Get Answer (Resume)", key="qa_btn_resume"):
                    with st.spinner("Generating answer..."):
                        try:
                            answer = qa_on_resume(question)
                            st.session_state.qa_answer_resume = answer
                        except Exception as e:
                            st.error(f"Error during Resume Q&A: {e}")
                            st.session_state.qa_answer_resume = "Could not generate an answer."

                if st.session_state.get('qa_answer_resume'):
                    st.text_area("Answer (Resume)", st.session_state.qa_answer_resume, height=150)
        
        # --- 5B. JD CHATBOT CONTENT ---
        with sub_tab_jd:
            st.markdown("### Ask any question about a saved Job Description.")
            
            if not st.session_state.candidate_jd_list:
                st.warning("Please add Job Descriptions in the 'JD Management' tab (Tab 3) first.")
            elif not GROQ_API_KEY:
                 st.error("Cannot use JD Chatbot: **GROQ_API_KEY** is not configured.")
            else:
                if 'qa_answer_jd' not in st.session_state: st.session_state.qa_answer_jd = ""

                # 1. JD Selection
                jd_names = [jd['name'] for jd in st.session_state.candidate_jd_list]
                selected_jd_name = st.selectbox(
                    "Select Job Description to Query",
                    options=jd_names,
                    key="jd_qa_select"
                )
                
                # 2. Question Input
                question = st.text_input(
                    "Your Question (about JD)", 
                    placeholder="e.g., What is the minimum experience required for this role?",
                    key="jd_qa_question"
                )
                
                # 3. Get Answer Button
                if st.button("Get Answer (JD)", key="qa_btn_jd"):
                    if selected_jd_name and question.strip():
                        with st.spinner(f"Generating answer for {selected_jd_name}..."):
                            try:
                                answer = qa_on_jd(question, selected_jd_name)
                                st.session_state.qa_answer_jd = answer
                            except Exception as e:
                                st.error(f"Error during JD Q&A: {e}")
                                st.session_state.qa_answer_jd = "Could not generate an answer."

                # 4. Answer Output
                if st.session_state.get('qa_answer_jd'):
                    st.text_area("Answer (JD)", st.session_state.qa_answer_jd, height=150)


    # --- TAB 6: Interview Prep ---
    with tab_interview_prep:
        st.header("Interview Preparation Tools")
        if not is_resume_parsed or "error" in st.session_state.parsed:
            st.warning("Please upload and successfully parse a resume first.")
        elif not GROQ_API_KEY:
             st.error("Cannot use Interview Prep: **GROQ_API_KEY** is not configured.")
        else:
            if 'iq_output' not in st.session_state: st.session_state.iq_output = ""
            if 'interview_qa' not in st.session_state: st.session_state.interview_qa = [] 
            if 'evaluation_report' not in st.session_state: st.session_state.evaluation_report = "" 
            
            st.subheader("1. Generate Interview Questions")
            
            section_choice = st.selectbox(
                "Select Section", 
                question_section_options, 
                key='iq_section_c',
                on_change=clear_interview_state 
            )
            
            if st.button("Generate Interview Questions", key='iq_btn_c'):
                with st.spinner("Generating questions..."):
                    try:
                        raw_questions_response = generate_interview_questions(st.session_state.parsed, section_choice)
                        st.session_state.iq_output = raw_questions_response
                        
                        st.session_state.interview_qa = [] 
                        st.session_state.evaluation_report = "" 
                        
                        # Parsing the generated questions (adjust logic based on your AI output)
                        q_list = []
                        current_level = ""
                        for line in raw_questions_response.splitlines():
                            line = line.strip()
                            if line.startswith('[') and line.endswith(']'):
                                current_level = line.strip('[]')
                            elif line.lower().startswith('q') and ':' in line:
                                question_text = line[line.find(':') + 1:].strip()
                                q_list.append({
                                    "question": f"({current_level}) {question_text}",
                                    "answer": "", 
                                    "level": current_level
                                })
                                
                        st.session_state.interview_qa = q_list
                        
                        st.success(f"Generated {len(q_list)} questions based on your **{section_choice}** section.")
                        
                    except Exception as e:
                        st.error(f"Error generating questions: {e}")
                        st.session_state.iq_output = "Error generating questions."
                        st.session_state.interview_qa = []

            if st.session_state.get('interview_qa'):
                st.markdown("---")
                st.subheader("2. Practice and Record Answers")
                
                with st.form("interview_practice_form"):
                    
                    for i, qa_item in enumerate(st.session_state.interview_qa):
                        st.markdown(f"**Question {i+1}:** {qa_item['question']}")
                        
                        answer = st.text_area(
                            f"Your Answer for Q{i+1}", 
                            value=st.session_state.interview_qa[i]['answer'], 
                            height=100,
                            key=f'answer_q_{i}',
                            label_visibility='collapsed'
                        )
                        st.session_state.interview_qa[i]['answer'] = answer 
                        st.markdown("---") 
                        
                    submit_button = st.form_submit_button("Submit & Evaluate Answers", use_container_width=True)

                    if submit_button:
                        
                        if all(item['answer'].strip() for item in st.session_state.interview_qa):
                            with st.spinner("Sending answers to AI Evaluator..."):
                                try:
                                    report = evaluate_interview_answers(
                                        st.session_state.interview_qa,
                                        st.session_state.parsed
                                    )
                                    st.session_state.evaluation_report = report
                                    st.success("Evaluation complete! See the report below.")
                                except Exception as e:
                                    st.error(f"Evaluation failed: {e}")
                                    st.session_state.evaluation_report = f"Evaluation failed: {e}\n{traceback.format_exc()}"
                        else:
                            st.error("Please answer all generated questions before submitting.")
                
                if st.session_state.get('evaluation_report'):
                    st.markdown("---")
                    st.subheader("3. AI Evaluation Report")
                    st.markdown(st.session_state.evaluation_report)

# --- 4. MAIN APPLICATION ENTRY POINT ---

if __name__ == '__main__':
    st.set_page_config(page_title="Candidate AI Dashboard", layout="wide")
    
    # Simple Router: Directs the user to the correct function based on session state
    if st.session_state.current_page == 'login':
        login_page()
    elif st.session_state.current_page == 'candidate':
        candidate_dashboard()
    # Add other pages as needed
    else:
        login_page() # Default fallback
