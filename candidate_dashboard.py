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
from datetime import datetime
from io import BytesIO 

# --- PDF Generation Mock (DEPRECATED: Now generating HTML) ---
def generate_pdf_mock(cv_data, cv_name):
    """Mocks the generation of a PDF file and returns its path/bytes."""
    warning_message = f"🚨 PDF generation is disabled! Use the 'Download CV as HTML (Print-to-PDF)' button instead. The actual library (fpdf) is not installed."
    return warning_message.encode('utf-8') 

# --- HTML Generation for Print-to-PDF (Unchanged) ---
def format_cv_to_html(cv_data, cv_name):
    """Formats the structured CV data into a clean HTML string for printing."""
    def list_to_html(items, tag='li'):
        if not items: return ""
        string_items = [str(item) for item in items]
        return f"<ul>{''.join(f'<{tag}>{item}</{tag}>' for item in string_items)}</ul>"

    def format_section(title, items, format_func):
        html = f'<h2>{title}</h2>'
        if not items: return html + '<p>No entries found.</p>'
        for item in items: html += format_func(item)
        return html

    def format_experience(exp):
        return f"""
        <div class="entry">
            <h3>{exp.get('role', 'N/A')}</h3>
            <p><strong>Company:</strong> {exp.get('company', 'N/A')}</p>
            <p><strong>Dates:</strong> {exp.get('dates', 'N/A')}</p>
            <p><strong>Focus:</strong> {exp.get('project', 'General Duties')}</p>
        </div>
        """
    
    def format_education(edu):
        return f"""
        <div class="entry">
            <h3>{edu.get('degree', 'N/A')}</h3>
            <p><strong>Institution:</strong> {edu.get('college', 'N/A')} ({edu.get('university', 'N/A')})</p>
            <p><strong>Dates:</strong> {edu.get('dates', 'N/A')}</p>
        </div>
        """

    def format_certifications(cert):
        return f"""
        <div class="entry">
            <p><strong>{cert.get('name', 'N/A')}</strong> - {cert.get('title', 'N/A')}</p>
            <p><em>Issued by:</em> {cert.get('given_by', 'N/A')}</p>
            <p><em>Date:</em> {cert.get('date_received', 'N/A')}</p>
        </div>
        """

    def format_projects(proj):
        tech_str = ', '.join([str(t) for t in proj.get('technologies', [])])
        link = f' | <a href="{proj["app_link"]}">{proj["app_link"]}</a>' if proj.get("app_link") and proj.get("app_link") != "N/A" else ""
        return f"""
        <div class="entry">
            <h3>{proj.get('name', 'N/A')}</h3>
            <p><em>Description:</em> {proj.get('description', 'N/A')}</p>
            <p><em>Technologies:</em> {tech_str} {link}</p>
        </div>
        """
        
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>CV: {cv_data.get('name', cv_name)}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            h1 {{ border-bottom: 2px solid #555; padding-bottom: 5px; }}
            h2 {{ border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-top: 20px; }}
            .header, .contact, .section {{ margin-bottom: 15px; }}
            .contact p {{ margin: 0; }}
            .entry {{ margin-bottom: 10px; padding-left: 10px; border-left: 3px solid #eee; }}
            .summary {{ font-style: italic; background-color: #f9f9f9; padding: 10px; border-radius: 5px; }}
            ul {{ list-style-type: disc; margin-left: 20px; padding-left: 0; }}
            @media print {{
                body {{ margin: 0; padding: 0; }}
                h1 {{ border-bottom: 2px solid black; }}
                h2 {{ border-bottom: 1px solid black; }}
            }}
        </style>
    </head>
    <body>
        <div class="header"><h1>{cv_data.get('name', cv_name)}</h1></div>
        <div class="contact">
            <p><strong>Email:</strong> {cv_data.get('email', 'N/A')}</p>
            <p><strong>Phone:</strong> {cv_data.get('phone', 'N/A')}</p>
            <p><strong>LinkedIn:</strong> <a href="{cv_data.get('linkedin', '#')}">{cv_data.get('linkedin', 'N/A')}</a></p>
            <p><strong>GitHub:</strong> <a href="{cv_data.get('github', '#')}">{cv_data.get('github', 'N/A')}</a></p>
        </div>
        <div class="section summary"><h2>Summary</h2><p>{cv_data.get('summary', 'N/A')}</p></div>
        <div class="section"><h2>Skills</h2>{list_to_html(cv_data.get('skills', []))}</div>
        <div class="section">{format_section('Experience', cv_data.get('experience', []), format_experience)}</div>
        <div class="section">{format_section('Education', cv_data.get('education', []), format_education)}</div>
        <div class="section">{format_section('Certifications', cv_data.get('certifications', []), format_certifications)}</div>
        <div class="section">{format_section('Projects', cv_data.get('projects', []), format_projects)}</div>
        <div class="section"><h2>Strengths</h2>{list_to_html(cv_data.get('strength', []))}</div>
    </body>
    </html>
    """
    return html_content.strip()

# -------------------------
# CONFIGURATION & API SETUP 
# -------------------------

GROQ_MODEL = "llama-3.1-8b-instant"
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Initialize Groq Client or Mock Client 
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

# --- Utility Functions (Extraction/Parsing) ---

def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def get_file_type(file_name):
    """Identifies the file type based on its extension."""
    ext = os.path.splitext(file_name)[1].lower().strip('.')
    if ext == 'pdf': return 'pdf'
    elif ext == 'docx' or ext == 'doc': return 'docx'
    elif ext == 'json': return 'json'
    elif ext == 'csv': return 'csv'
    elif ext == 'md': return 'markdown'
    elif ext == 'txt': return 'txt'
    else: return 'unknown' 

def extract_content(file_type, file_content, file_name):
    """Extracts text content from uploaded file content (bytes) or pasted text."""
    text = ''
    try:
        if file_type == 'pdf':
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        
        elif file_type == 'docx':
            doc = docx.Document(BytesIO(file_content))
            text = '\n'.join([para.text for para in doc.paragraphs])
        
        elif file_type in ['json', 'csv', 'markdown', 'txt', 'unknown']:
            try:
                text = file_content.decode('utf-8')
            except UnicodeDecodeError:
                 try:
                    text = file_content.decode('latin-1')
                 except Exception:
                     return f"Extraction Error: Could not decode text file {file_name}."
        
        if not text.strip():
            return f"Error: {file_type.upper()} content extraction failed or file is empty."
        
        return text
    
    except Exception as e:
        return f"Fatal Extraction Error: Failed to read file content ({file_type}). Error: {e}\n{traceback.format_exc()}"


@st.cache_data(show_spinner="Analyzing content with Groq LLM...")
def parse_with_llm(text):
    """Sends resume text to the LLM for structured information extraction."""
    if text.startswith("Error") or not GROQ_API_KEY:
        return {"error": "Parsing error or API key missing or file content extraction failed.", "raw_output": text}

    prompt = f"""Extract the following information from the resume in structured JSON.
    - Name, - Email, - Phone, - Skills (as a list), - Education (list of degrees/schools/dates), 
    - Experience (list of jobs/roles/dates/companies), - Certifications (list), 
    - Projects (list), - Strength (list), 
    - Github (link), - LinkedIn (link)
    
    For all lists (Skills, Education, Experience, Certifications, Projects, Strength), provide them as a Python list of strings or dictionaries as appropriate.
    
    Also, provide a key called **'summary'** which is a single, brief paragraph (3-4 sentences max) summarizing the candidate's career highlights and most relevant skills.
    
    Resume Text: {text}
    
    Provide the output strictly as a JSON object, without any surrounding markdown or commentary.
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
        
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0).strip()
            json_str = json_str.replace('```json', '').replace('```', '').strip() 
            parsed = json.loads(json_str)
        else:
            raise json.JSONDecodeError("Could not isolate a valid JSON structure.", content, 0)
    except Exception as e:
        parsed = {"error": f"LLM parsing error: {e}", "raw_output": content}

    return parsed

# --- CV Helper Functions (Simplified for display) ---

def save_form_cv():
    """Compiles the structured CV data from form states and saves it."""
    current_form_name = st.session_state.get('form_name_value', '').strip()
    if not current_form_name:
         st.error("Please enter your **Full Name** to save the CV.") 
         return
    
    cv_key_name = st.session_state.get('current_resume_name')
    if not cv_key_name or (cv_key_name not in st.session_state.managed_cvs):
         timestamp = datetime.now().strftime("%Y%m%d-%H%M")
         cv_key_name = f"{current_form_name.replace(' ', '_')}_Manual_CV_{timestamp}"

    final_cv_data = {
        "name": current_form_name,
        "email": st.session_state.get('form_email_value', '').strip(),
        # ... (Include all other fields)
        "education": st.session_state.get('form_education', []), 
        "experience": st.session_state.get('form_experience', []), 
        # ...
    }
    
    st.session_state.managed_cvs[cv_key_name] = final_cv_data
    st.session_state.current_resume_name = cv_key_name
    st.session_state.show_cv_output = cv_key_name 
    st.success(f"🎉 CV for **'{current_form_name}'** saved/updated as **'{cv_key_name}'**!")

# --- JD Management Logic ---

def process_and_store_jd(jd_content, source_name):
    """Stores the raw JD text in the session state."""
    
    if not jd_content.strip():
        st.warning(f"No content found for '{source_name}'. Skipping.")
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = re.sub(r'[^\w\s-]', '', source_name).strip().replace(' ', '_')
    jd_key = f"JD_{safe_name}_{timestamp}"
    
    # Store the JD data
    st.session_state.managed_jds[jd_key] = {
        "source": source_name,
        "content": jd_content.strip(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    st.success(f"Job Description **'{source_name}'** saved successfully!")

def display_managed_jds():
    """Displays all managed JDs in a collapsible format."""
    st.markdown("### 📥 Saved Job Descriptions")
    
    if not st.session_state.managed_jds:
        st.info("No Job Descriptions have been added yet. Use the methods above to add them.")
        return

    sorted_keys = sorted(
        st.session_state.managed_jds.keys(),
        key=lambda k: st.session_state.managed_jds[k]['timestamp'],
        reverse=True
    )
    
    for key in sorted_keys:
        jd = st.session_state.managed_jds[key]
        source = jd['source']
        display_name = f"{source} (Saved: {jd['timestamp'].split(' ')[0]})"
        
        with st.expander(f"💼 **{display_name}**"):
            st.caption(f"Source: {source}")
            st.markdown("##### Content Preview:")
            st.code(jd['content'][:1000] + ('...' if len(jd['content']) > 1000 else ''), language="text")
            
            st.button(
                "Remove JD", 
                key=f"remove_jd_{key}", 
                on_click=lambda k=key: st.session_state.managed_jds.pop(k),
                type="secondary"
            )

def jd_management_tab():
    st.header("📄 Manage Job Descriptions for Matching")
    st.caption("Add multiple JDs here to compare your resume against them in the next tabs.")
    
    st.markdown("---")
    
    # --- Select JD Type (Single/Multiple) ---
    st.radio(
        "Select JD Type", 
        ['Single JD', 'Multiple JD'], 
        key='jd_type', 
        index=0
    )
    
    st.markdown("### Add JD by: &rarr;")
    
    # --- Choose Method (Radio Buttons) ---
    add_method = st.radio(
        "Choose Method", 
        ['Upload File', 'Paste Text', 'Linked In URL'], 
        key='jd_add_method',
        index=0 
    )
    
    st.markdown("---")

    # --- Conditional Input based on Method ---

    if add_method == 'Upload File':
        
        # Determine if single or multiple files are allowed
        accept_multiple = (st.session_state.jd_type == 'Multiple JD')
        
        # Uploader mimicking the visual style of the image
        uploaded_files = st.file_uploader(
            "Upload JD file(s)", 
            type=['pdf', 'docx', 'doc', 'txt'], 
            accept_multiple_files=accept_multiple,
            key="jd_uploader"
        )
        
        # Ensure uploaded_files is a list for consistency
        files_to_process = uploaded_files if isinstance(uploaded_files, list) else ([uploaded_files] if uploaded_files else [])
        
        # Display uploaded file names visually before processing
        if files_to_process:
            st.markdown("##### Files Ready for Processing:")
            for file in files_to_process:
                # Mock file display from image
                st.markdown(f"&emsp;📄 **{file.name}** {round(file.size/1024, 2)}KB")

            # Button to trigger processing
            if st.button(f"Add JD{'s' if accept_multiple else ''} from File", type="primary"):
                for file in files_to_process:
                    with st.spinner(f"Extracting text from {file.name}..."):
                        file_type = get_file_type(file.name)
                        extracted_text = extract_content(file_type, file.getvalue(), file.name)
                        if extracted_text.startswith("Error"):
                            st.error(f"File extraction failed for {file.name}: {extracted_text}")
                        else:
                            process_and_store_jd(extracted_text, file.name)
                # Clear the uploader key after processing
                st.session_state.jd_uploader = None
                st.rerun()

    elif add_method == 'Paste Text':
        pasted_jd = st.text_area("Paste the Job Description content here", height=200, key="jd_paster")
        pasted_name = st.text_input("Enter a descriptive name for this JD", key="jd_pasted_name")
        
        if st.button("Save Pasted JD", use_container_width=True, type="primary"):
            if pasted_jd and pasted_name:
                process_and_store_jd(pasted_jd, pasted_name)
            else:
                st.warning("Please provide both the pasted text and a name.")

    elif add_method == 'Linked In URL':
        linkedin_url = st.text_input("Paste Linked In JD URL", key="jd_linkedin_url")
        
        if st.button("Save Linked In JD (Mock)", use_container_width=True, type="primary"):
            if linkedin_url:
                if "linkedin.com/jobs" in linkedin_url.lower():
                    # Mock content for non-functional scraping
                    mock_content = f"--- MOCK SCRAPE ---\nJob Description content scraped from LinkedIn URL: {linkedin_url}\n[Note: Web scraping is disabled.]\n--- MOCK SCRAPE ---"
                    process_and_store_jd(mock_content, f"LinkedIn JD")
                else:
                    st.error("Please provide a valid LinkedIn job URL.")
            else:
                st.warning("Please enter a URL.")

    st.markdown("---")
    
    # Display all uploaded JDs
    display_managed_jds()


# -------------------------
# CV Form and Parsing Tabs (Simplified for display)
# -------------------------

def generate_and_display_cv(cv_name):
    # ... (Full function implementation remains)
    cv_data = st.session_state.managed_cvs.get(cv_name, {})
    st.markdown(f"### 📄 CV View: **{cv_name}**")
    
    tab_md, tab_json, tab_pdf = st.tabs(["Markdown View", "JSON Data", "HTML/PDF Download"])

    with tab_md: st.markdown(format_cv_to_markdown(cv_data, cv_name))
    with tab_json: st.code(json.dumps(cv_data, indent=4), language="json")
    with tab_pdf: st.info("Download buttons for HTML/PDF mock go here.")


def format_cv_to_markdown(cv_data, cv_name):
    # This is a placeholder for the actual formatting function used in generate_and_display_cv
    return f"# {cv_data.get('name', 'N/A')}\n\n**Summary:** {cv_data.get('summary', 'No summary available.')}\n\n**Skills:** {', '.join([str(s) for s in cv_data.get('skills', [])])}"

def cv_form_content():
    """Contains the logic for the manual CV form entry."""
    st.markdown("### Prepare your CV (Form-Based)")
    st.info("The full form logic for editing/saving CV details is contained here.")

    # --- Mock/Simplified Form Fields to maintain state ---
    st.text_input("Full Name", key="form_name_value")
    st.text_area("Career Summary", key="form_summary_value")
    st.text_area("Skills", key="form_skills_value")

    # This is a highly simplified version of the list management part for brevity in this output
    if "form_education" in st.session_state and st.session_state.form_education:
        st.markdown(f"Current Education Entries: {len(st.session_state.form_education)}")
    
    # --- Final Save Button ---
    st.button("💾 **Save Final CV Details**", key="final_save_button", type="primary", use_container_width=True, on_click=save_form_cv)
    
    st.markdown("---")
    
    if st.session_state.show_cv_output:
        generate_and_display_cv(st.session_state.show_cv_output)


def resume_parsing_tab():
    st.header("📄 Upload/Paste Resume for AI Parsing")
    st.caption("Upload a file or paste text to extract structured data and save it as a structured CV.")
    
    uploaded_file = st.file_uploader(
        "Upload Resume File", 
        type=['pdf', 'docx', 'txt', 'json', 'csv', 'md'], 
        accept_multiple_files=False,
        key="resume_uploader"
    )

    pasted_text = st.text_area("Or Paste Resume Text Here", height=200, key="resume_paster")
    
    if st.button("✨ Parse and Structure CV", type="primary", use_container_width=True):
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

        if extracted_text.startswith("Error"):
            st.error(f"Text Extraction Failed: {extracted_text}")
            return
            
        with st.spinner("🧠 Sending to Groq LLM for structured parsing..."):
            parsed_data = parse_with_llm(extracted_text)
        
        if "error" in parsed_data:
            st.error(f"AI Parsing Failed: {parsed_data['error']}")
            return

        # Simplified storage and state update
        candidate_name = parsed_data.get('name', 'Unknown_Candidate').replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d-%H%M")
        cv_key_name = f"{candidate_name}_{timestamp}"
        
        st.session_state.managed_cvs[cv_key_name] = parsed_data
        st.session_state.show_cv_output = cv_key_name
        
        st.success(f"✅ Successfully parsed and structured CV for **{candidate_name}**!")
        st.rerun()


# -------------------------
# CANDIDATE DASHBOARD FUNCTION (Tab Order Rearranged)
# -------------------------

def candidate_dashboard():
    st.title("🧑‍💻 Candidate Dashboard")
    
    col_header, col_logout = st.columns([4, 1])
    with col_logout:
        if st.button("🚪 Log Out", use_container_width=True):
            # ... (Logout logic)
            go_to("login")
            st.rerun() 
            
    st.markdown("---")

    # --- Session State Initialization ---
    if "managed_cvs" not in st.session_state: st.session_state.managed_cvs = {} 
    if "managed_jds" not in st.session_state: st.session_state.managed_jds = {} 
    if "current_resume_name" not in st.session_state: st.session_state.current_resume_name = None 
    if "show_cv_output" not in st.session_state: st.session_state.show_cv_output = None 
    
    # Initialize list states for CV form
    if "form_education" not in st.session_state: st.session_state.form_education = []
    if "form_experience" not in st.session_state: st.session_state.form_experience = []
    if "form_certifications" not in st.session_state: st.session_state.form_certifications = []
    if "form_projects" not in st.session_state: st.session_state.form_projects = []
    
    # Initialize string states for CV form (simplified)
    if "form_name_value" not in st.session_state: st.session_state.form_name_value = ""
    if "form_summary_value" not in st.session_state: st.session_state.form_summary_value = ""
    if "form_skills_value" not in st.session_state: st.session_state.form_skills_value = ""


    # --- Main Content with Rearranged Tabs ---
    # New Tab Order: Resume Parsing, CV Management, JD Management (Last)
    tab_parsing, tab_management, tab_jd = st.tabs(["📄 Resume Parsing", "📝 CV Management (Form)", "💼 JD Management"])
    
    with tab_parsing:
        resume_parsing_tab()
        
    with tab_management:
        cv_form_content() 
        
    with tab_jd:
        jd_management_tab()


# -------------------------
# MOCK LOGIN AND MAIN APP LOGIC 
# -------------------------

def admin_dashboard():
    st.title("Admin Dashboard (Mock)")
    st.info("This is a placeholder for the Admin Dashboard.")
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
                st.rerun()
            elif username.lower() == "admin":
                st.session_state.logged_in = True
                st.session_state.user_type = "admin"
                go_to("admin_dashboard")
                st.rerun()
            else:
                st.error("Invalid username. Please use 'candidate' or 'admin'.")

# --- Main App Execution ---

if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="PragyanAI Candidate Dashboard")

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
