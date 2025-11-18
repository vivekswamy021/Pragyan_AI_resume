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
import time
import pandas as pd
import base64 

# --- CONFIGURATION & API SETUP ---

GROQ_MODEL = "llama-3.1-8b-instant"
# Load environment variables (e.g., GROQ_API_KEY)
load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# --- Default/Mock Data for Filtering ---
DEFAULT_ROLES = ["Data Scientist", "Cloud Engineer", "Software Engineer", "AI/ML Engineer"]
DEFAULT_JOB_TYPES = ["Full-time", "Contract", "Remote"]
STARTER_KEYWORDS = {
    "Python", "MySQL", "GCP", "cloud computing", "ML", 
    "API services", "LLM integration", "JavaScript", "SQL", "AWS", "MLOps", "Data Visualization"
}
# --- End Default/Mock Data ---


# --- Define MockGroqClient globally ---

class MockGroqClient:
    """Mock client for local testing when Groq is not available or key is missing."""
    # The structure must mimic the actual Groq client for client = Groq(...) to work.
    def chat(self):
        class Completions:
            def create(self, **kwargs):
                prompt_content = kwargs.get('messages', [{}])[0].get('content', '')
                
                # Check if it's a JD Q&A call
                if "Answer the following question about the Job Description concisely and directly." in prompt_content:
                    question_match = re.search(r'Question:\s*(.*)', prompt_content)
                    question = question_match.group(1).strip() if question_match else "a question"
                    
                    if 'role' in question.lower():
                        return type('MockResponse', (object,), {'choices': [type('Choice', (object,), {'message': type('Message', (object,), {'content': 'The required role in this Job Description is Cloud Engineer.'})()})()]})
                    elif 'experience' in question.lower():
                        # --- SYNTAX FIX APPLIED HERE ---
                        # Fixed the incorrect closing parenthesis structure. 
                        # It should be: type('Choice', (object,), {'message': Message_Object})()
                        # where Message_Object is: type('Message', (object,), {'content': '...'})()
                        return type('MockResponse', (object,), {'choices': [type('Choice', (object,), {'message': type('Message', (object,), {'content': 'The job requires 3+ years of experience in AWS/GCP and infrastructure automation.'})()})()]})
                        # --- END SYNTAX FIX ---
                    else:
                        return type('MockResponse', (object,), {'choices': [type('Choice', (object,), {'message': type('Message', (object,), {'content': f'Mock answer for JD question: The JD mentions Python and Docker as key skills.'})()})()]})

                # Check if it's a Resume Q&A call
                elif "Answer the following question about the resume concisely and directly." in prompt_content:
                    question_match = re.search(r'Question:\s*(.*)', prompt_content)
                    question = question_match.group(1).strip() if question_match else "a question"
                    
                    if 'name' in question.lower():
                        return type('MockResponse', (object,), {'choices': [type('Choice', (object,), {'message': type('Message', (object,), {'content': 'The candidate\'s name is Vivek Swamy.'})()})()]})
                    elif 'skills' in question.lower():
                        return type('MockResponse', (object,), {'choices': [type('Choice', (object,), {'message': type('Message', (object,), {'content': 'Key skills include Python, SQL, AWS, and MLOps.'})()})()]})
                    else:
                        return type('MockResponse', (object,), {'choices': [type('Choice', (object,), {'message': type('Message', (object,), {'content': f'Based on the mock resume data, I can provide a simulated answer to your question about {question}.'})()})()]})


                # Mock candidate data (Vivek Swamy) for parsing
                mock_llm_json = {
                    "name": "Vivek Swamy", 
                    "email": "vivek.swamy@example.com", 
                    "phone": "555-1234", 
                    "linkedin": "https://linkedin.com/in/vivek-swamy-mock", 
                    "github": "https://github.com/vivek-mock", 
                    # --- FIX: Ensure personal_details is a string, not an empty dict ---
                    "personal_details": "Highly motivated individual based in San Francisco, CA.", 
                    # --- END FIX ---
                    "skills": [
                        "Python", "SQL", "AWS", "Streamlit", 
                        "LLM Integration", "MLOps", "Data Visualization", 
                        "Docker", "Kubernetes", "Java", "API Services" 
                    ], 
                    "education": ["B.S. Computer Science, Mock University, 2020"], 
                    "experience": ["Software Intern, Mock Solutions (2024-2025)", "Data Analyst, Test Corp (2022-2024)"], 
                    "certifications": ["Mock Certification in AWS Cloud"], 
                    "projects": ["Mock Project: Built an MLOps pipeline using Docker and Kubernetes."], 
                    "strength": ["Mock Strength"], 
                }
                
                # Mock response content for GroqClient initialization check
                message_obj = type('Message', (object,), {'content': json.dumps(mock_llm_json)})()
                choice_obj = type('Choice', (object,), {'message': message_obj})()
                response_obj = type('MockResponse', (object,), {'choices': [choice_obj]})()
                return response_obj
        
        # Add a placeholder for the completions object if we need a mock response for fit evaluation
        class FitCompletions(Completions):
            def create(self, **kwargs):
                prompt_content = kwargs.get('messages', [{}])[0].get('content', '')
                
                if "Evaluate how well the following resume content matches the provided job description" in prompt_content:
                    # SIMULATED FIT LOGIC (Fallback for when the LLM-dependent function tries to run without a key)
                    
                    # Simple heuristic mock score based on role title in the prompt
                    jd_role_match = re.search(r'(?:Role|Engineer|Scientist)[:\s]+([\w\s/-]+)', prompt_content)
                    jd_role = jd_role_match.group(1).lower().strip() if jd_role_match else "default"
                    
                    if 'ai/ml' in jd_role or 'mlops' in jd_role:
                        score = 8
                    elif 'data scientist' in jd_role:
                        score = 7
                    elif 'cloud engineer' in jd_role:
                        score = 6
                    else:
                        score = 5
                        
                    # Calculate percentages based on the score to differentiate the rows
                    skills_p = 50 + (score * 5)
                    exp_p = 60 + (score * 3)
                    edu_p = 70 + (score * 1)
                    
                    # NOTE: This mock output uses the strict format expected by the regex parser below.
                    mock_fit_output = f"""
                    Overall Fit Score: {score}/10
                    
                    --- Section Match Analysis ---
                    Skills Match: {skills_p}%
                    Experience Match: {exp_p}%
                    Education Match: {edu_p}%
                    
                    Strengths/Matches:
                    - Mock Match Point 1 (Role: {jd_role})
                    - Mock Match Point 2
                    
                    Gaps/Areas for Improvement:
                    - Mock Gap 1
                    
                    Overall Summary: Mock summary for score {score}.
                    """
                    message_obj = type('Message', (object,), {'content': mock_fit_output})()
                    choice_obj = type('Choice', (object,), {'message': message_obj})()
                    response_obj = type('MockResponse', (object,), {'choices': [choice_obj]})()
                    return response_obj
                
                # Return standard parsing mock or Q&A mock
                return super().create(**kwargs)

        return FitCompletions()

try:
    # Attempt to import the real Groq client
    from groq import Groq
    
    if GROQ_API_KEY:
        client = Groq(api_key=GROQ_API_KEY)
        # Check if the client is really ready or just a placeholder
        if client:
             class GroqPlaceholder(Groq): 
                 def __init__(self, api_key): 
                     super().__init__(api_key=api_key)
                     self.client_ready = True
             client = GroqPlaceholder(api_key=GROQ_API_KEY)
        else:
            raise ValueError("Groq client not initialized successfully, falling back to Mock.")

    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set. Using Mock Client.")
        
except (ImportError, ValueError, NameError) as e:
    # Fallback to Mock Client
    client = MockGroqClient()
    
# --- END API SETUP ---


# --- Utility Functions ---

def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def get_file_type(file_name):
    """Identifies the file type based on its extension, handling common text formats."""
    ext = os.path.splitext(file_name)[1].lower().strip('.')
    if ext == 'pdf': return 'pdf'
    elif ext in ('docx', 'doc'): return 'docx'
    elif ext in ('txt', 'md', 'markdown', 'rtf'): return 'txt' 
    elif ext == 'json': return 'json'
    elif ext in ('xlsx', 'xls', 'csv'): return 'excel' 
    else: return 'unknown' 

def extract_content(file_type, file_content_bytes, file_name):
    """Extracts text content from uploaded file content (bytes)."""
    text = ''
    excel_data = None
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
        
        elif file_type == 'txt':
            try:
                # Try UTF-8 first, fallback to Latin-1
                text = file_content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                 text = file_content_bytes.decode('latin-1')
        
        elif file_type == 'json':
            try:
                # Wrap JSON content so LLM parsing function can detect and use it
                text = file_content_bytes.decode('utf-8')
                text = "--- JSON Content Start ---\n" + text + "\n--- JSON Content End ---"
            except UnicodeDecodeError:
                return f"[Error] JSON content extraction failed: Unicode Decode Error.", None
        
        elif file_type == 'excel':
            try:
                if file_name.endswith('.csv'):
                    df = pd.read_csv(BytesIO(file_content_bytes))
                else: 
                    xls = pd.ExcelFile(BytesIO(file_content_bytes))
                    all_sheets_data = {}
                    for sheet_name in xls.sheet_names:
                        df = pd.read_excel(xls, sheet_name=sheet_name)
                        all_sheets_data[sheet_name] = df.to_json(orient='records') 
                        
                    excel_data = all_sheets_data 
                    text = json.dumps(all_sheets_data, indent=2)
                    text = f"[EXCEL_CONTENT] The following structured data was extracted:\n{text}"
                    
            except Exception as e:
                return f"[Error] Excel/CSV file parsing failed. Error: {e}", None


        if not text.strip() and file_type not in ('excel', 'json'): 
            return f"[Error] {file_type.upper()} content extraction failed or file is empty.", None
        
        return text, excel_data
    
    except Exception as e:
        return f"[Error] Fatal Extraction Error: Failed to read file content ({file_type}). Error: {e}\n{traceback.format_exc()}", None

@st.cache_data(show_spinner="Analyzing content with Groq LLM...")
def parse_resume_with_llm(text):
    """
    Sends resume text to the LLM for structured information extraction.
    """
    
    def get_fallback_name():
        return "Vivek Swamy" 

    # 1. Handle Pre-flight errors (e.g., failed extraction)
    if text.startswith("[Error"):
        return {"name": "Parsing Error", "error": text}

    # 2. Check for and parse direct JSON content (for JSON file uploads)
    json_match_external = re.search(r'--- JSON Content Start ---\s*(.*?)\s*--- JSON Content End ---', text, re.DOTALL)
    
    if json_match_external:
        try:
            json_content = json_match_external.group(1).strip()
            parsed_data = json.loads(json_content)
            
            if not parsed_data.get('name'):
                 parsed_data['name'] = get_fallback_name()
                 
            parsed_data['error'] = None 
            
            return parsed_data
        
        except json.JSONDecodeError:
            return {"name": get_fallback_name(), "error": f"LLM Input Error: Could not decode uploaded JSON content into a valid structure."}
            
    # 3. Handle Mock Client execution (Fallback for PDF/DOCX/TXT)
    if isinstance(client, MockGroqClient) or not GROQ_API_KEY:
        try:
            # Use the mock client's default mock response for parsing
            completion = client.chat().create(model=GROQ_MODEL, messages=[{}])
            content = completion.choices[0].message.content.strip()
            parsed_data = json.loads(content)
            
            if not parsed_data.get('name'):
                 parsed_data['name'] = get_fallback_name()
            
            parsed_data['error'] = None 
            return parsed_data
            
        except Exception as e:
            return {"name": get_fallback_name(), "error": f"Mock Client Error: {e}"}

    # 4. Handle Real Groq Client execution 
    
    # --- FIX: Refined Prompt to request 'personal_details' as a single string summary ---
    prompt = f"""Extract the following information from the resume in structured JSON.
    Ensure all relevant details for each category are captured.
    - Name, - Email, - Phone, - Skills (list), - Education (list of degrees/institutions/dates), 
    - Experience (list of job roles/companies/dates/responsibilities), - Certifications (list), 
    - Projects (list of project names/descriptions/technologies), - Strength (list of personal strengths/qualities), 
    - Personal Details (Provide a single string summarizing details like address, date of birth, or nationality, if present. If not present, use an empty string ""), 
    - Github (URL), - LinkedIn (URL)
    
    Resume Text:
    {text}
    
    Provide the output strictly as a JSON object.
    """
    # --- END FIX ---
    
    content = ""
    parsed = {}
    json_str = ""
    
    try:
        response = client.chat.completions.create( 
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content.strip()

        # --- CRITICAL FIX: AGGRESSIVE JSON ISOLATION USING REGEX ---
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0).strip()
            
            if json_str.startswith('```json'):
                json_str = json_str[len('```json'):]
            if json_str.endswith('```'):
                json_str = json_str[:-len('```')]
            
            json_str = json_str.strip()
            
            parsed = json.loads(json_str)
        else:
            raise json.JSONDecodeError("Could not isolate a valid JSON structure from LLM response.", content, 0)
        
        # --- END CRITICAL FIX ---
        
        # Final cleanup for the app structure
        if not parsed.get('name'):
            parsed['name'] = get_fallback_name()
            
        parsed['error'] = None 
        return parsed

    except json.JSONDecodeError as e:
        error_msg = f"JSON decoding error from LLM. LLM returned malformed JSON. Error: {e} | Malformed string segment:\n---\n{json_str[:200]}..."
        return {"name": get_fallback_name(), "error": error_msg}
        
    except Exception as e:
        error_msg = f"LLM API interaction error: {e}"
        return {"name": get_fallback_name(), "error": error_msg}

# --- END ADAPTED FUNCTION ---


# --- NEW HELPER FUNCTION FOR HTML/PDF Generation ---

def generate_cv_html(parsed_data):
    """Generates a simple, print-friendly HTML string from parsed data for PDF conversion."""
    
    # Simple CSS for a clean, print-friendly CV look
    css = """
    <style>
        @page { size: A4; margin: 1cm; }
        body { font-family: 'Arial', sans-serif; line-height: 1.5; margin: 0; padding: 0; font-size: 10pt; }
        .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 1.8em; }
        .contact-info { display: flex; justify-content: center; font-size: 0.8em; color: #555; }
        .contact-info span { margin: 0 8px; }
        .section { margin-bottom: 15px; page-break-inside: avoid; }
        .section h2 { border-bottom: 1px solid #999; padding-bottom: 3px; margin-bottom: 8px; font-size: 1.1em; text-transform: uppercase; color: #333; }
        .item-list ul { list-style-type: disc; margin-left: 20px; padding-left: 0; margin-top: 0; }
        .item-list ul li { margin-bottom: 3px; }
        .item-list p { margin: 3px 0 8px 0; }
        a { color: #0056b3; text-decoration: none; }
    </style>
    """
    
    # --- HTML Structure ---
    html_content = f"<html><head>{css}<title>{parsed_data.get('name', 'CV')}</title></head><body>"
    
    # 1. Header and Contact Info
    html_content += '<div class="header">'
    html_content += f"<h1>{parsed_data.get('name', 'Candidate Name')}</h1>"
    
    contact_parts = []
    if parsed_data.get('email'): contact_parts.append(f"<span>📧 {parsed_data['email']}</span>")
    if parsed_data.get('phone'): contact_parts.append(f"<span>📱 {parsed_data['phone']}</span>")
    
    linkedin_url = parsed_data.get('linkedin')
    if linkedin_url:
        display_name = (linkedin_url.split('/')[-1] or 'LinkedIn').replace('-', ' ').title()
        contact_parts.append(f"<span>🔗 <a href='{linkedin_url}'>{display_name}</a></span>")

    github_url = parsed_data.get('github')
    if github_url:
        display_name = (github_url.split('/')[-1] or 'GitHub').replace('-', ' ').title()
        contact_parts.append(f"<span>💻 <a href='{github_url}'>{display_name}</a></span>")
    
    html_content += f'<div class="contact-info">{" | ".join(contact_parts)}</div>'
    html_content += '</div>'
    
    # 2. Sections
    # Defines the display order of sections
    section_order = ['personal_details', 'experience', 'projects', 'education', 'certifications', 'skills', 'strength']
    
    for k in section_order:
        v = parsed_data.get(k)
        
        # Skip contact details already handled
        if k in ['name', 'email', 'phone', 'linkedin', 'github']: continue 

        # --- FIX: Update check for valid data ---
        is_valid_data = False
        if isinstance(v, str) and v.strip():
            is_valid_data = True
        elif isinstance(v, list) and v:
            is_valid_data = True
        elif isinstance(v, dict) and any(val for val in v.values()): # Handle cases where LLM still returns dict with content
            is_valid_data = True
        
        if is_valid_data:
            
            html_content += f'<div class="section"><h2>{k.replace("_", " ").title()}</h2>'
            html_content += '<div class="item-list">'
            
            if k == 'personal_details':
                # FIX: Handle string summary (preferred) and fall back to dict
                if isinstance(v, str):
                    html_content += f"<p>{v}</p>"
                elif isinstance(v, dict):
                    # Format dictionary content as a simple list for display
                    details = [f"**{key.replace('_', ' ').title()}** : {value}" for key, value in v.items() if value]
                    if details:
                        html_content += '<ul>'
                        for detail in details:
                            html_content += f"<li>{detail}</li>"
                        html_content += '</ul>'
                    else:
                        # Skip if dictionary is empty/all values are empty
                        html_content = html_content.removesuffix(f'<div class="section"><h2>{k.replace("_", " ").title()}</h2><div class="item-list">')
                        continue

            elif isinstance(v, list):
                # Using <ul> for lists (experience, education, skills, etc.)
                html_content += '<ul>'
                for item in v:
                    if item: 
                        html_content += f"<li>{item}</li>"
                html_content += '</ul>'
            else:
                # Fallback for unexpected string value
                html_content += f"<p>{v}</p>"
                
            html_content += '</div></div>'

    html_content += '</body></html>'
    return html_content

# --- END NEW HELPER FUNCTION ---


# --- HELPER FUNCTIONS FOR FILE/TEXT PROCESSING ---

def clear_interview_state():
    """Clears all session state variables related to interview/match sessions."""
    if 'interview_chat_history' in st.session_state: del st.session_state['interview_chat_history']
    if 'current_interview_jd' in st.session_state: del st.session_state['current_interview_jd']
    if 'evaluation_report' in st.session_state: del st.session_state['evaluation_report']
    if 'candidate_match_results' in st.session_state: st.session_state.candidate_match_results = []
    
# Updated signature to match the request
def parse_and_store_resume(content_source, file_name_key, source_type):
    """Handles extraction, parsing, and storage of CV data from either a file or pasted text."""
    extracted_text = ""
    excel_data = None
    file_name = "Pasted_Resume"

    if source_type == 'file':
        uploaded_file = content_source
        file_name = uploaded_file.name
        file_type = get_file_type(file_name)
        uploaded_file.seek(0) 
        st.session_state.current_parsing_source_name = file_name 
        extracted_text, excel_data = extract_content(file_type, uploaded_file.getvalue(), file_name)
    elif source_type == 'text':
        extracted_text = content_source.strip()
        file_name = "Pasted_Text"
        st.session_state.current_parsing_source_name = file_name 

    if extracted_text.startswith("[Error"):
        return {"error": extracted_text, "full_text": extracted_text, "excel_data": None, "name": file_name}
    
    # 2. Call LLM Parser
    parsed_data = parse_resume_with_llm(extracted_text)
    
    # 3. Handle LLM Parsing Error
    if parsed_data.get('error') is not None: 
        error_name = parsed_data.get('name', file_name) 
        return {"error": parsed_data['error'], "full_text": extracted_text, "excel_data": excel_data, "name": error_name}

    # 4. Create compiled text for download/Q&A
    compiled_text = ""
    for k, v in parsed_data.items():
        if v and k not in ['error']:
            # FIX: Only display the section header if the content is not an empty string or empty list/dict
            
            # Check for empty string/list/dict
            if isinstance(v, str) and not v.strip(): continue
            if isinstance(v, list) and not v: continue
            if isinstance(v, dict) and not any(val for val in v.values()): continue # Fix for dicts like {'a':'', 'b':''}

            compiled_text += f"## {k.replace('_', ' ').title()}\n\n"
            
            if isinstance(v, list):
                compiled_text += "\n".join([f"* {item}" for item in v if item]) + "\n\n"
            elif isinstance(v, dict):
                 # FIX: Nicely format dictionary content
                dict_content = [f"- **{key.replace('_', ' ').title()}**: {value}" for key, value in v.items() if value]
                if dict_content:
                    compiled_text += "\n".join(dict_content) + "\n\n"
                else:
                    # Skip if the dictionary had valid keys but empty values
                    compiled_text = compiled_text.removesuffix(f"## {k.replace('_', ' ').title()}\n\n")
            else:
                compiled_text += str(v) + "\n\n"

    # Ensure final_name uses the parsed name
    final_name = parsed_data.get('name', 'Unknown_Candidate').replace(' ', '_') 
    
    return {
        "parsed": parsed_data, 
        "full_text": compiled_text, 
        "excel_data": excel_data, 
        "name": final_name
    }


def get_download_link(data, filename, file_format):
    """
    Generates a base64 encoded download link for the given data and format.
    """
    mime_type = "application/octet-stream"
    
    if file_format == 'json':
        data_bytes = data.encode('utf-8')
        mime_type = "application/json"
    elif file_format == 'markdown':
        data_bytes = data.encode('utf-8')
        mime_type = "text/markdown"
    elif file_format == 'html':
        # Now uses the new function to get the HTML content
        data_bytes = data.encode('utf-8')
        mime_type = "text/html"
    else:
        return "" 

    b64 = base64.b64encode(data_bytes).decode()
    
    # Return the full data URI
    return f"data:{mime_type};base64,{b64}"

def render_download_button(data_uri, filename, label, color):
    """Renders an HTML button that triggers a file download."""
    
    if color == 'json':
        bg_color = "#4CAF50" # Green
        icon = "💾"
    elif color == 'markdown':
        bg_color = "#008CBA" # Blue
        icon = "⬇️"
    elif color == 'html':
        bg_color = "#f44336" # Red
        icon = "📄"
    else:
        bg_color = "#555555"
        icon = ""
        
    st.markdown(
        f"""
        <a href="{data_uri}" download="{filename}" style="text-decoration: none;">
            <button style="
                background-color: {bg_color}; 
                color: white; 
                border: none; 
                padding: 10px 10px; 
                text-align: center; 
                text-decoration: none; 
                display: inline-block; 
                font-size: 14px; 
                margin: 4px 0; 
                cursor: pointer; 
                border-radius: 4px;
                width: 100%;">
                {icon} {label}
            </button>
        </a>
        """, 
        unsafe_allow_html=True
    )
# --- END HELPER FUNCTIONS ---


@st.cache_data(show_spinner="Analyzing JD for metadata...")
def extract_jd_metadata(jd_text):
    """Mocks the extraction of key metadata (Role, Skills, Job Type) from JD text using LLM."""
    if jd_text.startswith("[Error"):
        return {"role": "Error", "key_skills": ["Error"], "job_type": "Error"}
    
    # Simple heuristic mock
    role_match = re.search(r'(?:Role|Position|Title|Engineer|Scientist)[:\s\n]+([\w\s/-]+)', jd_text, re.IGNORECASE)
    role = role_match.group(1).strip() if role_match else "Software Engineer (Mock)"
    
    # Extract Skills from JD content - ENHANCED SKILL LIST
    skills_match = re.findall(r'(Python|Java|SQL|AWS|Docker|Kubernetes|React|Streamlit|Cloud|Data|ML|LLM|MLOps|Visualization|Deep Learning|TensorFlow|Pytorch)', jd_text, re.IGNORECASE)
    
    # Simple heuristic to improve role names if generic title is found
    if 'data scientist' in jd_text.lower() or 'machine learning' in jd_text.lower():
         role = "Data Scientist/ML Engineer"
    elif 'cloud engineer' in jd_text.lower() or 'aws' in jd_text.lower() or 'gcp' in jd_text.lower():
         role = "Cloud Engineer"
    
    job_type_match = re.search(r'(Full-time|Part-time|Contract|Remote|Hybrid)', jd_text, re.IGNORECASE)
    job_type = job_type_match.group(1) if job_type_match else "Full-time (Mock)"
    
    return {
        "role": role, 
        "key_skills": list(set([s.lower() for s in skills_match])), # Keep all unique skills found
        "job_type": job_type
    }

def extract_jd_from_linkedin_url(url):
    """Mocks the extraction of JD content from a LinkedIn URL."""
    if "linkedin.com/jobs" not in url:
        return f"[Error] Invalid LinkedIn Job URL: {url}"

    # Mock content based on URL structure
    url_lower = url.lower()
    
    if "data-scientist" in url_lower:
        role = "Data Scientist"
        skills = ["Python", "SQL", "ML", "Data Analysis", "Pytorch", "Visualization"]
        focus = "machine learning and statistical modeling"
        
    elif "cloud-engineer" in url_lower or "aws" in url_lower:
        role = "Cloud Engineer"
        skills = ["AWS", "Docker", "Kubernetes", "Cloud Services", "GCP", "Terraform"]
        focus = "infrastructure as code and cloud deployment"
        
    elif "ml-engineer" in url_lower or "ai-engineer" in url_lower:
        role = "AI/ML Engineer"
        skills = ["MLOps", "LLM", "Deep Learning", "Python", "TensorFlow", "API Services"]
        focus = "production-level AI/ML model development and deployment"
        
    else:
        role = "Software Engineer"
        skills = ["Java", "API", "SQL", "React", "JavaScript"]
        focus = "full-stack application development"
    
    skills_str = ", ".join(skills)

    return f"""
    --- Simulated JD for: {role} ---
    
    Company: MockCorp
    Location: Remote
    
    Job Summary:
    We are seeking a highly skilled **{role}** to join our team. The ideal candidate will have expertise in {skills_str}. Must be focused on **{focus}**. This is a Full-time position.
    
    Responsibilities:
    * Develop and maintain systems using **{skills[0]}** and **{skills[1]}** in a collaborative environment.
    * Manage and deploy applications on **{skills[2]}** platforms.
    * Collaborate with cross-functional teams.
    
    Qualifications:
    * 3+ years of experience.
    * Strong proficiency in **{skills[0]}** and analytical tools.
    * Experience with cloud platforms (e.g., AWS).
    ---
    """
    
# --- EVALUATE JD FIT FUNCTION (LLM-DEPENDENT) ---
@st.cache_data(show_spinner="Evaluating candidate fit with Groq LLM...")
def evaluate_jd_fit(job_description, parsed_json):
    """
    Evaluates how well a resume fits a given job description, 
    including section-wise scores, by calling the Groq LLM API.
    """
    # Use the client object, which can be the real Groq client or the MockGroqClient
    global client, GROQ_MODEL, GROQ_API_KEY
    
    if parsed_json.get('error') is not None: 
         # This message is now explicitly caught in the match_batch_tab to set the score to 'Cannot evaluate'
         return f"Cannot evaluate due to resume parsing errors: {parsed_json['error']}"

    if isinstance(client, MockGroqClient) and not GROQ_API_KEY:
         # In mock mode, use the special mock implementation for fit evaluation
         response = client.chat().create(model=GROQ_MODEL, messages=[{"role": "user", "content": f"Evaluate how well the following resume content matches the provided job description: {job_description}"}])
         return response.choices[0].message.content.strip()

    if not job_description.strip(): return "Please paste a job description."

    # Prepare data for LLM
    candidate_summary = json.dumps({
        "name": parsed_json.get('name'),
        "skills": parsed_json.get('skills'),
        "experience": parsed_json.get('experience'),
        "education": parsed_json.get('education')
    }, indent=2)

    # --- LLM PROMPT for Evaluation ---
    prompt = f"""
    You are an expert ATS (Applicant Tracking System) and HR evaluator. 
    Evaluate how well the following candidate's resume content matches the provided job description.
    
    Job Description:
    {job_description}
    
    Candidate Summary (Parsed Resume Data):
    {candidate_summary}
    
    Provide your analysis in the EXACT FORMAT specified below. Use scores from 1 to 10.
    
    Overall Fit Score: [Score]/10
    
    --- Section Match Analysis ---
    Skills Match: [Percentage]%
    Experience Match: [Percentage]%
    Education Match: [Percentage]%
    
    Strengths/Matches:
    - List 2-3 specific points where the candidate's background directly matches the JD requirements.
    
    Gaps/Areas for Improvement:
    - List 1-2 specific points where the candidate is lacking compared to the JD requirements.
    
    Overall Summary: A concise, one-paragraph summary of the candidate's fit.
    """
    # --- End LLM PROMPT ---

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error] LLM API Call Failed for Fit Evaluation: {e}"

# --- END EVALUATE JD FIT FUNCTION ---


# --- Q&A CHAT FUNCTION ---
def run_qa_chat(user_prompt, context_text, context_type, history):
    """Handles the back-and-forth Q&A interaction with the LLM."""
    global client, GROQ_MODEL, GROQ_API_KEY
    
    # 1. Determine System Prompt based on context
    if context_type == 'jd':
        sys_msg = "You are an expert HR analyst. Answer the following question about the Job Description concisely and directly. Do not use conversational filler. Your answer must be factual based ONLY on the provided JD text."
    else: # context_type == 'resume'
        sys_msg = "You are an expert talent scout. Answer the following question about the resume concisely and directly. Do not use conversational filler. Your answer must be factual based ONLY on the provided resume text/summary."

    # 2. Build the message history for the chat
    messages = [
        {"role": "system", "content": f"{sys_msg}\n\nContext:\n{context_text}"}
    ]
    
    for role, content in history:
        messages.append({"role": role, "content": content})
    
    # Add the current user question
    messages.append({"role": "user", "content": f"Question: {user_prompt}"})

    # 3. Call the LLM (or Mock)
    try:
        if isinstance(client, MockGroqClient):
            # Mock client has specific mock logic inside its 'create' method
            completion = client.chat().create(model=GROQ_MODEL, messages=[messages[-1]]) 
        else:
            completion = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                temperature=0.1
            )
        
        return completion.choices[0].message.content.strip()
    
    except Exception as e:
        return f"[Error] LLM API Call Failed for Q&A: {e}"

# --- END Q&A CHAT FUNCTION ---


# ==============================================================================
# --- STREAMLIT PAGE FUNCTIONS ---
# ==============================================================================

def init_session_state():
    """Initializes all necessary session state variables."""
    if 'page' not in st.session_state:
        st.session_state.page = 'parser' # Initial page is the Resume Parser
    if 'candidate_data' not in st.session_state:
        st.session_state.candidate_data = None # Stores the result of parse_and_store_resume
    if 'current_parsing_source_name' not in st.session_state:
        st.session_state.current_parsing_source_name = "Candidate Resume"
    if 'job_description_text' not in st.session_state:
        st.session_state.job_description_text = ""
    if 'candidate_match_results' not in st.session_state:
        st.session_state.candidate_match_results = []
    if 'evaluation_report' not in st.session_state:
        st.session_state.evaluation_report = ""
    if 'interview_chat_history' not in st.session_state:
        st.session_state.interview_chat_history = []
    if 'current_interview_jd' not in st.session_state:
        st.session_state.current_interview_jd = ""


def resume_parser_tab():
    """UI and logic for the Resume Parser tab."""
    st.header("1. 📄 Resume Parser")
    st.markdown("Upload a candidate's resume or paste the text to extract structured data using the **Groq LLM**.")
    
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Upload/Paste Resume")
        # File Uploader
        uploaded_file = st.file_uploader(
            "Upload PDF, DOCX, TXT, or JSON file", 
            type=['pdf', 'docx', 'txt', 'json'],
            key="file_uploader"
        )
        
        st.markdown("---")
        
        # Text Area for pasting content (e.g., from LinkedIn profile or simple text CV)
        pasted_text = st.text_area(
            "Or, paste resume text here",
            height=300,
            key="pasted_text_area",
            placeholder="Paste your resume text here (Name, Contact, Experience, Skills...)"
        )
        
        # Parse Button
        parse_button_label = f"✨ Parse Resume ({GROQ_MODEL})"
        if st.button(parse_button_label, use_container_width=True, key="parse_button"):
            
            # Reset existing states
            st.session_state.candidate_data = None
            st.session_state.evaluation_report = ""
            clear_interview_state()

            if uploaded_file:
                result = parse_and_store_resume(uploaded_file, "file_uploader", 'file')
                st.session_state.candidate_data = result
            elif pasted_text.strip():
                result = parse_and_store_resume(pasted_text, "pasted_text_area", 'text')
                st.session_state.candidate_data = result
            else:
                st.warning("Please upload a file or paste text to begin parsing.")
                
            # Rerun to update the display in the second column
            st.rerun() 

    with col2:
        st.subheader("Parsed Candidate Data")
        
        candidate_data = st.session_state.candidate_data
        
        if candidate_data is None:
            st.info("Upload or paste a resume on the left and click 'Parse Resume' to see the extracted data.")
        
        elif candidate_data.get('error'):
            st.error(f"❌ Parsing Error for {candidate_data.get('name', 'Unknown')}")
            st.caption(candidate_data['error'])
            with st.expander("Show Raw Extracted Text"):
                st.text(candidate_data['full_text'])
                
        else:
            name = candidate_data['parsed'].get('name', 'Candidate')
            st.success(f"✅ Successfully Parsed: **{name}**")
            
            # Display Key Information
            st.markdown(f"**Email:** {candidate_data['parsed'].get('email', 'N/A')}")
            st.markdown(f"**Phone:** {candidate_data['parsed'].get('phone', 'N/A')}")
            st.markdown(f"**Key Skills:** {', '.join(candidate_data['parsed'].get('skills', [])[:5])}...")
            
            st.markdown("---")
            
            # --- Download Buttons ---
            download_col1, download_col2, download_col3 = st.columns(3)
            
            # 1. Download Parsed JSON
            with download_col1:
                json_content = json.dumps(candidate_data['parsed'], indent=2)
                json_uri = get_download_link(json_content, f"{candidate_data['name']}_Parsed.json", 'json')
                render_download_button(json_uri, f"{candidate_data['name']}_Parsed.json", "Download JSON", 'json')

            # 2. Download Formatted Markdown
            with download_col2:
                md_uri = get_download_link(candidate_data['full_text'], f"{candidate_data['name']}_Formatted.md", 'markdown')
                render_download_button(md_uri, f"{candidate_data['name']}_Formatted.md", "Download Markdown", 'markdown')

            # 3. Generate Downloadable HTML/CV
            with download_col3:
                html_content = generate_cv_html(candidate_data['parsed'])
                html_uri = get_download_link(html_content, f"{candidate_data['name']}_CV.html", 'html')
                render_download_button(html_uri, f"{candidate_data['name']}_CV.html", "View/Print HTML CV", 'html')


            # --- Expanders for Detail View ---
            st.markdown("---")
            with st.expander("View Full Parsed Content", expanded=True):
                st.json(candidate_data['parsed'])

            with st.expander("View Raw Extracted Text"):
                st.text(candidate_data['full_text'])


def jd_matching_tab():
    """UI and logic for the Job Description Matching tab."""
    st.header("2. 🎯 Job Description Matcher")
    st.markdown("Compare the parsed candidate data against a specific Job Description to evaluate fit.")

    if st.session_state.candidate_data is None:
        st.warning("Please go to the **Resume Parser** tab first and successfully parse a candidate's resume.")
        return

    candidate_name = st.session_state.candidate_data.get('name', 'Candidate')
    st.info(f"Candidate Selected: **{candidate_name.replace('_', ' ')}**")
    
    # JD Input Section
    st.subheader("Input Job Description")
    
    jd_tab1, jd_tab2 = st.tabs(["Paste JD Text", "LinkedIn URL (Mock)"])

    with jd_tab1:
        jd_text = st.text_area(
            "Paste the full Job Description here (Role, Requirements, Qualifications, etc.)",
            value=st.session_state.job_description_text,
            height=300,
            key="jd_text_area",
            placeholder="Paste the Job Description text..."
        )
        if st.button("Save/Update JD Text", key="save_jd_button"):
            st.session_state.job_description_text = jd_text
            st.success("Job Description saved.")

    with jd_tab2:
        linkedin_url = st.text_input(
            "Paste LinkedIn Job URL to simulate JD extraction",
            key="linkedin_url_input",
            placeholder="e.g., https://www.linkedin.com/jobs/view/..."
        )
        if st.button("Simulate Extraction", key="simulate_jd_button"):
            mock_jd = extract_jd_from_linkedin_url(linkedin_url)
            st.session_state.job_description_text = mock_jd
            st.success(f"Simulated JD for **{linkedin_url}** loaded.")
            st.rerun() # Rerun to update text area value

    job_description = st.session_state.job_description_text
    
    st.markdown("---")
    
    # Match Evaluation Button
    if st.button("🚀 Evaluate Candidate Fit", use_container_width=True, key="evaluate_fit_button"):
        if not job_description.strip() or job_description.startswith("Please paste"):
            st.error("Please provide a Job Description before evaluating.")
            st.session_state.evaluation_report = ""
        else:
            # Clear previous evaluation before starting new one
            st.session_state.evaluation_report = ""
            
            with st.spinner(f"Running LLM evaluation of {candidate_name.replace('_', ' ')} against JD..."):
                report = evaluate_jd_fit(job_description, st.session_state.candidate_data['parsed'])
                st.session_state.evaluation_report = report
            
            if st.session_state.evaluation_report.startswith("[Error]"):
                st.error(st.session_state.evaluation_report)
            elif st.session_state.evaluation_report.startswith("Cannot evaluate"):
                st.error(st.session_state.evaluation_report)
            else:
                st.success("Fit evaluation complete!")

    # Evaluation Report Display
    if st.session_state.evaluation_report:
        st.subheader("Evaluation Report")
        report_text = st.session_state.evaluation_report

        # --- Report Parsing and Display ---
        if report_text.startswith("Cannot evaluate"):
            st.error(report_text)
            return
            
        # Regex to extract structured data
        overall_match = re.search(r'Overall Fit Score: (\d+)/10', report_text)
        skills_match = re.search(r'Skills Match: (\d+)%', report_text)
        exp_match = re.search(r'Experience Match: (\d+)%', report_text)
        edu_match = re.search(r'Education Match: (\d+)%', report_text)
        
        # Display Score Gauges
        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        
        overall_score = int(overall_match.group(1)) if overall_match else 5
        
        with col_g1:
            st.metric(label="Overall Fit Score", value=f"{overall_score}/10")
        with col_g2:
            st.metric(label="Skills Match", value=f"{skills_match.group(1)}%") if skills_match else st.markdown("**N/A**")
        with col_g3:
            st.metric(label="Experience Match", value=f"{exp_match.group(1)}%") if exp_match else st.markdown("**N/A**")
        with col_g4:
            st.metric(label="Education Match", value=f"{edu_match.group(1)}%") if edu_match else st.markdown("**N/A**")
            
        st.markdown("---")

        # Display Summary/Strengths/Gaps
        # Remove the score lines and section analysis to show the free text only
        
        # Use simple regex splits for the remaining content
        strengths_match = re.search(r'Strengths/Matches:\s*(.*?)(?:Gaps/Areas for Improvement:|$)', report_text, re.DOTALL)
        gaps_match = re.search(r'Gaps/Areas for Improvement:\s*(.*?)(?:Overall Summary:|$)', report_text, re.DOTALL)
        summary_match = re.search(r'Overall Summary:\s*(.*)', report_text, re.DOTALL)
        
        st.subheader("Detailed Analysis")
        
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.markdown("### Strengths/Matches 🟢")
            if strengths_match:
                st.markdown(strengths_match.group(1).strip().replace('\n', '<br>'), unsafe_allow_html=True)
            else:
                st.markdown("No specific strengths identified.")
                
        with col_s2:
            st.markdown("### Gaps/Areas for Improvement 🟠")
            if gaps_match:
                st.markdown(gaps_match.group(1).strip().replace('\n', '<br>'), unsafe_allow_html=True)
            else:
                st.markdown("No significant gaps identified.")
        
        st.markdown("---")
        st.markdown("### Overall Summary")
        if summary_match:
            st.write(summary_match.group(1).strip())
        
        with st.expander("View Full Raw LLM Report"):
            st.text(report_text)


def interview_qa_tab():
    """UI and logic for the Candidate Q&A/Mock Interview tab."""
    st.header("3. 💬 Q&A Interview Assistant")
    st.markdown("Ask natural language questions about the candidate's resume or the target Job Description.")

    # 1. Check for parsed data
    if st.session_state.candidate_data is None:
        st.warning("Please go to the **Resume Parser** tab first and successfully parse a candidate's resume.")
        return

    st.subheader(f"Q&A Session for: {st.session_state.candidate_data['name'].replace('_', ' ')}")
    
    # 2. Context Selection (Resume or JD)
    col_sel1, col_sel2 = st.columns(2)
    
    with col_sel1:
        context_type = st.radio(
            "Select Context Source:", 
            ('Resume (Candidate Data)', 'Job Description'), 
            key='qa_context_type',
            help="Choose whether you want to ask questions about the candidate's background or the job requirements."
        )

    with col_sel2:
        # JD Display/Warning
        if context_type == 'Job Description':
            if st.session_state.job_description_text.strip():
                jd_metadata = extract_jd_metadata(st.session_state.job_description_text)
                st.success(f"JD Context: **{jd_metadata['role']}**")
                context_text = st.session_state.job_description_text
            else:
                st.warning("No Job Description available. Go to **JD Matcher** to input one.")
                context_text = "No Job Description provided."
        else:
            st.success("Resume Context: Candidate Summary")
            context_text = st.session_state.candidate_data['full_text']
            

    # 3. Chat Interface
    chat_history = st.session_state.interview_chat_history
    
    # Display chat history
    st.markdown("---")
    chat_container = st.container(height=400)
    
    with chat_container:
        if not chat_history:
            st.info("Start the conversation by asking a question in the text box below.")
            
        for role, content in chat_history:
            with st.chat_message(role):
                st.markdown(content)

    # Chat Input
    user_prompt = st.chat_input("Ask a question about the candidate or the job...")

    if user_prompt and context_text.strip() != "No Job Description provided.":
        
        # 1. Display user message immediately
        with chat_container:
            with st.chat_message("user"):
                st.markdown(user_prompt)
        
        # 2. Add user message to history
        chat_history.append(("user", user_prompt))
        
        # 3. Get LLM response
        with st.spinner(f"Thinking with {GROQ_MODEL}..."):
            llm_response = run_qa_chat(
                user_prompt, 
                context_text, 
                'jd' if context_type == 'Job Description' else 'resume', 
                chat_history
            )

        # 4. Display LLM response
        with chat_container:
            with st.chat_message("assistant"):
                st.markdown(llm_response)

        # 5. Add LLM response to history
        chat_history.append(("assistant", llm_response))

        # IMPORTANT: Force a rerun to show the latest chat messages
        st.rerun() 
        

# ==============================================================================
# --- MAIN APPLICATION ENTRY POINT ---
# ==============================================================================

def main():
    """Main function to run the Streamlit Candidate Dashboard."""
    
    # Set Streamlit Page Configuration
    st.set_page_config(
        page_title="Candidate Dashboard",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Initialize Session State
    init_session_state()

    # --- Sidebar for Navigation ---
    with st.sidebar:
        st.title("🤖 Candidate Dashboard")
        st.markdown("---")
        
        # Navigation Buttons
        if st.button("📄 1. Resume Parser", use_container_width=True, key="nav_parser"):
            go_to('parser')
        
        if st.session_state.candidate_data and not st.session_state.candidate_data.get('error'):
            if st.button("🎯 2. JD Matcher", use_container_width=True, key="nav_matcher"):
                go_to('matcher')
            
            if st.button("💬 3. Q&A Interview", use_container_width=True, key="nav_qa"):
                go_to('qa')
        else:
            st.info("Complete step 1 to unlock other features.")
        
        st.markdown("---")
        
        # API Status Indicator
        if not GROQ_API_KEY:
            st.warning("⚠️ **Mock Client Active**\n(Groq API Key not found)")
        elif isinstance(client, MockGroqClient):
            st.warning("⚠️ **Mock Client Active**\n(Groq Import Failed)")
        else:
            st.success(f"✅ **Groq API Active**\nModel: {GROQ_MODEL}")

        # Clear Data Button
        if st.button("Clear All Data", use_container_width=True, key="clear_all"):
            st.session_state.candidate_data = None
            st.session_state.job_description_text = ""
            st.session_state.evaluation_report = ""
            clear_interview_state()
            go_to('parser')
            st.rerun()

    # --- Main Content Area ---

    # Display content based on the current page state
    if st.session_state.page == 'parser':
        resume_parser_tab()
    elif st.session_state.page == 'matcher':
        jd_matching_tab()
    elif st.session_state.page == 'qa':
        interview_qa_tab()

if __name__ == "__main__":
    main()
