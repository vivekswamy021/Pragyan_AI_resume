import streamlit as st
import os
import tempfile
import json
import re
import traceback
import pandas as pd
from datetime import date

# --- 1. GLOBAL CONFIGURATION AND INITIAL STATE ---

# NOTE: Replace with your actual Groq API Key setup.
# In a real deployment, you would use st.secrets or os.environ
GROQ_API_KEY = os.environ.get('GROQ_API_KEY') or st.secrets.get('GROQ_API_KEY', 'YOUR_PLACEHOLDER_KEY')

# Global Session State Initializer
def initialize_session_state():
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "login" # Start at login
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None
    if 'parsed' not in st.session_state:
        st.session_state.parsed = {}  # Parsed resume data (JSON-like)
    if 'full_text' not in st.session_state:
        st.session_state.full_text = "" # Full resume text
    if 'excel_data' not in st.session_state:
        st.session_state.excel_data = {} # Data extracted for Excel/CSV
    if 'candidate_uploaded_resumes' not in st.session_state:
        st.session_state.candidate_uploaded_resumes = [] # For uploader files
    if 'candidate_jd_list' not in st.session_state:
        st.session_state.candidate_jd_list = [] # List of JDs for candidate matching
    if 'candidate_match_results' not in st.session_state:
        st.session_state.candidate_match_results = [] # Results of batch matching
    if 'pasted_cv_text' not in st.session_state:
        st.session_state.pasted_cv_text = ""
    if 'filtered_jds_display' not in st.session_state:
        st.session_state.filtered_jds_display = [] # For Filter JD tab

# Utility for navigation
def go_to(page):
    st.session_state.current_page = page

# Utility for interview prep state reset
def clear_interview_state():
    st.session_state.iq_output = ""
    st.session_state.interview_qa = []
    st.session_state.evaluation_report = ""

# Dropdown options for Interview Prep tab
question_section_options = [
    "Overall Experience & Summary", 
    "Education", 
    "Skills", 
    "Projects", 
    "Specific Work Experience"
]

# --- 2. PLACEHOLDER / HELPER FUNCTIONS (MUST BE IMPLEMENTED) ---

# Replace these with your actual resume parsing/data extraction logic
def parse_and_store_resume(file_or_text, file_name_key, source_type='file'):
    """Placeholder for the resume parsing logic."""
    if GROQ_API_KEY == 'YOUR_PLACEHOLDER_KEY':
        return {"error": "GROQ_API_KEY not configured. Cannot parse.", "name": "Error_File"}
    
    # --- YOUR ACTUAL PARSING LOGIC GOES HERE ---
    
    # Simulated successful output structure:
    if source_type == 'file' and file_or_text.name.endswith('.pdf'):
        full_text = f"This is the full text of {file_or_text.name}."
        parsed_data = {"name": file_or_text.name, "email": "test@example.com", "skills": ["Python", "Streamlit"]}
        excel_data = {"Name": [file_or_text.name], "Email": ["test@example.com"], "Skills": ["Python, Streamlit"]}
        return {"parsed": parsed_data, "full_text": full_text, "excel_data": excel_data, "name": file_or_text.name}
    elif source_type == 'text':
        name = "Pasted CV"
        full_text = file_or_text[:100] + "..."
        parsed_data = {"name": name, "email": "pasted@example.com", "skills": ["PlaceholderSkill1", "PlaceholderSkill2"]}
        excel_data = {"Name": [name], "Email": ["pasted@example.com"], "Skills": ["PlaceholderSkill1, PlaceholderSkill2"]}
        return {"parsed": parsed_data, "full_text": full_text, "excel_data": excel_data, "name": name}
    
    # Simulated failed output
    return {"error": "Parsing failed for unknown reason. Check logs.", "name": "Simulated_Failure"}

def get_file_type(path):
    return os.path.splitext(path)[1].lower().strip('.')

def extract_content(file_type, path):
    """Placeholder for file content extraction (PDF, DOCX, TXT)."""
    if file_type in ['pdf', 'docx', 'txt']:
        return f"Simulated content extracted from {path}. This is where the JD text would be."
    return "Error: Unsupported file type"

def extract_jd_from_linkedin_url(url):
    """Placeholder for LinkedIn JD scraper/extractor."""
    return f"--- Simulated JD for: {url} ---\nRole: AI Engineer\nRequirements: 5+ years experience, Python, Groq."

def extract_jd_metadata(jd_text):
    """Placeholder for extracting structured data from JD text."""
    return {
        "role": "Software Developer (Simulated)",
        "job_type": "Full-time (Simulated)",
        "key_skills": ["Python", "SQL", "Cloud"]
    }

def evaluate_jd_fit(jd_content, parsed_json):
    """Placeholder for the Groq-based JD fit analysis."""
    return f"""
    --- JD Fit Analysis for {parsed_json.get('name', 'CV')} ---
    Overall Fit Score: 7/10
    
    --- Section Match Analysis ---
    Skills Match: 80%
    Experience Match: 60%
    Education Match: 90%
    
    Strengths/Matches: Found Python, SQL, and 3 years experience.
    Weaknesses/Gaps: Missing specific Cloud certification.
    """

def qa_on_resume(question):
    """Placeholder for Groq-based Q&A on resume data."""
    return f"Based on the parsed resume data (skills: {st.session_state.parsed.get('skills')}), the answer to '{question}' is: Placeholder Response."
    
def qa_on_jd(question, selected_jd_name):
    """Placeholder for Groq-based Q&A on JD content."""
    jd_item = next(jd for jd in st.session_state.candidate_jd_list if jd['name'] == selected_jd_name)
    return f"Based on the JD for '{selected_jd_name}' (Role: {jd_item.get('role')}), the answer to '{question}' is: Placeholder JD Response."

def generate_interview_questions(parsed_json, section_choice):
    """Placeholder for Groq-based interview question generation."""
    return f"""
    [Behavioral]
    Q1: Tell me about a time you faced a difficult technical challenge related to your {section_choice}.
    [Technical]
    Q2: Explain the difference between Python lists and tuples.
    """

def evaluate_interview_answers(qa_list, parsed_json):
    """Placeholder for Groq-based answer evaluation."""
    total_q = len(qa_list)
    return f"""
    ## 📝 Interview Evaluation Report ({total_q} Questions)
    
    **Candidate:** {parsed_json.get('name', 'N/A')}
    **Evaluation Focus:** {st.session_state.iq_section_c}
    
    ### Overall Score: 8.5/10
    
    ### Key Feedback:
    * **Strengths:** Answers to technical questions (Q2) were clear and demonstrated solid foundational knowledge.
    * **Areas for Improvement:** The behavioral response (Q1) lacked specific details (STAR format). Use stronger, quantifiable achievements.
    
    ### Detail Breakdown:
    * **Q1 (Behavioral):** Good attempt, but needs more structure. (Score: 7/10)
    * **Q2 (Technical):** Excellent, precise answer. (Score: 10/10)
    """

# --- 3. TAB CONTENT PLACEHOLDER FUNCTIONS ---

def login_page():
    # This page is required to start the application
    st.title("🔐 Login")
    
    username = st.text_input("Username", value="candidate")
    password = st.text_input("Password", type="password", value="password")
    
    if st.button("Login"):
        if username == "candidate" and password == "password":
            st.session_state.logged_in = True
            st.session_state.user_role = "candidate"
            st.success("Logged in successfully!")
            go_to("candidate_dashboard")
            st.rerun()
        else:
            st.error("Invalid username or password.")
            
def cv_management_tab_content():
    """Placeholder for the CV Management tab logic."""
    st.header("✍️ CV Management")
    if not st.session_state.parsed:
        st.warning("No resume data loaded. Please upload and parse your CV in the 'Resume Parsing' tab.")
        return

    st.subheader(f"Data for: **{st.session_state.parsed.get('name', 'N/A')}**")
    
    # Display Parsed Data (as JSON)
    with st.expander("View/Edit Parsed Data (JSON format)"):
        st.json(st.session_state.parsed)
    
    # Display Full Text
    with st.expander("View Extracted Full Text"):
        st.text_area("Raw Text", st.session_state.full_text, height=200)

    # Download Buttons
    st.subheader("Download Data")
    col1, col2 = st.columns(2)
    
    # Download Parsed Data as JSON
    parsed_json_str = json.dumps(st.session_state.parsed, indent=4)
    col1.download_button(
        label="Download Parsed JSON",
        data=parsed_json_str,
        file_name=f"parsed_data_{date.today()}.json",
        mime="application/json",
        use_container_width=True
    )
    
    # Download Excel Data
    if st.session_state.excel_data:
        df = pd.DataFrame(st.session_state.excel_data)
        
        # Convert DataFrame to Excel bytes
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='ParsedData')
        excel_buffer.seek(0)
        
        col2.download_button(
            label="Download Parsed Excel/CSV",
            data=excel_buffer,
            file_name=f"parsed_data_{date.today()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        col2.info("No structured data for Excel/CSV.")

# Note: Added io import at top if needed for the excel download button
import io

def filter_jd_tab_content():
    """Placeholder for the Filter JD tab logic."""
    st.header("🔍 Filter Job Descriptions")
    st.markdown("Use this to quickly filter saved JDs based on metadata and your resume.")

    if not st.session_state.candidate_jd_list:
        st.error("Please add Job Descriptions in the 'JD Management' tab first.")
        return

    if not st.session_state.parsed:
        st.warning("No resume loaded. The relevance filter will be less effective.")
        
    jd_df = pd.DataFrame(st.session_state.candidate_jd_list)
    
    # --- Filter Controls ---
    col_filters, col_skill = st.columns([1, 1.5])

    with col_filters:
        unique_roles = jd_df['role'].unique().tolist()
        selected_roles = st.multiselect("Filter by Role:", options=unique_roles, default=unique_roles)

        unique_types = jd_df['job_type'].unique().tolist()
        selected_types = st.multiselect("Filter by Job Type:", options=unique_types, default=unique_types)
        
    with col_skill:
        # Get all unique skills from all JDs
        all_skills = set()
        for skill_list in jd_df['key_skills'].tolist():
            if isinstance(skill_list, list):
                for skill in skill_list:
                    all_skills.add(skill)
        
        sorted_skills = sorted(list(all_skills))
        selected_skills = st.multiselect("Filter by Required Key Skills (AND logic):", options=sorted_skills)


    # --- Application of Filters ---
    filtered_df = jd_df[jd_df['role'].isin(selected_roles) & jd_df['job_type'].isin(selected_types)]

    # Apply Skill Filter (AND logic: JD must have ALL selected skills)
    if selected_skills:
        skill_mask = filtered_df['key_skills'].apply(lambda skills: all(skill in skills for skill in selected_skills))
        filtered_df = filtered_df[skill_mask]

    # --- Display Results ---
    st.markdown("---")
    st.subheader(f"Displaying {len(filtered_df)} of {len(jd_df)} JDs")

    if not filtered_df.empty:
        # Columns to display in the result table
        display_cols = ['name', 'role', 'job_type', 'key_skills']
        display_df = filtered_df[display_cols].copy()
        
        # Format for better display
        display_df.rename(columns={'name': 'JD Name', 'role': 'Role', 'job_type': 'Job Type', 'key_skills': 'Key Skills'}, inplace=True)
        display_df['Key Skills'] = display_df['Key Skills'].apply(lambda x: ', '.join(x) if isinstance(x, list) else 'N/A')
        
        st.dataframe(display_df, use_container_width=True)
        
        # Optional: Detailed View
        with st.expander("View Full Content of Filtered JDs"):
            for index, row in filtered_df.iterrows():
                st.markdown(f"**{row['name']}** (Role: {row['role']})")
                st.text(row['content'])
                st.markdown("---")
    else:
        st.info("No Job Descriptions match the selected criteria.")


# --- 4. THE CANDIDATE DASHBOARD FUNCTION (PROVIDED IN PREVIOUS RESPONSE) ---
# NOTE: The provided function is included below. It relies on all the
# placeholder functions and session state variables defined above.

def candidate_dashboard():
    st.header("👩‍🎓 Candidate Dashboard")
    st.markdown("Welcome! Use the tabs below to manage your CV and access AI preparation tools.")

    # --- MODIFIED NAVIGATION BLOCK ---
    nav_col, _ = st.columns([1, 1]) 

    with nav_col:
        if st.button("🚪 Log Out", key="candidate_logout_btn", use_container_width=True):
            go_to("login") 
    # --- END MODIFIED NAVIGATION BLOCK ---
    
    # Sidebar for Status Only
    with st.sidebar:
        st.header("Resume/CV Status")
        
        # Check if a resume is currently loaded into the main parsing variables
        if st.session_state.parsed.get("name"):
            st.success(f"Currently loaded: **{st.session_state.parsed['name']}**")
        elif st.session_state.full_text:
            st.warning("Resume content is loaded, but parsing may have errors.")
        else:
            st.info("Please upload a file or use the CV builder in 'CV Management' to begin.")

    # Main Content Tabs (REARRANGED TABS HERE)
    # The order has been changed to move tab_chatbot (formerly 2) and tab_interview_prep (formerly 3) to the end.
    tab_cv_mgmt, tab_parsing, tab_jd_mgmt, tab_batch_match, tab_filter_jd, tab_chatbot, tab_interview_prep = st.tabs([
        "✍️ CV Management", 
        "📄 Resume Parsing", 
        "📚 JD Management", 
        "🎯 Batch JD Match",
        "🔍 Filter JD",
        "💬 Resume/JD Chatbot (Q&A)", # MOVED TO END
        "❓ Interview Prep"            # MOVED TO END
    ])
    
    is_resume_parsed = bool(st.session_state.get('parsed', {}).get('name')) or bool(st.session_state.get('full_text'))
    
    # --- TAB 0: CV Management ---
    with tab_cv_mgmt:
        cv_management_tab_content()

    # --- TAB 1 (Now tab_parsing): Resume Parsing (MODIFIED: Added Paste Your CV option) ---
    with tab_parsing:
        st.header("Resume Upload and Parsing")
        
        # 1. Input Method Selection
        input_method = st.radio(
            "Select Input Method",
            ["Upload File", "Paste Text"],
            key="parsing_input_method"
        )
        
        st.markdown("---")

        # --- A. Upload File Method (UPDATED FILE TYPES HERE) ---
        if input_method == "Upload File":
            st.markdown("### 1. Upload Resume File") 
            
            # 🚨 File types expanded here
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
                # Only store the single uploaded file if it's new
                if not st.session_state.candidate_uploaded_resumes or st.session_state.candidate_uploaded_resumes[0].name != uploaded_file.name:
                    st.session_state.candidate_uploaded_resumes = [uploaded_file] 
                    st.session_state.pasted_cv_text = "" # Clear pasted text
                    st.toast("Resume file uploaded successfully.")
            elif st.session_state.candidate_uploaded_resumes and uploaded_file is None:
                # Case where the file is removed from the uploader
                st.session_state.candidate_uploaded_resumes = []
                st.session_state.parsed = {}
                st.session_state.full_text = ""
                st.toast("Upload cleared.")
            
            file_to_parse = st.session_state.candidate_uploaded_resumes[0] if st.session_state.candidate_uploaded_resumes else None
            
            st.markdown("### 2. Parse Uploaded File")
            
            if file_to_parse:
                if st.button(f"Parse and Load: **{file_to_parse.name}**", use_container_width=True):
                    with st.spinner(f"Parsing {file_to_parse.name}..."):
                        result = parse_and_store_resume(file_to_parse, file_name_key='single_resume_candidate', source_type='file')
                        
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
            else:
                st.info("No resume file is currently uploaded. Please upload a file above.")

        # --- B. Paste Text Method (NEW) ---
        else: # input_method == "Paste Text"
            st.markdown("### 1. Paste Your CV Text")
            
            pasted_text = st.text_area(
                "Copy and paste your entire CV or resume text here.",
                value=st.session_state.get('pasted_cv_text', ''),
                height=300,
                key='pasted_cv_text_input'
            )
            st.session_state.pasted_cv_text = pasted_text # Update session state immediately
            
            st.markdown("---")
            st.markdown("### 2. Parse Pasted Text")
            
            if pasted_text.strip():
                if st.button("Parse and Load Pasted Text", use_container_width=True):
                    with st.spinner("Parsing pasted text..."):
                        # Clear file upload state
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

    # --- TAB 2 (Now tab_jd_mgmt): JD Management (Candidate) ---
    with tab_jd_mgmt:
        st.header("📚 Manage Job Descriptions for Matching")
        st.markdown("Add multiple JDs here to compare your resume against them in the next tabs.")
        
        if "candidate_jd_list" not in st.session_state:
             st.session_state.candidate_jd_list = []
        
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
                            metadata = extract_jd_metadata(jd_text) # NEW METADATA EXTRACTION
                        
                        name_base = url.split('/jobs/view/')[-1].split('/')[0] if '/jobs/view/' in url else f"URL {count+1}"
                        # CRITICAL: Added explicit JD naming convention for LinkedIn URLs in Candidate JD list
                        name = f"JD from URL: {name_base}" 
                        if name in [item['name'] for item in st.session_state.candidate_jd_list]:
                            name = f"JD from URL: {name_base} ({len(st.session_state.candidate_jd_list) + 1})" 

                        st.session_state.candidate_jd_list.append({"name": name, "content": jd_text, **metadata}) # ADD METADATA
                        
                        if not jd_text.startswith("[Error"):
                            count += 1
                                
                    if count > 0:
                        st.success(f"✅ {count} JD(s) added successfully! Check the display below for the extracted content.")
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
                            
                            metadata = extract_jd_metadata(text) # NEW METADATA EXTRACTION
                            st.session_state.candidate_jd_list.append({"name": name_base, "content": text, **metadata}) # ADD METADATA
                    st.success(f"✅ {len(texts)} JD(s) added successfully!")

        # Upload File
        elif method == "Upload File":
            uploaded_files = st.file_uploader(
                "Upload JD file(s)",
                type=["pdf", "txt", "docx"],
                accept_multiple_files=(jd_type == "Multiple JD"), # Dynamically set
                key="jd_file_uploader_candidate"
            )
            if st.button("Add JD(s) from File", key="add_jd_file_btn_candidate"):
                # CRITICAL FIX: Ensure 'files_to_process' is always a list of single UploadedFile objects
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
                            metadata = extract_jd_metadata(jd_text) # NEW METADATA EXTRACTION
                            st.session_state.candidate_jd_list.append({"name": file.name, "content": jd_text, **metadata}) # ADD METADATA
                            count += 1
                        else:
                            st.error(f"Error extracting content from {file.name}: {jd_text}")
                            
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
                    # Also clear filter display
                    st.session_state.filtered_jds_display = [] 
                    st.success("All JDs and associated match results have been cleared.")
                    st.rerun() 

            for idx, jd_item in enumerate(st.session_state.candidate_jd_list, 1):
                title = jd_item['name']
                display_title = title.replace("--- Simulated JD for: ", "")
                with st.expander(f"JD {idx}: {display_title} | Role: {jd_item.get('role', 'N/A')}"):
                    st.markdown(f"**Job Type:** {jd_item.get('job_type', 'N/A')} | **Key Skills:** {', '.join(jd_item.get('key_skills', ['N/A']))}") # ADDED METADATA DISPLAY
                    st.markdown("---")
                    st.text(jd_item['content'])
        else:
            st.info("No Job Descriptions added yet.")

    # --- TAB 3 (Now tab_batch_match): Batch JD Match (Candidate) ---
    with tab_batch_match:
        st.header("🎯 Batch JD Match: Best Matches")
        st.markdown("Compare your current resume against all saved job descriptions.")

        if not is_resume_parsed:
            st.warning("Please **upload and parse your resume** in the 'Resume Parsing' tab or **build your CV** in the 'CV Management' tab first.")
        
        elif not st.session_state.candidate_jd_list:
            st.error("Please **add Job Descriptions** in the 'JD Management' tab (Tab 4) before running batch analysis.")
            
        elif not GROQ_API_KEY or GROQ_API_KEY == 'YOUR_PLACEHOLDER_KEY':
             st.error("Cannot use JD Match: GROQ_API_KEY is not configured.")
             
        else:
            if "candidate_match_results" not in st.session_state:
                st.session_state.candidate_match_results = []

            # 1. Get all available JD names
            all_jd_names = [item['name'] for item in st.session_state.candidate_jd_list]
            
            # 2. Add multiselect widget
            selected_jd_names = st.multiselect(
                "Select Job Descriptions to Match Against",
                options=all_jd_names,
                default=all_jd_names, # Default to selecting all JDs
                key='candidate_batch_jd_select'
            )
            
            # 3. Filter the list of JDs based on selection
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
                        
                        # Loop over jds_to_match
                        for jd_item in jds_to_match:
                            
                            jd_name = jd_item['name']
                            jd_content = jd_item['content']

                            try:
                                fit_output = evaluate_jd_fit(jd_content, parsed_json)
                                
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
                                    "numeric_score": int(overall_score) if overall_score.isdigit() else -1, # Added for sorting/ranking
                                    "skills_percent": skills_percent,
                                    "experience_percent": experience_percent, 
                                    "education_percent": education_percent,   
                                    "full_analysis": fit_output
                                })
                            except Exception as e:
                                results_with_score.append({
                                    "jd_name": jd_name,
                                    "overall_score": "Error",
                                    "numeric_score": -1, # Set a low score for errors
                                    "skills_percent": "Error",
                                    "experience_percent": "Error", 
                                    "education_percent": "Error",   
                                    "full_analysis": f"Error running analysis for {jd_name}: {e}\n{traceback.format_exc()}"
                                })
                                
                        # --- NEW RANKING LOGIC ---
                        # 1. Sort by numeric_score (highest first)
                        results_with_score.sort(key=lambda x: x['numeric_score'], reverse=True)
                        
                        # 2. Assign Rank (handle ties)
                        current_rank = 1
                        current_score = -1 
                        
                        for i, item in enumerate(results_with_score):
                            if item['numeric_score'] > current_score:
                                current_rank = i + 1
                                current_score = item['numeric_score']
                            
                            item['rank'] = current_rank
                            # Remove the temporary numeric_score field
                            del item['numeric_score'] 
                            
                        st.session_state.candidate_match_results = results_with_score
                        # --- END NEW RANKING LOGIC ---
                        
                        st.success("Batch analysis complete!")


            # 3. Display Results (UPDATED TO INCLUDE RANK)
            if st.session_state.get('candidate_match_results'):
                st.markdown("#### Match Results for Your Resume")
                results_df = st.session_state.candidate_match_results
                
                display_data = []
                for item in results_df:
                    # Also include extracted JD metadata for a richer view
                    
                    # Find the full JD item to get the metadata
                    full_jd_item = next((jd for jd in st.session_state.candidate_jd_list if jd['name'] == item['jd_name']), {})
                    
                    display_data.append({
                        # 🚨 ADDED RANK COLUMN
                        "Rank": item.get("rank", "N/A"),
                        "Job Description (Ranked)": item["jd_name"].replace("--- Simulated JD for: ", ""),
                        "Role": full_jd_item.get('role', 'N/A'), # Added Role
                        "Job Type": full_jd_item.get('job_type', 'N/A'), # Added Job Type
                        "Fit Score (out of 10)": item["overall_score"],
                        "Skills (%)": item.get("skills_percent", "N/A"),
                        "Experience (%)": item.get("experience_percent", "N/A"), 
                        "Education (%)": item.get("education_percent", "N/A"),   
                    })

                st.dataframe(display_data, use_container_width=True)

                st.markdown("##### Detailed Reports")
                for item in results_df:
                    # UPDATED HEADER TO INCLUDE RANK
                    rank_display = f"Rank {item.get('rank', 'N/A')} | "
                    header_text = f"{rank_display}Report for **{item['jd_name'].replace('--- Simulated JD for: ', '')}** (Score: **{item['overall_score']}/10** | S: **{item.get('skills_percent', 'N/A')}%** | E: **{item.get('experience_percent', 'N/A')}%** | Edu: **{item.get('education_percent', 'N/A')}%**)"
                    with st.expander(header_text):
                        st.markdown(item['full_analysis'])

    # --- TAB 4 (Now tab_filter_jd): Filter JD (NEW) ---
    with tab_filter_jd:
        filter_jd_tab_content()

    # --- TAB 5 (Now tab_chatbot): Resume Chatbot (Q&A) (MOVED) ---
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
            elif not GROQ_API_KEY or GROQ_API_KEY == 'YOUR_PLACEHOLDER_KEY':
                 st.error("Cannot use Chatbot: GROQ_API_KEY is not configured.")
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
        
        # --- 5B. JD CHATBOT CONTENT (NEW SUBTAB) ---
        with sub_tab_jd:
            st.markdown("### Ask any question about a saved Job Description.")
            
            if not st.session_state.candidate_jd_list:
                st.warning("Please add Job Descriptions in the 'JD Management' tab (Tab 4) first.")
            elif not GROQ_API_KEY or GROQ_API_KEY == 'YOUR_PLACEHOLDER_KEY':
                 st.error("Cannot use JD Chatbot: GROQ_API_KEY is not configured.")
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
                    else:
                        st.error("Please select a JD and enter a question.")

                # 4. Answer Output
                if st.session_state.get('qa_answer_jd'):
                    st.text_area("Answer (JD)", st.session_state.qa_answer_jd, height=150)


    # --- TAB 6 (Now tab_interview_prep): Interview Prep (MOVED) ---
    with tab_interview_prep:
        st.header("Interview Preparation Tools")
        if not is_resume_parsed or "error" in st.session_state.parsed:
            st.warning("Please upload and successfully parse a resume first.")
        elif not GROQ_API_KEY or GROQ_API_KEY == 'YOUR_PLACEHOLDER_KEY':
             st.error("Cannot use Interview Prep: GROQ_API_KEY is not configured.")
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

# --- 5. MAIN APPLICATION ENTRY POINT ---
if __name__ == "__main__":
    st.set_page_config(
        page_title="AI-Powered Career Assistant",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    initialize_session_state()

    # Simple router based on session state
    if not st.session_state.logged_in or st.session_state.current_page == "login":
        login_page()
    elif st.session_state.logged_in and st.session_state.user_role == "candidate":
        candidate_dashboard()
    else:
        st.error("Unknown state. Please log in.")
        go_to("login")
        st.rerun()
