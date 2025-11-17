import streamlit as st
import os
import pdfplumber
import docx
import json
import traceback
import re 
from dotenv import load_dotenv 
from datetime import datetime
from io import BytesIO 
import tempfile # Still needed for mock URL extraction, but not for file upload

# --- CONFIGURATION & API SETUP ---

GROQ_MODEL = "llama-3.1-8b-instant"
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Groq Client or Mock Client 
try:
    from groq import Groq
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set.")
    client = Groq(api_key=GROQ_API_KEY)
except (ImportError, ValueError) as e:
    # Mock Client for local testing without Groq
    class MockGroqClient:
        def chat(self):
            class Completions:
                def create(self, **kwargs):
                    return type('MockResponse', (object,), {'choices': [{'message': {'content': '{"name": "Mock Candidate", "summary": "Mock summary for testing.", "skills": ["Python", "Streamlit"]}'}}]})()
            return Completions()
    client = MockGroqClient()
    st.info(f"AI functions are running in MOCK mode because Groq setup failed: {e}")

# --- Utility Functions ---

def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def get_file_type(file_name):
    """Identifies the file type based on its extension."""
    ext = os.path.splitext(file_name)[1].lower().strip('.')
    if ext == 'pdf': return 'pdf'
    elif ext == 'docx' or ext == 'doc': return 'docx'
    elif ext == 'txt': return 'txt'
    else: return 'unknown' 

def extract_content(file_type, file_content_bytes, file_name):
    """
    Extracts text content from uploaded file content (bytes).
    This function is used for both resume and JD file uploads.
    """
    text = ''
    try:
        if file_type == 'pdf':
            with pdfplumber.open(BytesIO(file_content_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        
        elif file_type == 'docx':
            doc = docx.Document(BytesIO(file_content_bytes))
            text = '\n'.join([para.text for para in doc.paragraphs])
        
        elif file_type in ['txt', 'unknown']:
            try:
                text = file_content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                 text = file_content_bytes.decode('latin-1')
        
        if not text.strip():
            return f"[Error] {file_type.upper()} content extraction failed or file is empty."
        
        return text
    
    except Exception as e:
        return f"[Error] Fatal Extraction Error: Failed to read file content ({file_type}). Error: {e}\n{traceback.format_exc()}"


@st.cache_data(show_spinner="Analyzing content with Groq LLM...")
def parse_resume_with_llm(text):
    """Sends resume text to the LLM for structured information extraction."""
    if text.startswith("[Error") or isinstance(client, MockGroqClient):
        # Fallback for mock/error states
        return {"name": "Mock Candidate", "summary": "Mock summary for testing.", "skills": ["Python", "Streamlit"], "error": "Mock/Parsing error." if isinstance(client, MockGroqClient) else text}

    prompt = f"""Extract the following information from the resume in structured JSON.
    ... (omitted for brevity)
    Provide the output strictly as a JSON object, without any surrounding markdown or commentary.
    """
    # ... (Groq API call logic)
    return {"name": "Parsed Candidate", "summary": "Actual parsed summary.", "skills": ["Real", "Python", "Streamlit"]} # Mock for Groq


@st.cache_data(show_spinner="Analyzing JD for metadata...")
def extract_jd_metadata(jd_text):
    """Mocks the extraction of key metadata (Role, Skills, Job Type) from JD text using LLM."""
    if jd_text.startswith("[Error"):
        return {"role": "Error", "key_skills": ["Error"], "job_type": "Error"}
    
    # Simple heuristic mock
    role_match = re.search(r'(?:Role|Position|Title)[:\s]+([\w\s/-]+)', jd_text, re.IGNORECASE)
    role = role_match.group(1).strip() if role_match else "Software Engineer (Mock)"
    
    skills_match = re.findall(r'(Python|Java|SQL|AWS|Docker|Kubernetes|React|Streamlit)', jd_text, re.IGNORECASE)
    
    job_type_match = re.search(r'(Full-time|Part-time|Contract|Remote)', jd_text, re.IGNORECASE)
    job_type = job_type_match.group(1) if job_type_match else "Full-time (Mock)"
    
    return {
        "role": role, 
        "key_skills": list(set([s.lower() for s in skills_match][:5])), # Limit to 5 unique skills
        "job_type": job_type
    }

def extract_jd_from_linkedin_url(url):
    """Mocks the extraction of JD content from a LinkedIn URL."""
    if "linkedin.com/jobs" not in url:
        return f"[Error] Invalid LinkedIn Job URL: {url}"

    # Mock content based on URL structure
    role = "Data Scientist" if "data" in url.lower() else "Cloud Engineer"
    
    return f"""
    --- Simulated JD for: {role} ---
    
    Company: MockCorp
    Location: Remote
    
    Job Summary:
    We are seeking a highly skilled {role} to join our team. The ideal candidate will have expertise in Python, SQL, and AWS. Must be able to work in a fast-paced environment and deliver solutions quickly. This is a Full-time position.
    
    Responsibilities:
    * Develop and maintain data pipelines using **Python** and **SQL**.
    * Manage and deploy applications on **AWS** and **Docker**.
    * Collaborate with cross-functional teams.
    
    Qualifications:
    * 3+ years of experience.
    * Strong proficiency in **Python** and analytical tools.
    * Experience with cloud platforms (e.g., **AWS**).
    ---
    """

# --- CV Helper Functions (Simplified for display) ---

def save_form_cv():
    """Compiles the structured CV data from form states and saves it."""
    # ... (omitted for brevity)
    st.success(f"🎉 CV saved/updated!")

def generate_and_display_cv(cv_name):
    """Generates the final structured CV data from session state and displays it."""
    # ... (omitted for brevity)
    st.markdown(f"### 📄 CV View: **{cv_name}**")
    st.info("CV Display Logic Here.")
    
# --- Main Tab Content Functions ---

def resume_parsing_tab():
    st.header("📄 Upload/Paste Resume for AI Parsing")
    st.caption("Upload a file or paste text to extract structured data and save it as a structured CV.")
    
    with st.form("resume_parsing_form", clear_on_submit=False):
        uploaded_file = st.file_uploader(
            "Upload Resume File (.pdf, .docx, .txt)", 
            type=['pdf', 'docx', 'txt'], 
            accept_multiple_files=False,
            key="resume_uploader"
        )

        st.markdown("---")
        pasted_text = st.text_area("Or Paste Resume Text Here", height=200, key="resume_paster")
        st.markdown("---")

        if st.form_submit_button("✨ Parse and Structure CV", type="primary", use_container_width=True):
            extracted_text = ""
            file_name = "Pasted_Resume"
            
            if uploaded_file is not None:
                file_name = uploaded_file.name
                file_type = get_file_type(file_name)
                extracted_text = extract_content(file_type, uploaded_file.getvalue(), file_name)
            elif pasted_text.strip():
                extracted_text = pasted_text.strip()
            else:
                st.warning("Please upload a file or paste text content to proceed.")
                return

            if extracted_text.startswith("[Error"):
                st.error(f"Text Extraction Failed: {extracted_text}")
                return
                
            with st.spinner("🧠 Sending to Groq LLM for structured parsing..."):
                parsed_data = parse_resume_with_llm(extracted_text)
            
            if "error" in parsed_data:
                st.error(f"AI Parsing Failed: {parsed_data['error']}")
                return

            # Store the new CV
            candidate_name = parsed_data.get('name', 'Unknown_Candidate').replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d-%H%M")
            cv_key_name = f"{candidate_name}_{timestamp}"
            
            st.session_state.managed_cvs[cv_key_name] = parsed_data
            st.session_state.show_cv_output = cv_key_name
            
            st.success(f"✅ Successfully parsed and structured CV for **{candidate_name}**!")
            st.rerun()

def cv_form_content():
    """Manual CV Form Tab."""
    st.header("📝 CV Management (Manual Form)")
    st.info("Use this form to manually enter or edit structured CV details.")
    # Simplified form fields for brevity
    st.text_input("Full Name", key="form_name_value")
    st.text_area("Career Summary", key="form_summary_value")
    st.button("💾 **Save CV Details**", type="primary", use_container_width=True, on_click=save_form_cv)
    st.markdown("---")
    if st.session_state.show_cv_output:
        generate_and_display_cv(st.session_state.show_cv_output)


def jd_management_tab_candidate():
    """JD Management Tab as provided by the user with fixes."""
    st.header("📚 Manage Job Descriptions for Matching")
    st.markdown("Add multiple JDs here to compare your resume against them in the next tabs.")
    
    if "candidate_jd_list" not in st.session_state:
        st.session_state.candidate_jd_list = []
    
    st.markdown("---")
    
    jd_type = st.radio("Select JD Type", ["Single JD", "Multiple JD"], key="jd_type_candidate", index=0)
    st.markdown("### Add JD by:")
    
    method = st.radio("Choose Method", ["Upload File", "Paste Text", "LinkedIn URL"], key="jd_add_method_candidate", index=0) 
    
    st.markdown("---")

    # --- LinkedIn URL Section ---
    if method == "LinkedIn URL":
        with st.form("jd_url_form_candidate", clear_on_submit=True):
            url_list = st.text_area(
                "Enter one or more URLs (comma separated)" if jd_type == "Multiple JD" else "Enter URL", key="url_list_candidate"
            )
            if st.form_submit_button("Add JD(s) from URL", key="add_jd_url_btn_candidate"):
                if url_list:
                    urls = [u.strip() for u in url_list.split(",")] if jd_type == "Multiple JD" else [url_list.strip()]
                    
                    count = 0
                    for url in urls:
                        if not url: continue
                        
                        with st.spinner(f"Attempting JD extraction and metadata analysis for: {url}"):
                            jd_text = extract_jd_from_linkedin_url(url)
                            metadata = extract_jd_metadata(jd_text) # NEW METADATA EXTRACTION
                        
                        if jd_text.startswith("[Error"):
                            st.error(f"Failed to process {url}: {jd_text}")
                            continue
                            
                        name_base = url.split('/jobs/view/')[-1].split('/')[0] if '/jobs/view/' in url else f"URL JD"
                        # CRITICAL: Added explicit JD naming convention for LinkedIn URLs in Candidate JD list
                        name = f"JD from URL: {name_base}" 
                        if any(item['name'] == name for item in st.session_state.candidate_jd_list):
                            name = f"JD from URL: {name_base} ({len(st.session_state.candidate_jd_list) + 1})" 

                        st.session_state.candidate_jd_list.append({"name": name, "content": jd_text, **metadata}) # ADD METADATA
                        count += 1
                            
                    if count > 0:
                        st.success(f"✅ {count} JD(s) added successfully! Check the display below for the extracted content.")
                        st.rerun() # Rerun to display updated list
                    else:
                        st.error("No JDs were added successfully.")

    # --- Paste Text Section ---
    elif method == "Paste Text":
        with st.form("jd_paste_form_candidate", clear_on_submit=True):
            text_list = st.text_area(
                "Paste one or more JD texts (separate by '---')" if jd_type == "Multiple JD" else "Paste JD text here", key="text_list_candidate"
            )
            if st.form_submit_button("Add JD(s) from Text", key="add_jd_text_btn_candidate"):
                if text_list:
                    texts = [t.strip() for t in text_list.split("---")] if jd_type == "Multiple JD" else [text_list.strip()]
                    count = 0
                    for i, text in enumerate(texts):
                        if text:
                            name_base = text.splitlines()[0].strip()
                            if len(name_base) > 30: name_base = f"{name_base[:27]}..."
                            if not name_base: name_base = f"Pasted JD {len(st.session_state.candidate_jd_list) + i + 1}"
                            
                            metadata = extract_jd_metadata(text) # NEW METADATA EXTRACTION
                            st.session_state.candidate_jd_list.append({"name": name_base, "content": text, **metadata}) # ADD METADATA
                            count += 1
                    
                    if count > 0:
                        st.success(f"✅ {count} JD(s) added successfully!")
                        st.rerun() # Rerun to display updated list
                    else:
                        st.error("No valid JD text provided.")


    # --- Upload File Section ---
    elif method == "Upload File":
        uploaded_files = st.file_uploader(
            "Upload JD file(s)",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=(jd_type == "Multiple JD"), # Dynamically set
            key="jd_file_uploader_candidate"
        )
        
        # Ensure files_to_process is always a list for consistency
        files_to_process = uploaded_files if isinstance(uploaded_files, list) else ([uploaded_files] if uploaded_files else [])
        
        with st.form("jd_upload_form_candidate", clear_on_submit=False):
            # Show files if they exist before the button
            if files_to_process:
                st.markdown("##### Files Selected:")
                for file in files_to_process:
                    st.markdown(f"&emsp;📄 **{file.name}** {round(file.size / (1024*1024), 2)}MB")
                    
            if st.form_submit_button("Add JD(s) from File", key="add_jd_file_btn_candidate"):
                if not files_to_process:
                    st.warning("Please upload file(s).")
                    
                count = 0
                for file in files_to_process:
                    if file:
                        with st.spinner(f"Extracting content from {file.name}..."):
                            file_type = get_file_type(file.name)
                            # FIX: Use file.getvalue() for content extraction
                            jd_text = extract_content(file_type, file.getvalue(), file.name)
                            
                        if not jd_text.startswith("[Error"):
                            metadata = extract_jd_metadata(jd_text) # NEW METADATA EXTRACTION
                            st.session_state.candidate_jd_list.append({"name": file.name, "content": jd_text, **metadata}) # ADD METADATA
                            count += 1
                        else:
                            st.error(f"Error extracting content from {file.name}: {jd_text}")
                            
                if count > 0:
                    st.success(f"✅ {count} JD(s) added successfully!")
                    st.rerun() # Rerun to display updated list
                elif uploaded_files:
                    st.error("No valid JD files were uploaded or content extraction failed.")


    st.markdown("---")
    # Display Added JDs
    if st.session_state.candidate_jd_list:
        
        col_display_header, col_clear_button = st.columns([3, 1])
        
        with col_display_header:
            st.markdown("### ✅ Current JDs Added:")
            
        with col_clear_button:
            if st.button("🗑️ Clear All JDs", key="clear_jds_candidate", use_container_width=True, help="Removes all currently loaded JDs."):
                st.session_state.candidate_jd_list = []
                st.session_state.candidate_match_results = [] # Assuming this exists
                st.session_state.filtered_jds_display = [] # Assuming this exists
                st.success("All JDs and associated match results have been cleared.")
                st.rerun() 

        for idx, jd_item in enumerate(st.session_state.candidate_jd_list, 1):
            title = jd_item['name']
            display_title = title.replace("--- Simulated JD for: ", "")
            with st.expander(f"**JD {idx}:** {display_title} | Role: {jd_item.get('role', 'N/A')}"):
                st.markdown(f"**Job Type:** {jd_item.get('job_type', 'N/A')} | **Key Skills:** `{', '.join(jd_item.get('key_skills', ['N/A']))}`") # ADDED METADATA DISPLAY
                st.markdown("---")
                st.text(jd_item['content'])
    else:
        st.info("No Job Descriptions added yet.")
        
# -------------------------
# CANDIDATE DASHBOARD FUNCTION 
# -------------------------

def candidate_dashboard():
    st.title("🧑‍💻 Candidate Dashboard")
    
    col_header, col_logout = st.columns([4, 1])
    with col_logout:
        if st.button("🚪 Log Out", use_container_width=True):
            # Simple session state reset on logout
            for key in list(st.session_state.keys()):
                if key not in ['page', 'logged_in', 'user_type']:
                    del st.session_state[key]
            go_to("login")
            st.rerun() 
            
    st.markdown("---")

    # --- Session State Initialization ---
    if "managed_cvs" not in st.session_state: st.session_state.managed_cvs = {} 
    if "show_cv_output" not in st.session_state: st.session_state.show_cv_output = None 
    if "form_name_value" not in st.session_state: st.session_state.form_name_value = ""
    # Ensure all JD lists/states are initialized
    if "candidate_jd_list" not in st.session_state: st.session_state.candidate_jd_list = []
    if "candidate_match_results" not in st.session_state: st.session_state.candidate_match_results = []
    if "filtered_jds_display" not in st.session_state: st.session_state.filtered_jds_display = []


    # --- Main Content with Rearranged Tabs ---
    # Tab Order: Resume Parsing, CV Management, JD Management (Last, as requested)
    tab_parsing, tab_management, tab_jd = st.tabs(["📄 Resume Parsing", "📝 CV Management (Form)", "📚 JD Management"])
    
    with tab_parsing:
        resume_parsing_tab()
        
    with tab_management:
        cv_form_content() 
        
    # The fixed JD Management tab is here:
    with tab_jd:
        jd_management_tab_candidate()


# -------------------------
# MOCK LOGIN AND MAIN APP LOGIC 
# -------------------------

def login_page():
    st.title("Welcome to PragyanAI")
    st.header("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username (Enter 'candidate')")
        password = st.text_input("Password (Any value)", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username.lower() == "candidate":
                st.session_state.logged_in = True
                st.session_state.user_type = "candidate"
                go_to("candidate_dashboard")
                st.rerun()
            else:
                st.error("Invalid username. Please use 'candidate'.")

# --- Main App Execution ---

if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="PragyanAI Candidate Dashboard")

    if 'page' not in st.session_state: st.session_state.page = "login"
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'user_type' not in st.session_state: st.session_state.user_type = None
    
    if st.session_state.logged_in and st.session_state.user_type == "candidate":
        candidate_dashboard()
    else:
        login_page()
