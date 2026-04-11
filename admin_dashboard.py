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

# -------------------------
# UTILITY FUNCTIONS
# -------------------------

def go_to(page_name):
    st.session_state.page = page_name

def get_file_type(file_path):
    ext = os.path.splitext(file_path)[1].lower().strip('.')
    if ext == 'pdf': return 'pdf'
    elif ext == 'docx': return 'docx'
    elif ext == 'xlsx': return 'xlsx'
    else: return 'txt' 

def extract_content(file_type, file_path):
    text = ''
    try:
        if file_type == 'pdf':
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text: text += page_text + '\n'
        elif file_type == 'docx':
            doc = docx.Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
        elif file_type == 'xlsx':
            workbook = openpyxl.load_workbook(file_path)
            for sheet in workbook.sheetnames:
                ws = workbook[sheet]
                for row in ws.iter_rows(values_only=True):
                    row_text = ' | '.join([str(c) for c in row if c is not None])
                    if row_text.strip(): text += row_text + '\n'
        else:
             with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        return text if text.strip() else "Error: Content extraction failed."
    except Exception as e:
        return f"Fatal Extraction Error: {e}"

@st.cache_data(show_spinner="Extracting metadata...")
def extract_jd_metadata(jd_text):
    if not GROQ_API_KEY: return {"role": "N/A", "job_type": "N/A", "key_skills": []}
    prompt = f"Analyze this JD and return JSON with keys: role, job_type, key_skills:\n{jd_text}"
    try:
        response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.0)
        content = response.choices[0].message.content.strip()
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        parsed = json.loads(json_match.group(0)) if json_match else {}
        return {"role": parsed.get("role", "N/A"), "job_type": parsed.get("job_type", "N/A"), "key_skills": parsed.get("key_skills", [])}
    except: return {"role": "N/A", "job_type": "N/A", "key_skills": []}

@st.cache_data(show_spinner="Parsing Resume...")
def parse_with_llm(text):
    if not GROQ_API_KEY: return {"error": "API Key missing"}
    prompt = f"Extract information from this resume into JSON (Name, Email, Phone, Skills, Education, Experience, summary):\n{text}"
    try:
        response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.2)
        json_match = re.search(r'\{.*\}', response.choices[0].message.content, re.DOTALL)
        return json.loads(json_match.group(0)) if json_match else {"error": "Failed to isolate JSON"}
    except Exception as e: return {"error": str(e)}

def evaluate_jd_fit(job_description, parsed_json):
    if not GROQ_API_KEY: return "AI disabled."
    prompt = f"Evaluate resume fit for JD. Return Fit Score/10 and Section analysis:\nJD: {job_description}\nResume: {json.dumps(parsed_json)}"
    response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.3)
    return response.choices[0].message.content.strip()

def parse_and_store_resume(file_input):
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file_input.name) 
    with open(temp_path, "wb") as f: f.write(file_input.getbuffer()) 
    file_type = get_file_type(temp_path)
    text = extract_content(file_type, temp_path)
    parsed = parse_with_llm(text)
    return {"parsed": parsed, "name": parsed.get('name', file_input.name.split('.')[0])}

def extract_jd_from_linkedin_url(url):
    return f"Simulated JD content for {url}. Requirements: Python, SQL, 3 years exp."

# -------------------------
# ADMIN DASHBOARD TABS
# -------------------------

def candidate_approval_tab():
    st.header("👤 Candidate Approval")
    if not st.session_state.resumes_to_analyze:
        st.info("No resumes uploaded yet.")
        return

    for idx, resume_data in enumerate(st.session_state.resumes_to_analyze):
        name = resume_data['name']
        parsed = resume_data.get('parsed', {})
        status = st.session_state.resume_statuses.get(name, "Pending")
        
        with st.container(border=True):
            st.subheader(f"Candidate: {name}")
            col1, col2 = st.columns(2)
            col1.markdown(f"**📧 Email:** {parsed.get('email', 'N/A')}\n\n**📱 Phone:** {parsed.get('phone', 'N/A')}")
            edu = parsed.get('education', ['N/A'])[0] if isinstance(parsed.get('education'), list) else parsed.get('education', 'N/A')
            col2.markdown(f"**🎓 University:** {edu}\n\n**Brief Info:** {parsed.get('summary', 'No summary available.')}")
            
            c1, c2, c3, _ = st.columns([1,1,1,4])
            if c1.button("✅ Approve", key=f"app_{idx}"):
                st.session_state.resume_statuses[name] = "Approved"
                st.rerun()
            if c2.button("❌ Reject", key=f"rej_{idx}"):
                st.session_state.resume_statuses[name] = "Rejected"
                st.rerun()
            if c3.button("🟡 Pending", key=f"pen_{idx}"):
                st.session_state.resume_statuses[name] = "Pending"
                st.rerun()

def vendor_approval_tab():
    st.header("🤝 Vendor Approval")
    with st.form("add_vendor_form", clear_on_submit=True):
        st.markdown("#### Vendor Company Details")
        col1, col2 = st.columns(2)
        v_name = col1.text_input("Vendor Company Name")
        v_domain = col2.text_input("Service / Domain Name")
        v_code = st.text_input("Vendor ID / Code")
        st.markdown("#### Contact Details")
        c3, c4, c5 = st.columns(3)
        v_person = c3.text_input("Contact Person")
        v_email = c4.text_input("Email ID")
        v_phone = c5.text_input("Contact Number")
        v_addr = st.text_area("Company Address")
        if st.form_submit_button("Add Vendor"):
            if v_name and v_email:
                st.session_state.vendors.append({'name': v_name, 'domain': v_domain, 'code': v_code, 'person': v_person, 'email': v_email, 'phone': v_phone, 'addr': v_addr})
                st.session_state.vendor_statuses[v_name] = "Pending"
                st.success(f"Vendor {v_name} added!")
                st.rerun()

    st.markdown("---")
    st.subheader("2. Update Existing Vendor Status")
    for idx, v in enumerate(st.session_state.vendors):
        with st.container(border=True):
            st.write(f"**{v['name']}** ({v['code']}) | Person: {v['person']} | Email: {v['email']}")
            new_status = st.selectbox("Status", ["Pending", "Approved", "Rejected"], index=["Pending", "Approved", "Rejected"].index(st.session_state.vendor_statuses[v['name']]), key=f"vstat_{idx}")
            if st.button("Update Status", key=f"vup_{idx}"):
                st.session_state.vendor_statuses[v['name']] = new_status
                st.rerun()

def statistics_tab():
    st.header("📈 System Statistics")
    
    # Candidate Breakdown
    st.subheader("Candidate Breakdown")
    c_stats = st.session_state.resume_statuses.values()
    c1, c2, c3 = st.columns(3)
    c1.metric("Pending Candidates", list(c_stats).count("Pending"))
    c2.metric("Approved Candidates", list(c_stats).count("Approved"))
    c3.metric("Rejected Candidates", list(c_stats).count("Rejected"))
    
    st.markdown("---")
    
    # Vendor Breakdown
    st.subheader("Vendor Breakdown")
    v_stats = st.session_state.vendor_statuses.values()
    v1, v2, v3 = st.columns(3)
    v1.metric("Pending Vendors", list(v_stats).count("Pending"))
    v2.metric("Approved Vendors", list(v_stats).count("Approved"))
    v3.metric("Rejected Vendors", list(v_stats).count("Rejected"))

def admin_dashboard():
    st.title("🧑‍💼 Admin Dashboard")
    if st.button("🚪 Log Out"): go_to("login")
    
    t1, t2, t3, t4 = st.tabs(["📄 JD Management", "📊 Resume Analysis", "🛠️ User Management", "📈 Statistics"])
    
    with t1:
        # Simplified JD Management
        jd_text = st.text_area("Paste JD here")
        if st.button("Add JD"):
            st.session_state.admin_jd_list.append({"name": f"JD {len(st.session_state.admin_jd_list)+1}", "content": jd_text})
            st.success("JD Added")

    with t2:
        up_files = st.file_uploader("Upload Resumes", accept_multiple_files=True)
        if st.button("Parse Resumes"):
            for f in up_files:
                res = parse_and_store_resume(f)
                st.session_state.resumes_to_analyze.append(res)
                st.session_state.resume_statuses[res['name']] = "Pending"
            st.success("Parsed successfully")

    with t3:
        sub1, sub2 = st.tabs(["Candidate Approval", "Vendor Approval"])
        with sub1: candidate_approval_tab()
        with sub2: vendor_approval_tab()

    with t4:
        statistics_tab()

# -------------------------
# MAIN INITIALIZATION
# -------------------------

if __name__ == '__main__':
    st.set_page_config(layout="wide")
    if 'page' not in st.session_state: st.session_state.page = "admin_dashboard"
    if 'admin_jd_list' not in st.session_state: st.session_state.admin_jd_list = []
    if 'resumes_to_analyze' not in st.session_state: st.session_state.resumes_to_analyze = []
    if 'resume_statuses' not in st.session_state: st.session_state.resume_statuses = {}
    if 'vendors' not in st.session_state: st.session_state.vendors = []
    if 'vendor_statuses' not in st.session_state: st.session_state.vendor_statuses = {}
    
    if st.session_state.page == "admin_dashboard": admin_dashboard()
    else: st.info("Logged out.")
