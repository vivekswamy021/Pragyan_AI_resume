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
        @property
        def completions(self):
            return self.chat()
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

    prompt = f"Analyze this JD and extract role, job_type, and key_skills in JSON: {jd_text}"
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except:
        pass
    return {"role": "General Analyst", "job_type": "Full-time", "key_skills": []}

@st.cache_data(show_spinner="Analyzing content with Groq LLM...")
def parse_with_llm(text, return_type='json'):
    if not GROQ_API_KEY: return {"error": "API key missing"}

    prompt = f"Extract Name, Email, Phone, Skills, Education (as list), Experience, and Summary from this resume in JSON: {text}"
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
    return {"error": "JSON isolation failed"}

def evaluate_jd_fit(job_description, parsed_json):
    if not GROQ_API_KEY: return "AI Evaluation Disabled."
    prompt = f"Evaluate fit between JD: {job_description} and Resume: {json.dumps(parsed_json)}"
    response = client.chat.completions.create(
        model=GROQ_MODEL, 
        messages=[{"role": "user", "content": prompt}], 
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def update_resume_metadata(resume_name, new_status, applied_jd, submitted_date, resume_list_index):
    st.session_state.resume_statuses[resume_name] = new_status
    if 0 <= resume_list_index < len(st.session_state.resumes_to_analyze):
        st.session_state.resumes_to_analyze[resume_list_index]['applied_jd'] = applied_jd
        st.session_state.resumes_to_analyze[resume_list_index]['submitted_date'] = submitted_date
        st.toast(f"Status for **{resume_name}** updated.")

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
    return {"parsed": parsed, "full_text": text, "name": parsed.get('name', file_name) if isinstance(parsed, dict) else file_name}

# --- Approval Tab Content Functions ---

def candidate_approval_tab_content():
    st.header("👤 Candidate Approval")
    if "resumes_to_analyze" not in st.session_state or not st.session_state.resumes_to_analyze:
        st.info("No resumes available.")
        return

    jd_options = ["Select JD"] + [item['name'] for item in st.session_state.admin_jd_list]

    for idx, resume_data in enumerate(st.session_state.resumes_to_analyze):
        resume_name = resume_data['name']
        current_status = st.session_state.resume_statuses.get(resume_name, "Pending")
        parsed_data = resume_data.get('parsed', {})
        
        # --- FIX FOR KEYERROR: 0 ---
        education_list = parsed_data.get('education', [])
        university_info = "N/A"
        
        if isinstance(education_list, list) and len(education_list) > 0:
            university_info = str(education_list[0])
        elif isinstance(education_list, str) and education_list.strip():
            university_info = education_list
            
        if len(university_info) > 60: university_info = university_info[:57] + "..."

        with st.container(border=True):
            st.markdown(### **Candidate:** {resume_name})
            col_contact, col_education = st.columns(2)
            with col_contact:
                st.write(f"**📧 Email:** {parsed_data.get('email', 'N/A')}")
                st.write(f"**📱 Phone:** {parsed_data.get('phone', 'N/A')}")
            with col_education:
                st.write(f"**🎓 Education:** {university_info}")
                st.write(f"**Status:** {current_status}")
            
            sel_jd = st.selectbox("Assign JD", jd_options, key=f"jd_sel_{idx}")
            
            # Action Buttons
            b1, b2, b3 = st.columns(3)
            if b1.button("✅ Approve", key=f"app_{idx}"):
                update_resume_metadata(resume_name, "Approved", sel_jd, str(date.today()), idx)
                st.rerun()
            if b2.button("❌ Reject", key=f"rej_{idx}"):
                update_resume_metadata(resume_name, "Rejected", sel_jd, str(date.today()), idx)
                st.rerun()
            if b3.button("🟡 Pending", key=f"pen_{idx}"):
                update_resume_metadata(resume_name, "Pending", sel_jd, str(date.today()), idx)
                st.rerun()

def vendor_approval_tab_content():
    st.header("🤝 Vendor Approval")
    st.write("Vendor management dashboard.")

def admin_dashboard(go_to_func): 
    st.title("🧑‍💼 Admin Dashboard")
    st.caption(f"Logged in as: **{st.session_state.get('user_type', 'Admin')}**")

    if st.button("Log Out"):
        st.session_state.logged_in = False
        go_to_func("login")
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📄 JD Management", "📊 Resume Analysis", "🛠️ User Management", "📈 Statistics"])
    
    with tab1:
        st.subheader("Manage Job Descriptions")
        # Simplified JD logic
        if st.button("Add Sample JD"):
            st.session_state.admin_jd_list.append({"name": "Data Engineer", "content": "Python, SQL, AWS", "role": "Engineer"})
            st.rerun()

    with tab2:
        st.subheader("Resume Processing")
        uploaded = st.file_uploader("Upload Resumes", accept_multiple_files=True)
        if st.button("Parse Resumes"):
            if uploaded:
                for f in uploaded:
                    result = parse_and_store_resume(f)
                    st.session_state.resumes_to_analyze.append(result)
                    st.session_state.resume_statuses[result['name']] = "Pending"
                st.success("Parsed successfully!")
                st.rerun()

    with tab3:
        c_tab, v_tab = st.tabs(["Candidate Approval", "Vendor Approval"])
        with c_tab: candidate_approval_tab_content()
        with v_tab: vendor_approval_tab_content()

    with tab4:
        st.metric("Total Candidates", len(st.session_state.resumes_to_analyze))
        st.metric("Total JDs", len(st.session_state.admin_jd_list))

# --- Main Entry Point ---
if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="PragyanAI Admin")
    
    # Session State Init
    if 'page' not in st.session_state: st.session_state.page = "admin_dashboard"
    if 'admin_jd_list' not in st.session_state: st.session_state.admin_jd_list = []
    if 'resumes_to_analyze' not in st.session_state: st.session_state.resumes_to_analyze = []
    if 'resume_statuses' not in st.session_state: st.session_state.resume_statuses = {}
    if 'vendors' not in st.session_state: st.session_state.vendors = []
    if 'vendor_statuses' not in st.session_state: st.session_state.vendor_statuses = {}

    if st.session_state.page == "admin_dashboard":
        admin_dashboard(go_to)
    else:
        st.info("Please log in.")
