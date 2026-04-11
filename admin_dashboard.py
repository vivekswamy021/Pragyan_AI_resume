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
                    raise ValueError("GROQ_API_KEY not set. AI functions disabled.")
            return Completions()
    client = MockGroqClient()
else:
    client = Groq(api_key=GROQ_API_KEY)

# --- Utility Functions ---

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
    """Extracts text content from various file types."""
    text = ''
    try:
        if file_type == 'pdf':
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + '\n'
        elif file_type == 'docx':
            doc = docx.Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
        elif file_type == 'xlsx':
            workbook = openpyxl.load_workbook(file_path)
            for sheet in workbook.sheetnames:
                ws = workbook[sheet]
                for row in ws.iter_rows(values_only=True):
                    row_text = ' | '.join([str(c) for c in row if c is not None])
                    if row_text.strip():
                        text += row_text + '\n'
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        return text if text.strip() else f"Error: {file_type.upper()} content extraction failed."
    except Exception as e:
        return f"Fatal Extraction Error: {e}"

@st.cache_data(show_spinner="Extracting JD metadata...")
def extract_jd_metadata(jd_text):
    if not GROQ_API_KEY:
        return {"role": "N/A", "job_type": "N/A", "key_skills": []}

    prompt = f"""Analyze the following Job Description and extract:
    1. role, 2. job_type, 3. key_skills (list). Output strictly as JSON.
    JD: {jd_text}"""
    
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            return {
                "role": parsed.get("role", "General Analyst"),
                "job_type": parsed.get("job_type", "Full-time"),
                "key_skills": parsed.get("key_skills", [])
            }
    except:
        pass
    return {"role": "General Analyst", "job_type": "Full-time", "key_skills": []}

@st.cache_data(show_spinner="Analyzing content...")
def parse_with_llm(text, return_type='json'):
    if not GROQ_API_KEY: return {"error": "API key missing"}

    prompt = f"Extract Name, Email, Phone, Skills, Education (as list), Experience, Summary from this resume text in JSON format: {text}"
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        return {"error": str(e)}
    return {"error": "Failed to parse JSON"}

def evaluate_jd_fit(job_description, parsed_json):
    if not GROQ_API_KEY: return "AI Evaluation Disabled."
    prompt = f"Match this resume JSON: {json.dumps(parsed_json)} against this JD: {job_description}. Provide Overall Fit Score: X/10 and Section Match Analysis."
    response = client.chat.completions.create(
        model=GROQ_MODEL, 
        messages=[{"role": "user", "content": prompt}], 
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def extract_jd_from_linkedin_url(url: str) -> str:
    return f"Simulated JD content for {url}"

def update_resume_metadata(resume_name, new_status, applied_jd, submitted_date, resume_list_index):
    st.session_state.resume_statuses[resume_name] = new_status
    if 0 <= resume_list_index < len(st.session_state.resumes_to_analyze):
        st.session_state.resumes_to_analyze[resume_list_index]['applied_jd'] = applied_jd
        st.session_state.resumes_to_analyze[resume_list_index]['submitted_date'] = submitted_date
        st.toast(f"Updated **{resume_name}**")

def parse_and_store_resume(file_input, file_name_key='default', source_type='file'):
    text = ""
    file_name = ""
    if source_type == 'file':
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file_input.name) 
        with open(temp_path, "wb") as f:
            f.write(file_input.getbuffer()) 
        text = extract_content(get_file_type(temp_path), temp_path)
        file_name = file_input.name
    
    parsed = parse_with_llm(text)
    return {"parsed": parsed, "full_text": text, "name": parsed.get('name', file_name)}

# --- UI Components ---

def candidate_approval_tab_content():
    st.header("👤 Candidate Approval")
    if "resumes_to_analyze" not in st.session_state or not st.session_state.resumes_to_analyze:
        st.info("No resumes uploaded.")
        return

    jd_options = ["Select JD"] + [item['name'] for item in st.session_state.admin_jd_list]

    for idx, resume_data in enumerate(st.session_state.resumes_to_analyze):
        resume_name = resume_data['name']
        current_status = st.session_state.resume_statuses.get(resume_name, "Pending")
        parsed_data = resume_data.get('parsed', {})
        
        # --- FIXED LOGIC HERE ---
        education_data = parsed_data.get('education', [])
        if isinstance(education_data, list) and len(education_data) > 0:
            university_info = str(education_data[0])
        elif isinstance(education_data, str) and education_data.strip():
            university_info = education_data
        else:
            university_info = "N/A"
        
        if len(university_info) > 60: university_info = university_info[:57] + "..."

        with st.container(border=True):
            st.subheader(f"{resume_name} ({current_status})")
            col1, col2 = st.columns(2)
            col1.write(f"**Email:** {parsed_data.get('email', 'N/A')}")
            col2.write(f"**Education:** {university_info}")
            
            sel_jd = st.selectbox("Assign JD", jd_options, key=f"jd_{idx}")
            
            c1, c2, c3 = st.columns(3)
            if c1.button("✅ Approve", key=f"app_{idx}"):
                update_resume_metadata(resume_name, "Approved", sel_jd, str(date.today()), idx)
                st.rerun()
            if c2.button("❌ Reject", key=f"rej_{idx}"):
                update_resume_metadata(resume_name, "Rejected", sel_jd, str(date.today()), idx)
                st.rerun()
            if c3.button("🟡 Pending", key=f"pen_{idx}"):
                update_resume_metadata(resume_name, "Pending", sel_jd, str(date.today()), idx)
                st.rerun()

def vendor_approval_tab_content():
    st.header("🤝 Vendor Approval")
    # Simplified for brevity; similar form logic as candidate
    st.write("Vendor management logic goes here.")

def admin_dashboard(go_to_func): 
    st.title("🧑‍💼 Admin Dashboard")
    if st.button("🚪 Log Out"):
        st.session_state.logged_in = False
        go_to_func("login")
        st.rerun()

    t1, t2, t3, t4 = st.tabs(["📄 JD Management", "📊 Resume Analysis", "🛠️ User Management", "📈 Statistics"])
    
    with t1:
        st.write("JD Management Logic")
    with t2:
        # Resume Analysis Logic (uploading and parsing)
        uploaded = st.file_uploader("Upload Resumes", accept_multiple_files=True)
        if st.button("Process"):
            for f in uploaded:
                res = parse_and_store_resume(f)
                st.session_state.resumes_to_analyze.append(res)
                st.session_state.resume_statuses[res['name']] = "Pending"
            st.rerun()
    with t3:
        sub1, sub2 = st.tabs(["Candidates", "Vendors"])
        with sub1: candidate_approval_tab_content()
        with sub2: vendor_approval_tab_content()
    with t4:
        st.metric("Total Resumes", len(st.session_state.resumes_to_analyze))

if __name__ == '__main__':
    st.set_page_config(layout="wide")
    if 'page' not in st.session_state: st.session_state.page = "admin_dashboard"
    if 'resumes_to_analyze' not in st.session_state: st.session_state.resumes_to_analyze = []
    if 'resume_statuses' not in st.session_state: st.session_state.resume_statuses = {}
    if 'admin_jd_list' not in st.session_state: st.session_state.admin_jd_list = []
    if 'vendors' not in st.session_state: st.session_state.vendors = []
    if 'vendor_statuses' not in st.session_state: st.session_state.vendor_statuses = {}

    if st.session_state.page == "admin_dashboard":
        admin_dashboard(go_to)
    else:
        st.button("Back to Dashboard", on_click=lambda: go_to("admin_dashboard"))
