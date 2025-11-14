import streamlit as st
import os
import pdfplumber
import docx
import openpyxl
import json
import tempfile
from groq import Groq
import traceback
import re 
from dotenv import load_dotenv 
from datetime import date 
from streamlit.runtime.uploaded_file_manager import UploadedFile

# -------------------------
# CONFIGURATION & API SETUP (Necessary for standalone functions)
# -------------------------

GROQ_MODEL = "llama-3.1-8b-instant"
# Load environment variables (mocked if running standalone)
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Groq Client or Mock Client (Must be present for function definitions)
if not GROQ_API_KEY:
    class MockGroqClient:
        def chat(self):
            class Completions:
                def create(self, **kwargs):
                    raise ValueError("GROQ_API_KEY not set. AI functions disabled.")
            return Completions()
    client = MockGroqClient()
else:
    client = Groq(api_key=GROQ_API_KEY)

# --- Utility Functions (Duplicated/shared for both dashboards) ---

def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def get_file_type(file_path):
    """Identifies the file type based on its extension."""
    ext = os.path.splitext(file_path)[1].lower().strip('.')
    if ext == 'pdf': return 'pdf'
    elif ext == 'docx': return 'docx'
    elif ext == 'xlsx': return 'xlsx'
    else: return 'txt' 

def extract_content(file_type, file_path):
    """Extracts text content from various file types (Simplified for resume parsing)."""
    text = ''
    try:
        # Use tempfile path for extraction if running on an environment that requires disk access
        if file_type == 'pdf':
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        elif file_type == 'docx':
            doc = docx.Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
        
        if not text.strip():
            return f"Error: {file_type.upper()} content extraction failed or file is empty."
        
        return text
    
    except Exception as e:
        return f"Fatal Extraction Error: Failed to read file content ({file_type}). Error: {e}"


@st.cache_data(show_spinner="Extracting JD metadata...")
def extract_jd_metadata(jd_text):
    """Extracts structured metadata (Role, Key Skills) from raw JD text."""
    if not GROQ_API_KEY:
        return {"role": "N/A", "key_skills": []}

    prompt = f"""Analyze the following Job Description and extract the key metadata.
    
    Job Description:
    {jd_text}
    
    Provide the output strictly as a JSON object with the following two keys:
    1.  **role**: The main job title.
    2.  **key_skills**: A list of 5 to 10 most critical hard and soft skills required.
    """
    content = ""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        
        # Robustly isolate JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0).strip()
            json_str = json_str.replace('```json', '').replace('```', '').strip() 
            parsed = json.loads(json_str)
        else:
            raise json.JSONDecodeError("Could not isolate a valid JSON structure from LLM response.", content, 0)
        
        return {
            "role": parsed.get("role", "General Analyst"),
            "key_skills": [s.strip() for s in parsed.get("key_skills", []) if isinstance(s, str)]
        }

    except Exception:
        return {"role": "General Analyst (LLM Error)", "key_skills": ["LLM Error", "Fallback"]}


@st.cache_data(show_spinner="Analyzing content with Groq LLM...")
def parse_with_llm(text):
    """Sends resume text to the LLM for structured information extraction."""
    if text.startswith("Error") or not GROQ_API_KEY:
        return {"error": "Parsing error or API key missing.", "raw_output": ""}

    prompt = f"""Extract the following information from the resume in structured JSON.
    - Name, - Email, - Phone, - Skills, - Education (list of degrees/schools), 
    - Experience (list of jobs), - Certifications, 
    - Projects, - Strength, 
    - Personal Details, - Github, - LinkedIn
    
    Also, provide a key called **'summary'** which is a single, brief paragraph (3-4 sentences max) summarizing the candidate's career highlights and most relevant skills.
    
    Resume Text: {text}
    
    Provide the output strictly as a JSON object.
    """
    content = ""
    parsed = {}
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        
        # Robustly isolate JSON object
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0).strip()
            json_str = json_str.replace('```json', '').replace('```', '').strip() 
            parsed = json.loads(json_str)
        else:
            raise json.JSONDecodeError("Could not isolate a valid JSON structure.", content, 0)
    except Exception as e:
        parsed = {"error": f"LLM error: {e}", "raw_output": content}

    return parsed


def evaluate_jd_fit(job_description, parsed_json):
    """Evaluates how well a resume fits a given job description, including section-wise scores."""
    if not GROQ_API_KEY or "error" in parsed_json: return "AI Evaluation Disabled or resume parsing failed."
    
    relevant_resume_data = {
        'Skills': parsed_json.get('skills', 'Not found or empty'),
        'Experience': parsed_json.get('experience', 'Not found or empty'),
        'Education': parsed_json.get('education', 'Not found or empty'),
    }
    resume_summary = json.dumps(relevant_resume_data, indent=2)

    prompt = f"""Evaluate how well the following resume content matches the provided job description.
    Job Description: {job_description}
    Resume Sections for Analysis: {resume_summary}
    Provide a detailed evaluation structured as follows:
    1.  **Overall Fit Score:** A score out of 10.
    2.  **Section Match Percentages:** A percentage score for the match in the key sections (Skills, Experience, Education).
    
    Format the output strictly as follows:
    Overall Fit Score: [Score]/10
    
    --- Section Match Analysis ---
    Skills Match: [XX]%
    Experience Match: [YY]%
    Education Match: [ZZ]%
    
    Strengths/Matches:
    - Point 1
    - Point 2
    
    Areas for Improvement:
    - Point 1
    - Point 2
    """

    response = client.chat.completions.create(
        model=GROQ_MODEL, 
        messages=[{"role": "user", "content": prompt}], 
        temperature=0.3
    )
    return response.choices[0].message.content.strip()


def parse_and_analyze_resume(file_input, jd_content, source_type='file', jd_name="Job Description"):
    """
    Handles file/text input, parsing, and analysis for the candidate dashboard.
    Returns a dictionary with results.
    """
    text = None
    file_name = f"Resume ({date.today().strftime('%Y-%m-%d')})"
    
    if source_type == 'file':
        if not isinstance(file_input, UploadedFile):
            return {"error": "Invalid file input type passed to parser."}
        
        # Save file to a temporary location for processing
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file_input.name) 
        with open(temp_path, "wb") as f:
            f.write(file_input.getbuffer()) 

        file_type = get_file_type(temp_path)
        text = extract_content(file_type, temp_path)
        file_name = file_input.name.split('.')[0]
    
    elif source_type == 'text':
        text = file_input
        
    if text.startswith("Error"):
        return {"error": text}

    # 1. Parse Resume
    parsed_resume = parse_with_llm(text)
    
    if "error" in parsed_resume:
        return {"error": f"Resume Parsing Failed: {parsed_resume.get('error', 'Unknown Error')}"}
    
    # 2. Extract JD Metadata
    jd_metadata = extract_jd_metadata(jd_content)
    
    # 3. Run Match Evaluation
    match_analysis = evaluate_jd_fit(jd_content, parsed_resume)
    
    overall_score_match = re.search(r'Overall Fit Score:\s*[^\d]*(\d+)\s*/10', match_analysis, re.IGNORECASE)
    overall_score = overall_score_match.group(1) if overall_score_match else 'N/A'
    
    return {
        "name": parsed_resume.get('name', file_name),
        "date": date.today().strftime("%Y-%m-%d"),
        "jd_name": jd_name,
        "jd_role": jd_metadata.get('role', 'N/A'),
        "overall_score": overall_score,
        "match_report": match_analysis,
        "parsed_resume": parsed_resume
    }

# --- Education Input Logic ---

def add_education_entry(degree, college, university, date_from, date_to):
    """
    Callback function to add a structured education entry to session state.
    """
    if not degree or not college or not university:
        st.error("Please fill in **Degree**, **College**, and **University**.")
        return
        
    entry = f"{degree}, {college}, {university} ({date_from.year} - {date_to.year})"
    
    if 'manual_education' not in st.session_state:
        st.session_state.manual_education = []
        
    st.session_state.manual_education.append(entry)
    st.success(f"Added Education: {entry}")

# -------------------------
# TAB FUNCTIONS
# -------------------------

def tab_cv_management():
    st.header("📊 CV Management")
    st.caption("Upload, view, and manage different versions of your CV.")

    if "managed_cvs" not in st.session_state:
        st.session_state.managed_cvs = {} # Stores {cv_name: parsed_data}

    st.markdown("### Upload New CV")
    new_cv_file = st.file_uploader(
        "Upload a PDF or DOCX Resume to Manage",
        type=["pdf", "docx"],
        key="new_cv_upload"
    )

    if new_cv_file:
        cv_name = st.text_input("Name this CV version (e.g., 'Tech Resume', 'Marketing CV')", 
                                value=new_cv_file.name.split('.')[0], key="cv_name_input")
        
        if st.button(f"Save & Parse '{cv_name}'", type="primary"):
            if not GROQ_API_KEY:
                st.error("❌ AI Analysis is disabled. Cannot parse CV for storage.")
                return

            with st.spinner(f"Parsing CV: {new_cv_file.name}..."):
                try:
                    # Save file to temp path to get the content
                    temp_dir = tempfile.mkdtemp()
                    temp_path = os.path.join(temp_dir, new_cv_file.name)
                    with open(temp_path, "wb") as f:
                        f.write(new_cv_file.getbuffer())
                    
                    file_type = get_file_type(temp_path)
                    text = extract_content(file_type, temp_path)
                    
                    if text.startswith("Error"):
                        st.error(f"Extraction failed: {text}")
                        return
                        
                    parsed_data = parse_with_llm(text)

                    if "error" in parsed_data:
                        st.error(f"Parsing failed: {parsed_data.get('error', 'Unknown error')}")
                    else:
                        st.session_state.managed_cvs[cv_name] = parsed_data
                        st.success(f"✅ CV **'{cv_name}'** successfully parsed and saved!")
                        # Optionally set as current resume for immediate analysis
                        st.session_state.current_resume_name = cv_name
                        st.rerun() 
                        
                except Exception as e:
                    st.error(f"An unexpected error occurred during parsing: {e}")
                    st.code(traceback.format_exc())

    st.markdown("---")

    st.markdown("### Saved CVs")
    if not st.session_state.managed_cvs:
        st.info("No CVs saved yet. Upload one above.")
    else:
        cv_names = list(st.session_state.managed_cvs.keys())
        selected_cv = st.selectbox("Select a CV to view details:", cv_names, key="cv_select_view")
        
        if selected_cv:
            data = st.session_state.managed_cvs[selected_cv]
            st.markdown(f"**Name:** {data.get('name', 'N/A')}")
            st.markdown(f"**Summary:** *{data.get('summary', 'N/A')}*")
            
            with st.expander(f"View Full Parsed Data for '{selected_cv}'"):
                st.json(data)
            
            col_actions_1, col_actions_2, _ = st.columns([1, 1, 4])
            with col_actions_1:
                if st.button("Set as Active CV", key="set_active_cv"):
                    # Set the currently viewed CV for use in the analyzer
                    st.session_state.current_resume_name = selected_cv
                    st.success(f"**'{selected_cv}'** set as the active CV for analysis.")
            with col_actions_2:
                if st.button("Delete CV", key="delete_cv"):
                    del st.session_state.managed_cvs[selected_cv]
                    if 'current_resume_name' in st.session_state and st.session_state.current_resume_name == selected_cv:
                        del st.session_state.current_resume_name
                    st.warning(f"CV **'{selected_cv}'** deleted.")
                    st.rerun()


def tab_resume_analyzer():
    st.header("🚀 Resume Analyzer")
    st.caption("Match your CV against a specific Job Description.")
    
    # --- Check for Active CV ---
    active_cv_name = st.session_state.get('current_resume_name')
    active_cv_data = None
    
    # Show CV Selection/Input Section
    st.markdown("### Step 1: Select or Input Your Resume")
    
    cv_source = st.radio(
        "Select CV Source", 
        ["Use Active Managed CV", "Upload New/Paste Text"],
        key="analyzer_cv_source"
    )
    
    resume_source = None
    source_type = None
    
    if cv_source == "Use Active Managed CV":
        if not active_cv_name:
            st.warning("No active CV set. Please go to the **CV Management** tab to select or upload one.")
            return
        st.info(f"Using **Active CV:** `{active_cv_name}`")
        # For analysis purposes, we need the raw text, which we don't store in managed_cvs.
        # We will adjust the logic to use the *parsed data* directly for evaluation,
        # but for the sake of simplicity, we will force a re-upload or prompt user.
        # ***FOR THIS IMPLEMENTATION, we will assume "managed CV" means using the PARSED data.***
        active_cv_data = st.session_state.managed_cvs.get(active_cv_name)
        
    elif cv_source == "Upload New/Paste Text":
        resume_method = st.radio(
            "Input Method", 
            ["Upload File (PDF/DOCX)", "Paste Text"],
            key="analyzer_resume_method"
        )
        
        uploaded_file = None
        pasted_resume_text = ""
        
        if resume_method == "Upload File (PDF/DOCX)":
            uploaded_file = st.file_uploader(
                "Upload your Resume",
                type=["pdf", "docx", "txt"],
                key="analyzer_resume_upload"
            )
            if uploaded_file:
                resume_source = uploaded_file
                source_type = 'file'
        else:
            pasted_resume_text = st.text_area(
                "Paste your Resume Text here",
                height=200,
                key="analyzer_resume_text_area"
            )
            if pasted_resume_text.strip():
                resume_source = pasted_resume_text.strip()
                source_type = 'text'

    # --- Education Form (Keeping this in the Analyzer tab as requested previously) ---
    st.markdown("#### Manually Add/Correct Education Entry")
    with st.expander("Add Structured Education"):
        with st.form("education_entry_form", clear_on_submit=True):
            col_degree, col_college = st.columns(2)
            with col_degree:
                new_degree = st.text_input("Degree/Qualification", key="analyzer_new_degree")
            with col_college:
                new_college = st.text_input("College/Institution Name", key="analyzer_new_college")
            
            new_university = st.text_input("Affiliating University Name", key="analyzer_new_university")

            col_from, col_to = st.columns(2)
            with col_from:
                new_date_from = st.date_input("Date From (Start)", value=date(2018, 1, 1), key="analyzer_new_date_from")
            with col_to:
                new_date_to = st.date_input("Date To (End/Expected)", value=date.today(), key="analyzer_new_date_to")

            if st.form_submit_button("Add Education to List"):
                add_education_entry(
                    new_degree.strip(), 
                    new_college.strip(), 
                    new_university.strip(), 
                    new_date_from, 
                    new_date_to
                )
    
        if st.session_state.get('manual_education'):
            st.markdown("##### Current Manually Added Education Entries:")
            for entry in st.session_state.manual_education:
                st.code(entry, language="text")
    # --- End Education Form ---

    st.markdown("---")
    
    st.markdown("### Step 2: Provide the Job Description (JD)")
    
    # --- JD Input ---
    jd_content = st.text_area(
        "Paste the full Job Description Text",
        height=300,
        key="analyzer_jd_text_area"
    )
    
    jd_name = "Custom JD"
    if jd_content:
         first_line = jd_content.splitlines()[0].strip()
         jd_name = st.text_input("Job Title for Tracking", value=first_line if len(first_line) < 50 else "Pasted JD", key="analyzer_jd_title_input")
        
    st.markdown("---")
    
    # --- Run Analysis Button ---
    if st.button("✨ Run Resume Match Analysis", key="run_analysis_btn", type="primary", use_container_width=True):
        
        # Validation checks
        if cv_source == "Use Active Managed CV" and not active_cv_data:
            st.error("❌ Please set an active CV in the CV Management tab or upload a new one.")
            return
        
        if cv_source == "Upload New/Paste Text" and not resume_source:
            st.error("❌ Please provide your resume using the selected method.")
            return

        if not jd_content.strip():
            st.error("❌ Please provide the Job Description content.")
            return
        
        if not GROQ_API_KEY:
            st.error("❌ AI Analysis is disabled. Please ensure the `GROQ_API_KEY` is set.")
            return

        # Execution
        with st.spinner(f"Running analysis against '{jd_name}'..."):
            try:
                if active_cv_data:
                    # If using Managed CV, we skip file extraction/parsing, and go straight to analysis
                    # Note: We simulate the structure that parse_and_analyze_resume returns
                    jd_metadata = extract_jd_metadata(jd_content.strip())
                    match_analysis = evaluate_jd_fit(jd_content.strip(), active_cv_data)
                    overall_score_match = re.search(r'Overall Fit Score:\s*[^\d]*(\d+)\s*/10', match_analysis, re.IGNORECASE)
                    overall_score = overall_score_match.group(1) if overall_score_match else 'N/A'
                    
                    analysis_result = {
                        "name": active_cv_data.get('name', active_cv_name),
                        "date": date.today().strftime("%Y-%m-%d"),
                        "jd_name": jd_name,
                        "jd_role": jd_metadata.get('role', 'N/A'),
                        "overall_score": overall_score,
                        "match_report": match_analysis,
                        "parsed_resume": active_cv_data # Use the stored parsed data
                    }
                else:
                    # If using fresh upload/paste, run the full process
                    analysis_result = parse_and_analyze_resume(
                        resume_source, 
                        jd_content.strip(), 
                        source_type=source_type, 
                        jd_name=jd_name
                    )

                if "error" in analysis_result:
                    st.error(f"Analysis Failed: {analysis_result['error']}")
                else:
                    st.session_state.candidate_results.insert(0, analysis_result)
                    st.session_state.current_resume = analysis_result
                    st.success(f"✅ Analysis complete! Score: **{analysis_result['overall_score']}/10**")
                    st.balloons()
                    st.rerun() 
                        
            except Exception as e:
                st.error(f"An unexpected error occurred during analysis: {e}")
                st.code(traceback.format_exc())

    st.markdown("---")
    
    # --- Display Current Analysis Result ---
    if st.session_state.current_resume:
        result = st.session_state.current_resume
        st.subheader(f"Latest Results for **{result['name']}**")
        
        col_score, col_jd_info, col_date = st.columns(3)
        with col_score:
            score = result['overall_score']
            is_digit = score.isdigit()
            st.metric(
                label="Overall Match Score", 
                value=f"{score}/10", 
                delta="Excellent" if is_digit and int(score) >= 8 else ("Good" if is_digit and int(score) >= 6 else "Needs Work"), 
                delta_color="normal"
            )
        with col_jd_info:
            st.markdown(f"**Target Role:** `{result.get('jd_role', 'N/A')}`")
            st.markdown(f"**Job Title:** `{result.get('jd_name', 'Custom JD')}`")
        with col_date:
            st.markdown(f"**Analysis Date:** `{result['date']}`")
            st.markdown(f"**Candidate Name:** `{result['name']}`")
            
        st.markdown("---")
        
        st.subheader("Detailed Match Report")
        st.text(result['match_report'])
        
        # Display Parsed Data (Always show parsed/stored data)
        with st.expander("View Full Parsed Resume Data"):
            st.json(result['parsed_resume'])
        
        if st.session_state.get('manual_education'):
             with st.expander("View Manually Added Education"):
                st.json(st.session_state.manual_education)

    else:
        st.info("Run an analysis above to view your first match report here.")


def tab_application_history():
    st.header("📝 Application History")
    
    if not st.session_state.get('candidate_results'):
        st.info("No analysis results found. Run a new analysis on the 'Resume Analyzer' tab to build your history.")
        return

    # Prepare data for display
    history_data = []
    for res in st.session_state.candidate_results:
        try:
            numeric_score = int(res['overall_score'])
        except:
            numeric_score = 0
        
        history_data.append({
            "Date": res['date'],
            "Job Title": res['jd_name'],
            "Role Found": res['jd_role'],
            "Match Score (out of 10)": res['overall_score'],
            "Sort_Score": numeric_score,
        })
        
    history_data.sort(key=lambda x: (x['Date'], x['Sort_Score']), reverse=True)
    
    st.markdown("### Your Past Resume Analysis Matches")
    
    st.dataframe(
        history_data,
        column_order=["Date", "Job Title", "Role Found", "Match Score (out of 10)"],
        hide_index=True,
        use_container_width=True
    )
    
    st.markdown("---")
    st.markdown("### View Detailed Reports")
    
    for i, res in enumerate(st.session_state.candidate_results):
        header_text = f"{res['date']} | **{res['jd_name']}** (Score: **{res['overall_score']}/10**)"
        with st.expander(header_text):
            st.markdown("#### Full Match Report")
            st.text(res['match_report'])
            
            if res.get('parsed_resume', {}).get('summary'):
                st.markdown("---")
                st.markdown(f"**Resume Summary:** *{res['parsed_resume']['summary']}*")


# -------------------------
# CANDIDATE DASHBOARD FUNCTION
# -------------------------

def candidate_dashboard():
    st.title("🧑‍💻 Candidate Dashboard")
    st.caption("Manage your CVs and analyze job fit using Groq LLMs.")
    
    col_header, col_logout = st.columns([4, 1])
    with col_logout:
        if st.button("🚪 Log Out", use_container_width=True):
            keys_to_delete = ['candidate_results', 'current_resume', 'manual_education', 'managed_cvs', 'current_resume_name']
            for key in keys_to_delete:
                if key in st.session_state:
                    del st.session_state[key]
            go_to("login")
            st.rerun() 
            
    st.markdown("---")

    # --- Session State Initialization for Candidate ---
    if "candidate_results" not in st.session_state: st.session_state.candidate_results = []
    if "current_resume" not in st.session_state: st.session_state.current_resume = None
    if "manual_education" not in st.session_state: st.session_state.manual_education = []
    if "managed_cvs" not in st.session_state: st.session_state.managed_cvs = {} # New State for CVs
    if "current_resume_name" not in st.session_state: st.session_state.current_resume_name = None # New State for active CV

    # --- Main Tabs ---
    tab_cv, tab_analyzer, tab_history = st.tabs(["📊 CV Management", "🚀 Resume Analyzer", "📝 Application History"])

    with tab_cv:
        tab_cv_management()

    with tab_analyzer:
        tab_resume_analyzer()

    with tab_history:
        tab_application_history()


# -------------------------
# MOCK LOGIN AND MAIN APP LOGIC (For full execution)
# -------------------------

def admin_dashboard():
    st.title("Admin Dashboard (Mock)")
    st.info("This is a placeholder for the Admin Dashboard. Use the Log Out button to switch.")
    if st.button("🚪 Log Out (Switch to Candidate)"):
        go_to("candidate_dashboard")
        st.session_state.user_type = "candidate"
        st.rerun()

def login_page():
    st.title("Welcome to PragyanAI")
    st.header("Login")
    
    with st.form("login_form"):
        username = st.text_input("Username (Enter 'candidate' or 'admin')")
        password = st.text_input("Password (Any value)", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            if username.lower() == "candidate":
                st.session_state.logged_in = True
                st.session_state.user_type = "candidate"
                go_to("candidate_dashboard")
                st.success("Logged in as Candidate!")
                st.rerun()
            elif username.lower() == "admin":
                st.session_state.logged_in = True
                st.session_state.user_type = "admin"
                go_to("admin_dashboard")
                st.success("Logged in as Admin!")
                st.rerun()
            else:
                st.error("Invalid username. Please use 'candidate' or 'admin'.")

# --- Main App Execution ---

if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="PragyanAI Candidate Dashboard")

    # Initialize state for navigation and authentication
    if 'page' not in st.session_state: st.session_state.page = "login"
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if 'user_type' not in st.session_state: st.session_state.user_type = None
    
    if st.session_state.logged_in:
        if st.session_state.user_type == "candidate":
            candidate_dashboard()
        elif st.session_state.user_type == "admin":
            admin_dashboard() 
    else:
        login_page()
