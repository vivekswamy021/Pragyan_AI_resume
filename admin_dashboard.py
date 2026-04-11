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
import csv 
from streamlit.runtime.uploaded_file_manager import UploadedFile

# -------------------------
# CONFIGURATION & API SETUP
# -------------------------

GROQ_MODEL = "llama-3.1-8b-instant"

load_dotenv()
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

if not GROQ_API_KEY:
    st.warning("🚨 WARNING: GROQ_API_KEY not set. AI functionality will not work.")
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
# CORE UTILITY FUNCTIONS
# -------------------------

def go_to(page_name):
    st.session_state.page = page_name

def get_file_type(file_path):
    ext = os.path.splitext(file_path)[1].lower().strip('.')
    return ext if ext in ['pdf', 'docx', 'xlsx'] else 'txt'

def extract_content(file_type, file_path):
    text = ''
    try:
        if file_type == 'pdf':
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + '\n'
        elif file_type == 'docx':
            doc = docx.Document(file_path)
            text = '\n'.join([p.text for p in doc.paragraphs])
        elif file_type == 'xlsx':
            workbook = openpyxl.load_workbook(file_path)
            for sheet in workbook.sheetnames:
                ws = workbook[sheet]
                for row in ws.iter_rows(values_only=True):
                    text += ' | '.join([str(c) for c in row if c is not None]) + '\n'
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        return text if text.strip() else "Error: Content extraction failed."
    except Exception as e:
        return f"Fatal Extraction Error: {e}"

@st.cache_data(show_spinner="Extracting JD metadata...")
def extract_jd_metadata(jd_text):
    prompt = f"Extract metadata from this JD: {jd_text}. Output strictly JSON with keys: role, job_type, key_skills."
    try:
        response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.0)
        json_match = re.search(r'\{.*\}', response.choices[0].message.content.strip(), re.DOTALL)
        parsed = json.loads(json_match.group(0))
        return {
            "role": parsed.get("role", "General Analyst"),
            "job_type": parsed.get("job_type", "Full-time"),
            "key_skills": parsed.get("key_skills", [])
        }
    except:
        return {"role": "N/A", "job_type": "N/A", "key_skills": []}

@st.cache_data(show_spinner="Parsing Resume with LLM...")
def parse_with_llm(text):
    prompt = f"""Extract information from this resume into JSON. 
    Keys: name, email, phone, skills, education, experience, summary (3-4 sentences max).
    Resume: {text}"""
    try:
        response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.2)
        json_match = re.search(r'\{.*\}', response.choices[0].message.content.strip(), re.DOTALL)
        return json.loads(json_match.group(0))
    except Exception as e:
        return {"error": str(e)}

def evaluate_jd_fit(jd_text, parsed_json):
    prompt = f"Evaluate fit between JD: {jd_text} and Resume: {json.dumps(parsed_json)}. Output Overall Fit Score: X/10 and section analysis."
    response = client.chat.completions.create(model=GROQ_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0.3)
    return response.choices[0].message.content.strip()

def parse_and_store_resume(file_input):
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, file_input.name)
    with open(temp_path, "wb") as f:
        f.write(file_input.getbuffer())
    
    file_type = get_file_type(temp_path)
    text = extract_content(file_type, temp_path)
    parsed = parse_with_llm(text)
    
    return {"parsed": parsed, "full_text": text, "name": parsed.get('name', file_input.name)}

def update_resume_metadata(resume_name, status, applied_jd, date_str, index):
    st.session_state.resume_statuses[resume_name] = status
    st.session_state.resumes_to_analyze[index]['applied_jd'] = applied_jd
    st.session_state.resumes_to_analyze[index]['submitted_date'] = date_str
    st.toast(f"Updated {resume_name} to {status}")

# -------------------------
# ADMIN DASHBOARD TABS
# -------------------------

def candidate_approval_tab():
    st.header("👤 Candidate Approval")
    if not st.session_state.resumes_to_analyze:
        st.info("No resumes uploaded for analysis yet.")
        return

    jd_options = ["Select JD"] + [j['name'] for j in st.session_state.admin_jd_list]

    for idx, resume in enumerate(st.session_state.resumes_to_analyze):
        data = resume['parsed']
        res_name = resume['name']
        current_status = st.session_state.resume_statuses.get(res_name, "Pending")

        with st.container(border=True):
            st.markdown(f"### Candidate: {res_name}")
            c1, c2 = st.columns(2)
            c1.write(f"📧 **Email:** {data.get('email', 'N/A')}")
            c1.write(f"📱 **Phone:** {data.get('phone', 'N/A')}")
            c2.write(f"🎓 **University:** {data.get('education', ['N/A'])[0]}")
            c2.write(f"📋 **Current Status:** `{current_status}`")
            
            st.write(f"**Brief Info:** {data.get('summary', 'No summary available.')}")
            
            sel_jd = st.selectbox("Assign JD", jd_options, key=f"jd_{idx}")
            sel_date = st.date_input("Submission Date", value=date.today(), key=f"date_{idx}")
            
            b1, b2, b3, _ = st.columns([1, 1, 1, 5])
            if b1.button("✅ Approve", key=f"app_{idx}"):
                update_resume_metadata(res_name, "Approved", sel_jd, str(sel_date), idx)
                st.rerun()
            if b2.button("❌ Reject", key=f"rej_{idx}"):
                update_resume_metadata(res_name, "Rejected", sel_jd, str(sel_date), idx)
                st.rerun()
            if b3.button("🟡 Pending", key=f"pen_{idx}"):
                update_resume_metadata(res_name, "Pending", sel_jd, str(sel_date), idx)
                st.rerun()

def vendor_approval_tab():
    st.header("🤝 Vendor Approval")
    with st.form("add_vendor", clear_on_submit=True):
        v_name = st.text_input("Vendor Company Name")
        v_person = st.text_input("Contact Person")
        v_email = st.text_input("Email ID")
        v_phone = st.text_input("Contact Number")
        v_addr = st.text_area("Company Address")
        v_code = st.text_input("Vendor ID / Code")
        v_status = st.selectbox("Initial Status", ["Pending Review", "Approved", "Rejected"])
        if st.form_submit_button("Add Vendor"):
            if v_name and v_email:
                st.session_state.vendors.append({
                    "name": v_name, "person": v_person, "email": v_email, 
                    "phone": v_phone, "address": v_addr, "code": v_code
                })
                st.session_state.vendor_statuses[v_name] = v_status
                st.success("Vendor Added!")
                st.rerun()

    st.markdown("### Update Existing Vendors")
    for idx, v in enumerate(st.session_state.vendors):
        with st.container(border=True):
            st.write(f"**{v['name']}** ({v['code']}) - Status: {st.session_state.vendor_statuses[v['name']]}")
            new_v_status = st.selectbox("Change Status", ["Pending Review", "Approved", "Rejected"], key=f"vstat_{idx}")
            if st.button("Update Status", key=f"vbtn_{idx}"):
                st.session_state.vendor_statuses[v['name']] = new_v_status
                st.rerun()

def statistics_tab():
    st.header("📈 System Statistics")
    
    # Candidate Stats
    st.subheader("Candidate Status Breakdown")
    c_pending = list(st.session_state.resume_statuses.values()).count("Pending")
    c_rejected = list(st.session_state.resume_statuses.values()).count("Rejected")
    c_approved = list(st.session_state.resume_statuses.values()).count("Approved")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Candidates Pending", c_pending)
    col2.metric("Candidates Rejected", c_rejected)
    col3.metric("Candidates Approved", c_approved)
    
    st.divider()
    
    # Vendor Stats
    st.subheader("Vendor Status Breakdown")
    v_pending = list(st.session_state.vendor_statuses.values()).count("Pending Review")
    v_approved = list(st.session_state.vendor_statuses.values()).count("Approved")
    v_rejected = list(st.session_state.vendor_statuses.values()).count("Rejected")
    
    vcol1, vcol2, vcol3 = st.columns(3)
    vcol1.metric("Vendors Pending", v_pending)
    vcol2.metric("Vendors Approved", v_approved)
    vcol3.metric("Vendors Rejected", v_rejected)

# -------------------------
# MAIN ADMIN DASHBOARD
# -------------------------

def admin_dashboard():
    st.title("🧑‍💼 Admin Dashboard")
    
    if st.button("🚪 Log Out"):
        go_to("login")
        st.rerun()

    # Initialization
    if 'admin_jd_list' not in st.session_state: st.session_state.admin_jd_list = []
    if 'resumes_to_analyze' not in st.session_state: st.session_state.resumes_to_analyze = []
    if 'resume_statuses' not in st.session_state: st.session_state.resume_statuses = {}
    if 'vendors' not in st.session_state: st.session_state.vendors = []
    if 'vendor_statuses' not in st.session_state: st.session_state.vendor_statuses = {}

    tabs = st.tabs(["📄 JD Management", "📊 Resume Analysis", "🛠️ User Management", "📈 Statistics"])
    
    with tabs[0]:
        st.header("JD Management")
        jd_text = st.text_area("Paste JD Text")
        jd_name = st.text_input("JD Title")
        if st.button("Add JD"):
            meta = extract_jd_metadata(jd_text)
            st.session_state.admin_jd_list.append({"name": jd_name, "content": jd_text, **meta})
            st.success("JD Added!")

    with tabs[1]:
        st.header("Resume Analysis")
        files = st.file_uploader("Upload Resumes", accept_multiple_files=True)
        if st.button("Process Resumes"):
            for f in files:
                res = parse_and_store_resume(f)
                st.session_state.resumes_to_analyze.append(res)
                st.session_state.resume_statuses[res['name']] = "Pending"
            st.success("Resumes Processed!")

    with tabs[2]:
        sub1, sub2 = st.tabs(["Candidates", "Vendors"])
        with sub1: candidate_approval_tab()
        with sub2: vendor_approval_tab()

    with tabs[3]:
        statistics_tab()

# --- Entry Point ---
if __name__ == "__main__":
    if 'page' not in st.session_state: st.session_state.page = "admin_dashboard"
    if st.session_state.page == "admin_dashboard":
        admin_dashboard()
