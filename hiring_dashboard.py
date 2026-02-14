import streamlit as st
import pandas as pd
import numpy as np
import time
import base64
import random
from groq import Groq

# --- Configuration & Initialization ---
st.set_page_config(layout="wide", page_title="Talent Management System")

# Initialize session state for authentication and role
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'role' not in st.session_state:
    st.session_state.role = None

# --- Mock Data (Simulating Database) ---
MOCK_METRICS = {
    "Total Candidates": 1250,
    "Total JDs": 450,
    "Total Vendors": 85,
    "No of Applications": 5200,
    "No of Social Media Posts": 110,
}

MOCK_USERS = [
    {"id": "C-101", "name": "Alice Johnson", "role": "Candidate", "status": "Pending"},
    {"id": "C-102", "name": "Bob Smith", "role": "Candidate", "status": "Approved"},
    {"id": "V-201", "name": "Global Staffing", "role": "Vendor", "status": "Pending"},
    {"id": "V-202", "name": "Tech Recruiters Inc.", "role": "Vendor", "status": "Approved"},
]

MOCK_JDS = [
    {"id": "JD-001", "title": "Senior Python Developer", "skill": "Python, AWS, ML", "type": "Remote"},
    {"id": "JD-002", "title": "Marketing Manager", "skill": "SEO, Content, Analytics", "type": "Onsite"},
    {"id": "JD-003", "title": "Cloud Architect", "skill": "Azure, DevOps, Networking", "type": "Remote"},
]

MOCK_CVS = [
    {"id": "CV-01", "name": "Data Scientist CV", "skills": "Python, ML, Pandas", "status": "Processed"},
    {"id": "CV-02", "name": "Frontend Resume", "skills": "React, JS, CSS", "status": "Pending"},
]


# --- Helper Functions ---

# Function for LLM interaction using OpenAI
def llm_call(prompt, task):
    """Calls OpenAI LLM API for various tasks."""
    if not st.session_state.get('api_key'):
        # Fallback to mock if no API key
        time.sleep(1)  # Short delay for mock
        if "match" in task.lower():
            score = random.randint(50, 95)
            return f"**Match Score: {score}%** (Rank: #{random.randint(1, 10)})<br>Key Alignment: {prompt[:40]}...<br>Suggested Next Steps: Interview focusing on edge cases."
        elif "gap" in task.lower():
            return "**GAP Analysis (SWOT)**\n\n**Weakness:** Missing hands-on experience in Kubernetes.\n**Opportunity:** Excellent foundation in Python and AWS.\n**Suggestion:** Focus on containerization training (Docker/Kubernetes). "
        elif "write" in task.lower():
            return "Dear Hiring Team,\n\nI am writing to express my enthusiasm for the position of... My background in [Skill A] and [Skill B] aligns perfectly with the requirements of JD-001.\n\nSincerely,\nCandidate Name"
        elif "summarise" in task.lower():
            return f"**Summary:** Highly proficient in {prompt[:20]} with 5+ years of experience. Seeking challenging roles in tech."
        else:
            return f"LLM Content for '{task}': {prompt}"

    try:
        client = Groq(api_key=st.session_state.api_key)
        # Craft prompt based on task
        if "match" in task.lower():
            full_prompt = f"Analyze the match between the candidate's CV and the job description. Provide a match score out of 100, key alignment points, and suggested next steps. Details: {prompt}"
        elif "gap" in task.lower():
            full_prompt = f"Perform a gap analysis between the CV and JD. Provide SWOT analysis with strengths, weaknesses, opportunities, and threats. Details: {prompt}"
        elif "write" in task.lower():
            full_prompt = f"Write a professional cover letter for the candidate applying to the job. Make it personalized and compelling. Details: {prompt}"
        elif "summarise" in task.lower():
            full_prompt = f"Summarize the candidate's profile in a concise paragraph. Details: {prompt}"
        elif "jd analysis" in task.lower():
            full_prompt = f"Analyze the job description and provide 5 crucial questions a candidate should be able to answer. JD: {prompt}"
        elif "q&a" in task.lower():
            full_prompt = f"Provide Q&A analysis for the job description. JD: {prompt}"
        elif "generate jd" in task.lower():
            full_prompt = f"Generate a professional job description based on the following details: {prompt}"
        elif "swot" in task.lower():
            full_prompt = f"Perform SWOT analysis for CV vs JD. Details: {prompt}"
        elif "skills comparison" in task.lower():
            full_prompt = f"Compare skills between CV and JD. Details: {prompt}"
        elif "skill gap" in task.lower():
            full_prompt = f"Analyze skill gaps and provide a roadmap for filling them. Details: {prompt}"
        elif "road map" in task.lower():
            full_prompt = f"Create a detailed skill development roadmap. Details: {prompt}"
        else:
            full_prompt = f"{task}: {prompt}"

        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=1000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling LLM: {str(e)}. Falling back to mock response."


def display_dashboard_header(title):
    """Displays the main dashboard title and role context."""
    st.markdown(f"""
        <div style="background-color: #0077B6; padding: 15px; border-radius: 10px; color: white;">
            <h1 style="margin: 0; font-size: 2em;">{title}</h1>
            <p style="margin: 0;">Logged in as: <strong>{st.session_state.role.capitalize()}</strong></p>
        </div>
    """, unsafe_allow_html=True)
    st.write("")

def mock_logout():
    """Clears session state and redirects to login."""
    st.session_state.authenticated = False
    st.session_state.role = None

# --- Authentication & UI Functions ---

def login_signup_page():
    """Handles the initial login/signup selection and mock authentication."""
    st.title("Pragyan-AI")
    st.markdown("---")

    # Initialize show_signup if not exists
    if 'show_signup' not in st.session_state:
        st.session_state.show_signup = False

    if st.session_state.show_signup:
        signup_page()
    else:
        login_page()

def login_page():
    """Login page layout."""
    col1, col2, col3 = st.columns([2, 1, 1])

    roles = ["Admin", "Candidate", "Hiring Company"]

    with col1:
        st.header("Login")
        st.info("Select your role to access the mock dashboard.")
        selected_role = st.selectbox("Select Role", roles, index=None, placeholder="Choose Role...")
        username = st.text_input("Username (e.g., 'test')")
        password = st.text_input("Password (e.g., '1234')", type="password")

        if st.button("Log In", use_container_width=True, type="primary") and selected_role:
            # Mock authentication: any non-empty username/password combination logs in
            if username and password:
                st.session_state.authenticated = True
                st.session_state.role = selected_role.lower().replace(" ", "_")
                st.success(f"Successfully logged in as {selected_role}!")
            else:
                st.error("Please enter a username and password.")

        st.markdown("---")
        if st.button("Don't have an account? Sign Up", use_container_width=True):
            st.session_state.show_signup = True
            st.rerun()

def signup_page():
    """Signup/Registration page layout."""
    col1, col2, col3 = st.columns([2, 1, 1])

    roles = ["Admin", "Candidate", "Hiring Company"]

    with col1:
        st.header("Sign Up / Register")
        st.info("Create your account to access the platform.")

        # Registration form
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        selected_role = st.selectbox("Select Role", roles, index=None, placeholder="Choose Role...", key="signup_role")
        username = st.text_input("Username", key="signup_username")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")

        if st.button("Register", use_container_width=True, type="primary"):
            # Basic validation
            if not name or not email or not username or not password:
                st.error("Please fill in all required fields.")
            elif password != confirm_password:
                st.error("Passwords do not match.")
            elif selected_role is None:
                st.error("Please select a role.")
            else:
                # Mock registration - in real app, save to database
                st.success(f"Account created successfully for {name} as {selected_role}!")
                st.info("You can now log in with your credentials.")
                st.session_state.show_signup = False
                st.rerun()

        st.markdown("---")
        if st.button("Already have an account? Log In", use_container_width=True):
            st.session_state.show_signup = False


# --- Admin Dashboard Functions ---

def admin_dashboard():
    """Admin Dashboard Layout and Features."""
    display_dashboard_header("Admin Dashboard")

    # Sidebar with Platform Overview
    with st.sidebar:
        st.button("Logout", on_click=mock_logout, type="secondary")

        st.markdown("---")
        st.subheader("📊 Platform Overview")

        # Platform metrics in sidebar
        st.metric("Total Users", MOCK_METRICS["Total Candidates"])
        st.metric("Active Jobs", MOCK_METRICS["Total JDs"])
        st.metric("Companies", MOCK_METRICS["Total Vendors"])
        st.metric("Applications", MOCK_METRICS["No of Applications"])


    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 User Management",
        "📂 Resume Management",
        "📄 JD Management",
        "📈 Analytics & Reports"
    ])

    with tab1:
        st.subheader("User Management")

        # Create tabs for different user types
        candidate_tab, vendor_tab = st.tabs(["👤 Candidate - Approval", "🏢 Vendor - Approval"])

        with candidate_tab:
            st.markdown("### Candidate Approval")
            candidates = [u for u in MOCK_USERS if u["role"] == "Candidate"]

            if candidates:
                pending_candidates = [c for c in candidates if c["status"] == "Pending"]
                approved_candidates = [c for c in candidates if c["status"] == "Approved"]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Pending Candidates**")
                    if pending_candidates:
                        for candidate in pending_candidates:
                            with st.container():
                                st.write(f"**{candidate['name']}** ({candidate['id']})")
                                if st.button(f"Approve {candidate['name']}", key=f"approve_candidate_{candidate['id']}", type="primary"):
                                    candidate['status'] = 'Approved'
                                    st.success(f"✅ Approved {candidate['name']}")
                    else:
                        st.success("No pending candidates.")

                with col2:
                    st.markdown("**Approved Candidates**")
                    if approved_candidates:
                        for candidate in approved_candidates:
                            st.write(f"✅ {candidate['name']} ({candidate['id']})")
                    else:
                        st.info("No approved candidates yet.")

            else:
                st.info("No candidates found.")

        with vendor_tab:
            st.markdown("### Vendor Approval")
            vendors = [u for u in MOCK_USERS if u["role"] == "Vendor"]

            if vendors:
                pending_vendors = [v for v in vendors if v["status"] == "Pending"]
                approved_vendors = [v for v in vendors if v["status"] == "Approved"]

                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Pending Vendors**")
                    if pending_vendors:
                        for vendor in pending_vendors:
                            with st.container():
                                st.write(f"**{vendor['name']}** ({vendor['id']})")
                                if st.button(f"Approve {vendor['name']}", key=f"approve_vendor_{vendor['id']}", type="primary"):
                                    vendor['status'] = 'Approved'
                                    st.success(f"✅ Approved {vendor['name']}")
                    else:
                        st.success("No pending vendors.")

                with col2:
                    st.markdown("**Approved Vendors**")
                    if approved_vendors:
                        for vendor in approved_vendors:
                            st.write(f"✅ {vendor['name']} ({vendor['id']})")
                    else:
                        st.info("No approved vendors yet.")

            else:
                st.info("No vendors found.")
        

    with tab2:
        st.subheader("Resume Management")
        st.markdown("Admin tools for managing the central Resume repository.")

        # Create tabs for different upload methods
        upload_tabs = st.tabs(["a.Individual", "b.Bulk In Zip,pdf,doc Format", "c.Folder - Drive"])

        with upload_tabs[0]:
            st.markdown("### Individual Resume Upload")
            st.info("Upload single resume files in PDF or DOCX format.")

            with st.container():
                st.markdown("**Upload Options:**")
                col1, col2 = st.columns(2)

                with col1:
                    uploaded_file = st.file_uploader(
                        "Select Resume File",
                        type=['pdf', 'docx'],
                        key="individual_resume",
                        help="Supported formats: PDF, DOCX"
                    )

                    if uploaded_file is not None:
                        st.success(f"✅ File '{uploaded_file.name}' selected for upload")
                        st.info("File details:")
                        st.write(f"- **Name:** {uploaded_file.name}")
                        st.write(f"- **Size:** {uploaded_file.size} bytes")
                        st.write(f"- **Type:** {uploaded_file.type}")

                with col2:
                    st.markdown("**Processing Options:**")
                    auto_process = st.checkbox("Auto-process after upload", value=True)
                    extract_metadata = st.checkbox("Extract metadata", value=True)
                    ocr_enabled = st.checkbox("Enable OCR for scanned PDFs", value=False)

            if uploaded_file is not None:
                if st.button("Upload & Process Resume", type="primary", use_container_width=True):
                    with st.spinner("Processing resume..."):
                        time.sleep(2)  # Simulate processing
                    st.success("✅ Resume uploaded and processed successfully!")
                    st.balloons()

        with upload_tabs[1]:
            st.markdown("### Bulk Resume Upload")
            st.info("Upload multiple resumes at once using ZIP files or select multiple PDF/DOC files.")

            with st.container():
                st.markdown("**Bulk Upload Options:**")

                # ZIP Upload
                st.markdown("**Option 1: ZIP File Upload**")
                zip_file = st.file_uploader(
                    "Upload ZIP file containing resumes",
                    type=['zip'],
                    key="bulk_zip",
                    help="ZIP file should contain PDF/DOCX resume files"
                )

                if zip_file is not None:
                    st.success(f"✅ ZIP file '{zip_file.name}' selected")
                    st.info("ZIP file will be extracted and individual resumes processed.")

                st.markdown("---")
                st.markdown("**Option 2: Multiple File Selection**")
                multiple_files = st.file_uploader(
                    "Select multiple resume files",
                    type=['pdf', 'docx'],
                    accept_multiple_files=True,
                    key="bulk_multiple",
                    help="Select multiple PDF/DOCX files at once"
                )

                if multiple_files:
                    st.success(f"✅ {len(multiple_files)} files selected")
                    with st.expander("View selected files"):
                        for i, file in enumerate(multiple_files, 1):
                            st.write(f"{i}. {file.name} ({file.size} bytes)")

                # Processing options for bulk upload
                st.markdown("---")
                st.markdown("**Bulk Processing Options:**")
                col1, col2 = st.columns(2)

                with col1:
                    batch_size = st.selectbox(
                        "Processing Batch Size",
                        [10, 25, 50, 100],
                        index=1,
                        help="Number of resumes to process simultaneously"
                    )

                with col2:
                    priority_processing = st.checkbox("Priority processing", value=False)
                    duplicate_detection = st.checkbox("Enable duplicate detection", value=True)

            # Upload button for bulk operations
            if zip_file or multiple_files:
                total_files = 1 if zip_file else len(multiple_files) if multiple_files else 0
                if st.button(f"Upload & Process {total_files} Resume{'s' if total_files > 1 else ''}",
                           type="primary", use_container_width=True):
                    with st.spinner(f"Processing {total_files} resume{'s' if total_files > 1 else ''}..."):
                        progress_bar = st.progress(0)
                        for i in range(101):
                            time.sleep(0.02)  # Simulate processing time
                            progress_bar.progress(i)
                    st.success(f"✅ Successfully processed {total_files} resume{'s' if total_files > 1 else ''}!")
                    st.balloons()

        with upload_tabs[2]:
            st.markdown("### Folder/Drive Integration")
            st.info("Connect to cloud storage or local folders for automated resume ingestion.")

            with st.container():
                st.markdown("**Integration Options:**")

                integration_type = st.selectbox(
                    "Select Integration Type",
                    ["OneDrive", "Dropbox", "Local Folder", "SFTP Server"],
                    help="Choose the storage service to connect"
                )

                if integration_type == "OneDrive":
                    st.markdown("**OneDrive Integration**")
                    onedrive_folder_url = st.text_input(
                        "OneDrive Folder URL",
                        placeholder="https://onedrive.live.com/...",
                        help="Paste the shareable link of your OneDrive folder"
                    )
                    if onedrive_folder_url:
                        st.info("🔗 Connection established (mocked)")
                        st.success("✅ Ready to sync resumes from OneDrive folder")

                elif integration_type == "Dropbox":
                    st.markdown("**Dropbox Integration**")
                    dropbox_folder_url = st.text_input(
                        "Dropbox Folder URL",
                        placeholder="https://www.dropbox.com/...",
                        help="Paste the shareable link of your Dropbox folder"
                    )
                    if dropbox_folder_url:
                        st.info("🔗 Connection established (mocked)")
                        st.success("✅ Ready to sync resumes from Dropbox folder")

                elif integration_type == "Local Folder":
                    st.markdown("**Local Folder Integration**")
                    local_folder_path = st.text_input(
                        "Local Folder Path",
                        placeholder="C:/Users/Documents/Resumes",
                        help="Enter the full path to your local resume folder"
                    )
                    if local_folder_path:
                        st.info("📁 Local folder path configured")
                        st.success("✅ Ready to monitor local folder for new resumes")

                elif integration_type == "SFTP Server":
                    st.markdown("**SFTP Server Integration**")
                    col1, col2 = st.columns(2)
                    with col1:
                        sftp_host = st.text_input("SFTP Host", placeholder="ftp.example.com")
                        sftp_username = st.text_input("Username")
                    with col2:
                        sftp_port = st.number_input("Port", value=22, min_value=1, max_value=65535)
                        sftp_path = st.text_input("Remote Path", placeholder="/resumes")

                    sftp_password = st.text_input("Password", type="password")

                    if sftp_host and sftp_username and sftp_password:
                        st.info("🔗 SFTP connection configured (mocked)")
                        st.success("✅ Ready to sync resumes from SFTP server")

                if st.button("Start Sync", type="primary", use_container_width=True):
                    with st.spinner("Establishing connection and syncing..."):
                        time.sleep(3)  # Simulate connection time
                    st.success("✅ Sync connection established! Monitoring for new resumes...")
                    st.info("📊 Last sync: Just now | Files synced: 0 | Status: Active")

        # Common section for all upload methods
        st.markdown("---")
        st.subheader("Resume Storage View")
        st.markdown("**Current Resume Repository:**")

        # Enhanced resume view with filtering
        col_filter, col_search = st.columns([1, 2])
        with col_filter:
            status_filter = st.selectbox("Filter by Status", ["All", "Processed", "Pending"], index=0)
        with col_search:
            search_term = st.text_input("Search resumes", placeholder="Enter name or skill...")

        # Filter the resume data
        filtered_cvs = MOCK_CVS.copy()
        if status_filter != "All":
            filtered_cvs = [cv for cv in filtered_cvs if cv["status"].lower() == status_filter.lower()]
        if search_term:
            filtered_cvs = [cv for cv in filtered_cvs
                          if search_term.lower() in cv["name"].lower() or
                             search_term.lower() in cv["skills"].lower()]

        if filtered_cvs:
            st.dataframe(pd.DataFrame(filtered_cvs), use_container_width=True)
            st.info(f"Showing {len(filtered_cvs)} of {len(MOCK_CVS)} resumes")
        else:
            st.info("No resumes match the current filters.")

        # Storage statistics
        st.markdown("---")
        st.markdown("**Storage Statistics:**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Resumes", len(MOCK_CVS))
        with col2:
            st.metric("Processed", len([cv for cv in MOCK_CVS if cv["status"] == "Processed"]))
        with col3:
            st.metric("Pending", len([cv for cv in MOCK_CVS if cv["status"] == "Pending"]))
        with col4:
            st.metric("Storage Used", "2.4 GB")

    with tab3:
        st.subheader("JD Management")
        st.info("Centralized system for importing and validating Job Descriptions.")

        jd_options = st.tabs(["Web URL - Neural", "Upload - PDF/DOC", "Paste - Text", "Linkedin - URL"])

        with jd_options[0]:
            url = st.text_input("Enter JD Web URL:", key="jd_web_url")
            if st.button("Process URL & Extract JD", use_container_width=True, key="process_jd_url"):
                st.toast(f"Extracting JD content from {url}... (Mocked)")
                st.success("JD content extracted and validated.")

        with jd_options[1]:
            st.file_uploader("Upload JD Document (PDF/DOC)", type=['pdf', 'docx'], key="jd_document_upload")

        with jd_options[2]:
            st.text_area("Paste JD Content Here", height=200, key="jd_content_paste")

        with jd_options[3]:
            st.text_input("Enter LinkedIn Job Post URL:", key="linkedin_jd_url")
            if st.button("Import from LinkedIn", key="import_linkedin_jd"):
                st.toast("Importing data from LinkedIn... (Mocked)")

    with tab4:
        st.subheader("Analytics & Reports")
        st.info("Comprehensive analytics and reporting dashboard for platform insights.")

        # Analytics tabs
        analytics_tabs = st.tabs(["Platform Metrics", "User Activity", "Resume Analytics", "JD Performance"])

        with analytics_tabs[0]:
            st.markdown("### Platform Overview Metrics")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users", MOCK_METRICS["Total Candidates"], "+12%")
            with col2:
                st.metric("Active Jobs", MOCK_METRICS["Total JDs"], "+5%")
            with col3:
                st.metric("Companies", MOCK_METRICS["Total Vendors"], "+8%")
            with col4:
                st.metric("Applications", MOCK_METRICS["No of Applications"], "+15%")

            st.markdown("---")
            st.markdown("### Growth Trends")
            # Mock chart data
            trend_data = pd.DataFrame({
                'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                'Users': [100, 150, 200, 250, 300, 350],
                'Applications': [200, 300, 400, 500, 600, 700]
            })
            st.line_chart(trend_data.set_index('Month'))

        with analytics_tabs[1]:
            st.markdown("### User Activity Analytics")
            st.markdown("**Recent Activity:**")
            activity_data = pd.DataFrame({
                "User": ["Alice Johnson", "Bob Smith", "Global Staffing"],
                "Action": ["Uploaded Resume", "Applied for JD-001", "Posted New JD"],
                "Timestamp": ["2025-11-01 10:30", "2025-11-01 09:15", "2025-10-31 16:45"]
            })
            st.dataframe(activity_data, use_container_width=True)

        with analytics_tabs[2]:
            st.markdown("### Resume Repository Analytics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Resumes", len(MOCK_CVS))
                st.metric("Processed Today", "5")
            with col2:
                st.metric("Pending Review", len([cv for cv in MOCK_CVS if cv["status"] == "Pending"]))
                st.metric("Avg Processing Time", "2.3 min")

            st.markdown("---")
            st.markdown("**Resume Skills Distribution:**")
            skills_data = pd.DataFrame({
                'Skill': ['Python', 'JavaScript', 'AWS', 'React', 'ML'],
                'Count': [45, 38, 32, 28, 25]
            })
            st.bar_chart(skills_data.set_index('Skill'))

        with analytics_tabs[3]:
            st.markdown("### Job Description Performance")
            jd_perf_data = pd.DataFrame({
                "JD ID": ["JD-001", "JD-002", "JD-003"],
                "Title": ["Senior Python Developer", "Marketing Manager", "Cloud Architect"],
                "Applications": [25, 18, 12],
                "Avg Match Score": [87, 82, 91]
            })
            st.dataframe(jd_perf_data, use_container_width=True)

            st.markdown("---")
            st.markdown("**Export Reports:**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Export Analytics Report (PDF)", use_container_width=True):
                    st.success("Report generated and downloaded!")
            with col2:
                if st.button("Export Data (CSV)", use_container_width=True):
                    st.success("CSV file generated and downloaded!")




# --- Candidate Dashboard Functions ---

def candidate_dashboard():
    """Candidate Dashboard Layout and Features."""
    display_dashboard_header("Candidate Dashboard")
    
    st.sidebar.button("Logout", on_click=mock_logout, type="secondary")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📂 Resume Management",
        "🔍 Job Descriptions",
        "🎯 CV-JD Match & Analysis",
        "💡 Skill Evaluation",
        "📈 Upskill - Based Skill Gap"
    ])

    with tab1:
        st.subheader("a. Prepare your CV")
        
        cv_options = st.tabs(["i. Form Based Details", "ii. Upload the CV - Docx/PDF", "iii. Paste Your CV", "iv. Get from Linkedin"])
        
        with cv_options[0]:
            st.caption("Prepare your CV using our structured form.")
            st.text_input("Full Name")
            st.text_area("Experience Details (Form-Based Mock)")
            st.button("Save Profile Details")
        
        with cv_options[1]:
            st.file_uploader("Upload your CV (DOCX/PDF)", type=['docx', 'pdf'])
            
        with cv_options[2]:
            st.text_area("Paste your entire CV content here", height=300)

        with cv_options[3]:
            st.text_input("Enter your LinkedIn Profile URL")
            st.button("Import Resume from LinkedIn")
            
        st.markdown("---")
        st.subheader("b. View the CV / Profile")
        cv_view = st.tabs(["i. PDF View", "ii. Markdown View", "iii. JSON View", "iv. Download Resume"])
        with cv_view[0]:
            st.markdown("### PDF View")
            st.info("PDF viewer would be embedded here (mocked)")
            st.markdown("**Resume Preview:**")
            st.code("PDF Content: John Doe - Senior Developer\nExperience: 5+ years in Python development\nSkills: Python, Django, React")
        with cv_view[1]:
            st.markdown("### Markdown View")
            st.markdown("**My Current Resume (Markdown View)**")
            st.code("""# John Doe

## Professional Summary
Experienced Python developer with 5+ years in web development and data science.

## Skills
- Python (Advanced)
- Django, Flask
- React, JavaScript
- SQL, PostgreSQL
- AWS, Docker
- Machine Learning

## Experience
### Senior Python Developer
Tech Corp | 2020-Present
- Developed scalable web applications
- Led team of 3 developers
- Implemented CI/CD pipelines

### Python Developer
Startup Inc | 2018-2020
- Built REST APIs
- Data analysis and visualization
- Agile development practices

## Education
BSc Computer Science | University Name | 2014-2018
""")
        with cv_view[2]:
            st.markdown("### JSON View")
            st.json({
                "name": "John Doe",
                "title": "Senior Python Developer",
                "experience_years": 5,
                "skills": ["Python", "Django", "React", "AWS", "Docker", "Machine Learning"],
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Senior Python Developer",
                        "period": "2020-Present",
                        "responsibilities": ["Developed scalable web applications", "Led team of 3 developers"]
                    },
                    {
                        "company": "Startup Inc",
                        "position": "Python Developer",
                        "period": "2018-2020",
                        "responsibilities": ["Built REST APIs", "Data analysis"]
                    }
                ],
                "education": {
                    "degree": "BSc Computer Science",
                    "university": "University Name",
                    "year": "2014-2018"
                }
            })
        with cv_view[3]:
            st.markdown("### Download Resume")
            st.info("Download your resume in various formats")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Download as PDF", key="download_pdf"):
                    st.success("PDF download initiated!")
                if st.button("Download as DOCX", key="download_docx"):
                    st.success("DOCX download initiated!")
            with col2:
                if st.button("Download as Markdown", key="download_md"):
                    st.success("Markdown download initiated!")
                if st.button("Download as JSON", key="download_json"):
                    st.success("JSON download initiated!")


    with tab2:
        st.subheader("1.Job Descriptions")

        st.markdown("**a. View & Search - Available Jobs**")

        st.markdown("**i. Display all JD - Based on**")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**1. Skill**")
            search_skill = st.text_input("Search by Skill (e.g., Python, AWS)")
        with col2:
            st.markdown("**2. Job Type - Remote / Onsite**")
            search_type = st.selectbox("Filter by Job Type", ["All", "Remote", "Onsite"])

        st.markdown("**3. RQ&A - JD**")
        st.markdown("**a. Select JD or Select CV**")
        selected_jd_id = st.selectbox("Select a JD to Analyze", [jd['id'] for jd in MOCK_JDS])

        st.markdown("**4. Role Based**")
        if st.button("Search Jobs", type="primary"):
            filtered_jds = [jd for jd in MOCK_JDS if (search_skill.lower() in jd['skill'].lower() or not search_skill) and (search_type == "All" or search_type == jd['type'])]
            st.info(f"Found {len(filtered_jds)} relevant Job Descriptions.")
            st.dataframe(pd.DataFrame(filtered_jds), use_container_width=True)

        if st.button("Run LLM Q&A on JD"):
            result = llm_call(f"Analyze JD {selected_jd_id} requirements and list 5 crucial questions a candidate should be able to answer.", "JD Analysis")
            st.markdown(f"**LLM Generated Questions for {selected_jd_id}:**")
            st.markdown(result)

        if st.button(f"Apply for {selected_jd_id}", key=f"apply_{selected_jd_id}_tab2"):
            st.toast(f"Application for {selected_jd_id} submitted successfully!")

        st.markdown("---")
        st.markdown("**b. Upload JD**")

        upload_tabs = st.tabs(["i. WebLink", "ii. Paste Text", "iii. Upload Doc/PDF", "iv. LinkedIn", "v. LLM based Q&A"])

        with upload_tabs[0]:
            st.markdown("**WebLink**")
            url = st.text_input("Enter JD Web URL:")
            if st.button("Process URL & Extract JD", use_container_width=True):
                st.toast(f"Extracting JD content from {url}... (Mocked)")
                st.success("JD content extracted and validated.")

        with upload_tabs[1]:
            st.markdown("**Paste Text**")
            st.text_area("Paste JD Content Here", height=200)

        with upload_tabs[2]:
            st.markdown("**Upload Doc/PDF**")
            st.file_uploader("Upload JD Document (PDF/DOC)", type=['pdf', 'docx'])

        with upload_tabs[3]:
            st.markdown("**LinkedIn**")
            st.text_input("Enter LinkedIn Job Post URL:")
            if st.button("Import from LinkedIn"):
                st.toast("Importing data from LinkedIn... (Mocked)")

        with upload_tabs[4]:
            st.markdown("**LLM based Q&A**")
            selected_jd_for_qa = st.selectbox("Select JD for Q&A", [jd['id'] for jd in MOCK_JDS], key="jd_qa")
            if st.button("Run Q&A Analysis"):
                result = llm_call(f"Q&A for JD {selected_jd_for_qa}", "JD Q&A")
                st.markdown(f"**Q&A Results for {selected_jd_for_qa}:**")
                st.markdown(result)


    with tab3:
        st.subheader("Match CV with JD")

        st.markdown("**a. Match CV with Select the JDs**")

        st.markdown("**i. Match CV with JD**")

        cv_match_jd = st.selectbox("Select a Job Description for Matching:", [jd['id'] for jd in MOCK_JDS])

        st.markdown("**1. Ranks - Best Matches**")
        if st.button("Run CV-JD Match & Ranking", type="primary"):
            st.balloons()
            match_result = llm_call(f"CV Content vs {cv_match_jd}", "Match Score")
            st.markdown(f"### 🎯 Match Results for {cv_match_jd}")
            st.markdown(match_result, unsafe_allow_html=True)

        st.markdown("**2. Apply the Jobs**")
        if st.button(f"Apply for {cv_match_jd}", key=f"apply_{cv_match_jd}_tab3"):
            st.toast(f"Application for {cv_match_jd} submitted successfully!")

        st.markdown("---")
        st.markdown("**b. Write CV for Specific JD**")

        st.markdown("**i. Select the Specific JD**")
        specific_jd = st.selectbox("Select Specific JD for CV Writing:", [jd['id'] for jd in MOCK_JDS], key="specific_jd")

        st.markdown("**ii. Deep Analysis with Any JD - GAP Analysis - SWOT Analysis**")

        st.markdown("**1. Match Score**")
        if st.button("Get Match Score", key="match_score"):
            match_result = llm_call(f"CV Content vs {specific_jd}", "Match Score")
            st.markdown(f"### Match Score for {specific_jd}")
            st.markdown(match_result, unsafe_allow_html=True)

        st.markdown("**2. GAP Analysis - SWOT Analysis**")
        if st.button("Run GAP Analysis & SWOT", key="gap_swot"):
            gap_result = llm_call(f"CV Content vs {specific_jd}", "GAP Analysis")
            st.markdown(f"### GAP Analysis & SWOT for {specific_jd}")
            st.markdown(gap_result, unsafe_allow_html=True)

        st.markdown("**3. Suggest Changes**")
        st.info("Suggested CV modifications based on GAP analysis:")
        st.text_area("Suggested Changes:", value="Add specific project details on Kubernetes.", key="suggest_changes")

        st.markdown("**4. Modify the CV**")
        if st.button("Modify CV", key="modify_cv"):
            st.toast("CV Modified successfully!")

        st.markdown("**5. Rematch JD and Score Difference Analysis**")
        if st.button("Rematch & Analyze Score Difference", key="rematch"):
            st.toast("Running Rematch...")
            rematch_result = llm_call(f"Modified CV vs {specific_jd}", "Match Score Rematch")
            st.markdown(f"### 🔄 Rematch Score Difference Analysis for {specific_jd}")
            st.markdown(rematch_result, unsafe_allow_html=True)
            st.success("Rematch complete! Score improved by 5%.")

        st.markdown("**6. Apply Job or Download the CV**")
        col_apply, col_download = st.columns(2)
        with col_apply:
            if st.button("Apply Job", key="apply_job_final"):
                st.toast("Application submitted!")
        with col_download:
            if st.button("Download CV", key="download_cv"):
                st.toast("CV download initiated!")

        st.markdown("---")
        st.markdown("**c. Write Cover Letter - for Specific JD and Resume**")

        st.markdown("**i. Select JD**")
        cl_jd = st.selectbox("Select JD for Cover Letter:", [jd['id'] for jd in MOCK_JDS], key="cl_jd")

        st.markdown("**1. Write Cover Letter**")
        cl_tone = st.radio("Select Tone", ["Professional", "Enthusiastic", "Concise"], key="cl_tone")
        if st.button("Generate Cover Letter", type="primary", key="generate_cl"):
            cl_prompt = f"Write a {cl_tone} cover letter for JD {cl_jd} using my current resume."
            cover_letter = llm_call(cl_prompt, "Write Cover Letter")
            st.markdown("### Generated Cover Letter:")
            st.code(cover_letter, language="text")

        st.markdown("**2. Download / Copy Cover Letter**")
        col_dl, col_copy = st.columns(2)
        with col_dl:
            if st.button("Download Cover Letter (DOCX)", key="dl_cl"):
                st.success("Cover letter downloaded!")
        with col_copy:
            if st.button("Copy Cover Letter to Clipboard", key="copy_cl"):
                st.success("Cover letter copied to clipboard!")

    with tab4:
        st.subheader("Skill Evaluation")

        st.markdown("**a. Mock Interviews for Specific JD**")

        st.markdown("**i. Selecting the JD and Mock Interview & Evaluation**")
        mi_jd = st.selectbox("Select JD for Mock Interview:", [jd['id'] for jd in MOCK_JDS], key="mi_jd")
        if st.button(f"Start Mock Interview for {mi_jd}", type="primary", key="start_mi"):
            st.info(f"Starting LLM-powered Mock Interview for {mi_jd}... (Interaction Mocked)")
            st.markdown("Interview Evaluation: Your answer on 'Cloud Scalability' was good, but lacked technical depth. Score: 7/10.")

        st.markdown("---")
        st.markdown("**b. Skill Evaluation**")

        st.markdown("**i. Skill Mentioned in Road Map - Evaluation**")
        up_jd = st.selectbox("Select JD to Analyze Skill Gap:", [jd['id'] for jd in MOCK_JDS], key="up_jd")

        if st.button("Get Skill Gap & Road Map", key="skill_gap"):
            st.toast(f"Analyzing skill gaps against {up_jd}...")
            gap_analysis = llm_call(f"Skill gap analysis for CV vs {up_jd}", "Skill Gap Road Map")

            st.markdown("### Skill Road Map & Suggested Certifications")
            st.markdown(gap_analysis, unsafe_allow_html=True)
            st.markdown("""
            **How to fill the gap:**
            1.  **Course Plan:** *Suggested Course: MongoDB Complete Guide (Coursera)* (30 hours)
            2.  **Certificate:** *Suggested Certificate: Certified Kubernetes Administrator (CKA)*
            """)

    with tab5:
        st.subheader("Upskill - Based Skill Gap")

        st.markdown("**a. Select JD**")

        st.markdown("**i. Get The Skill Gap**")
        upskill_jd = st.selectbox("Select JD for Skill Gap Analysis:", [jd['id'] for jd in MOCK_JDS], key="upskill_jd")

        if st.button("Analyze Skill Gap", type="primary", key="analyze_gap"):
            st.toast(f"Analyzing skill gaps against {upskill_jd}...")
            gap_analysis = llm_call(f"Skill gap analysis for CV vs {upskill_jd}", "Skill Gap Analysis")

            st.markdown("### Skill Gap Analysis")
            st.markdown(gap_analysis, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**b. Skill Road Map**")

        st.markdown("**ii. How to fill the Gap - Detailed Course Plan - Suggested Certificate**")

        if st.button("Generate Skill Road Map", type="primary", key="generate_roadmap"):
            roadmap = llm_call(f"Detailed skill roadmap for CV vs {upskill_jd}", "Skill Road Map")

            st.markdown("### Detailed Skill Development Road Map")
            st.markdown(roadmap, unsafe_allow_html=True)
            st.markdown("""
            **How to fill the gap:**
            1. **Course Plan:** *Suggested Course: MongoDB Complete Guide (Coursera)* (30 hours)
            2. **Certificate:** *Suggested Certificate: Certified Kubernetes Administrator (CKA)*
            3. **Practice Projects:** Build a full-stack application using the learned technologies
            4. **Mentorship:** Join developer communities and seek guidance
            """)


# --- Hiring Company Dashboard Functions ---

def hiring_company_dashboard():
    """Hiring Company Dashboard Layout and Features."""
    display_dashboard_header("Hiring Company Dashboard")

    st.sidebar.button("Logout", on_click=mock_logout, type="secondary")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📝 Create JD",
        "📄 Upload the CVs",
        "🔍 Explore CV",
        "🎯 Match CVs with JD",
        "Screen - Basic Screening",
        "📊 Candidate Profile Track"
    ])

    with tab1:
        st.subheader("Create Job Description")

        jd_creation_tabs = st.tabs([
            "a. Upload Doc",
            "b. From Linkedin",
            "c. Paste Content",
            "d. AI Assisted"
        ])

        with jd_creation_tabs[0]:
            st.markdown("### Upload Document")
            st.info("Upload a JD document in PDF or DOCX format.")
            uploaded_jd_file = st.file_uploader(
                "Select JD File",
                type=['pdf', 'docx'],
                key="jd_upload_doc",
                help="Supported formats: PDF, DOCX"
            )
            if uploaded_jd_file is not None:
                st.success(f"✅ File '{uploaded_jd_file.name}' uploaded successfully")
                st.info("File details:")
                st.write(f"- **Name:** {uploaded_jd_file.name}")
                st.write(f"- **Size:** {uploaded_jd_file.size} bytes")
                st.write(f"- **Type:** {uploaded_jd_file.type}")
                if st.button("Process JD Document", type="primary", use_container_width=True):
                    with st.spinner("Processing JD document..."):
                        time.sleep(2)
                    st.success("✅ JD processed and saved to repository!")

        with jd_creation_tabs[1]:
            st.markdown("### From LinkedIn")
            st.info("Import JD from a LinkedIn job post URL.")
            linkedin_url = st.text_input(
                "Enter LinkedIn Job Post URL",
                placeholder="https://www.linkedin.com/jobs/...",
                key="linkedin_jd_url_hiring"
            )
            if linkedin_url:
                st.info("🔗 URL provided")
                if st.button("Import from LinkedIn", type="primary", use_container_width=True):
                    with st.spinner("Importing JD from LinkedIn..."):
                        time.sleep(2)
                    st.success("✅ JD imported and saved from LinkedIn!")

        with jd_creation_tabs[2]:
            st.markdown("### Paste Content")
            st.info("Paste the JD content directly.")
            pasted_jd_content = st.text_area(
                "Paste JD Content Here",
                height=300,
                placeholder="Paste the full job description content...",
                key="paste_jd_content"
            )
            if pasted_jd_content:
                st.info(f"Content length: {len(pasted_jd_content)} characters")
                if st.button("Process Pasted Content", type="primary", use_container_width=True):
                    with st.spinner("Processing pasted JD content..."):
                        time.sleep(2)
                    st.success("✅ JD processed and saved from pasted content!")

        with jd_creation_tabs[3]:
            st.markdown("### AI Assisted")
            st.info("Use AI to generate or assist in creating a JD.")

            ai_assist_tabs = st.tabs(["i. Form Based"])

            with ai_assist_tabs[0]:
                st.markdown("#### Form Based JD Creation")
                st.info("Fill out the form below, and AI will generate a professional JD.")

                col1, col2 = st.columns(2)
                with col1:
                    job_title = st.text_input("Job Title", placeholder="e.g., Senior Python Developer", key="ai_job_title")
                    company_name = st.text_input("Company Name", placeholder="e.g., Tech Corp", key="ai_company_name")
                    location = st.text_input("Location", placeholder="e.g., Remote, New York", key="ai_location")
                    job_type = st.selectbox("Job Type", ["Full-time", "Part-time", "Contract", "Freelance"], key="ai_job_type")

                with col2:
                    experience_level = st.selectbox("Experience Level", ["Entry Level", "Mid Level", "Senior Level", "Executive"], key="ai_experience_level")
                    salary_range = st.text_input("Salary Range", placeholder="e.g., $80,000 - $120,000", key="ai_salary_range")
                    skills_required = st.text_area("Key Skills Required", placeholder="Python, AWS, ML\nDocker, Kubernetes", height=100, key="ai_skills")
                    responsibilities = st.text_area("Key Responsibilities", placeholder="Develop software solutions\nCollaborate with team", height=100, key="ai_responsibilities")

                if st.button("Generate JD with AI", type="primary", use_container_width=True):
                    if job_title and skills_required:
                        with st.spinner("AI generating JD..."):
                            time.sleep(3)
                        generated_jd = llm_call(f"Generate JD for {job_title} with skills: {skills_required}", "Generate JD")
                        st.markdown("### Generated Job Description:")
                        st.code(generated_jd, language="text")
                        if st.button("Save Generated JD", key="save_ai_jd"):
                            st.success("✅ JD saved to repository!")
                    else:
                        st.error("Please fill in at least Job Title and Key Skills.")

    with tab2:
        st.subheader("Upload the CVs")

        cv_upload_tabs = st.tabs([
            "a. Individual",
            "b. Bulk",
            "c. Digital CV Bank"
        ])

        with cv_upload_tabs[0]:
            st.markdown("### Individual CV Upload")
            st.info("Upload single CV files in PDF or DOCX format.")

            with st.container():
                st.markdown("**Upload Options:**")
                col1, col2 = st.columns(2)

                with col1:
                    uploaded_cv_file = st.file_uploader(
                        "Select CV File",
                        type=['pdf', 'docx'],
                        key="individual_cv_upload",
                        help="Supported formats: PDF, DOCX"
                    )

                    if uploaded_cv_file is not None:
                        st.success(f"✅ File '{uploaded_cv_file.name}' selected for upload")
                        st.info("File details:")
                        st.write(f"- **Name:** {uploaded_cv_file.name}")
                        st.write(f"- **Size:** {uploaded_cv_file.size} bytes")
                        st.write(f"- **Type:** {uploaded_cv_file.type}")


            if uploaded_cv_file is not None:
                if st.button("Upload & Process CV", type="primary", use_container_width=True, key="upload_process_cv"):
                    with st.spinner("Processing CV..."):
                        time.sleep(2)
                    st.success("✅ CV uploaded and processed successfully!")
                    st.balloons()

        with cv_upload_tabs[1]:
            st.markdown("### Bulk CV Upload")
            st.info("Upload multiple CVs at once using ZIP files or select multiple PDF/DOC files.")

            with st.container():
                st.markdown("**Bulk Upload Options:**")

                # ZIP Upload
                st.markdown("**Option 1: ZIP File Upload**")
                zip_cv_file = st.file_uploader(
                    "Upload ZIP file containing CVs",
                    type=['zip'],
                    key="bulk_cv_zip",
                    help="ZIP file should contain PDF/DOCX CV files"
                )

                if zip_cv_file is not None:
                    st.success(f"✅ ZIP file '{zip_cv_file.name}' selected")
                    st.info("ZIP file will be extracted and individual CVs processed.")

                st.markdown("---")
                st.markdown("**Option 2: Multiple File Selection**")
                multiple_cv_files = st.file_uploader(
                    "Select multiple CV files",
                    type=['pdf', 'docx'],
                    accept_multiple_files=True,
                    key="bulk_cv_multiple",
                    help="Select multiple PDF/DOCX files at once"
                )

                if multiple_cv_files:
                    st.success(f"✅ {len(multiple_cv_files)} files selected")
                    with st.expander("View selected files"):
                        for i, file in enumerate(multiple_cv_files, 1):
                            st.write(f"{i}. {file.name} ({file.size} bytes)")


            # Upload button for bulk operations
            if zip_cv_file or multiple_cv_files:
                total_cv_files = 1 if zip_cv_file else len(multiple_cv_files) if multiple_cv_files else 0
                if st.button(f"Upload & Process {total_cv_files} CV{'s' if total_cv_files > 1 else ''}",
                           type="primary", use_container_width=True, key="bulk_upload_process_cv"):
                    with st.spinner(f"Processing {total_cv_files} CV{'s' if total_cv_files > 1 else ''}..."):
                        progress_bar_cv = st.progress(0)
                        for i in range(101):
                            time.sleep(0.02)
                            progress_bar_cv.progress(i)
                    st.success(f"✅ Successfully processed {total_cv_files} CV{'s' if total_cv_files > 1 else ''}!")
                    st.balloons()

        with cv_upload_tabs[2]:
            st.markdown("### Digital CV Bank")
            st.info("Connect to digital CV repositories and databases for automated CV ingestion.")

            with st.container():
                st.markdown("**Integration Options:**")

                cv_bank_type = st.selectbox(
                    "Select CV Bank Type",
                    ["LinkedIn", "Indeed", "Glassdoor", "Company Database", "External API"],
                    key="cv_bank_type",
                    help="Choose the CV source to connect"
                )

                if cv_bank_type == "LinkedIn":
                    st.markdown("**LinkedIn CV Bank Integration**")
                    linkedin_cv_url = st.text_input(
                        "LinkedIn Search URL or Profile",
                        placeholder="https://www.linkedin.com/in/... or search URL",
                        key="linkedin_cv_url",
                        help="Paste LinkedIn profile URL or search results URL"
                    )
                    if linkedin_cv_url:
                        st.info("🔗 LinkedIn URL configured")
                        st.success("✅ Ready to import CVs from LinkedIn")

                elif cv_bank_type == "Indeed":
                    st.markdown("**Indeed CV Bank Integration**")
                    indeed_cv_url = st.text_input(
                        "Indeed Search URL",
                        placeholder="https://in.indeed.com/...",
                        key="indeed_cv_url",
                        help="Paste Indeed job search URL to extract candidate CVs"
                    )
                    if indeed_cv_url:
                        st.info("🔗 Indeed URL configured")
                        st.success("✅ Ready to import CVs from Indeed")

                elif cv_bank_type == "Glassdoor":
                    st.markdown("**Glassdoor CV Bank Integration**")
                    glassdoor_cv_url = st.text_input(
                        "Glassdoor Company URL",
                        placeholder="https://www.glassdoor.co.in/...",
                        key="glassdoor_cv_url",
                        help="Paste Glassdoor company profile URL"
                    )
                    if glassdoor_cv_url:
                        st.info("🔗 Glassdoor URL configured")
                        st.success("✅ Ready to import CVs from Glassdoor")

                elif cv_bank_type == "Company Database":
                    st.markdown("**Company Database Integration**")
                    col1, col2 = st.columns(2)
                    with col1:
                        db_host = st.text_input("Database Host", placeholder="localhost", key="db_host")
                        db_username = st.text_input("Username", key="db_username")
                    with col2:
                        db_port = st.number_input("Port", value=5432, min_value=1, max_value=65535, key="db_port")
                        db_name = st.text_input("Database Name", key="db_name")

                    db_password = st.text_input("Password", type="password", key="db_password")

                    if db_host and db_username and db_password:
                        st.info("🔗 Database connection configured (mocked)")
                        st.success("✅ Ready to sync CVs from company database")

                elif cv_bank_type == "External API":
                    st.markdown("**External API Integration**")
                    api_endpoint = st.text_input(
                        "API Endpoint URL",
                        placeholder="https://api.example.com/cvs",
                        key="api_endpoint",
                        help="Enter the API endpoint for CV data"
                    )
                    api_key = st.text_input("API Key", type="password", key="api_key")

                    if api_endpoint and api_key:
                        st.info("🔗 API connection configured (mocked)")
                        st.success("✅ Ready to import CVs from external API")

                if st.button("Start CV Bank Sync", type="primary", use_container_width=True, key="start_cv_bank_sync"):
                    with st.spinner("Establishing connection and syncing CVs..."):
                        time.sleep(3)
                    st.success("✅ CV Bank sync connection established! Monitoring for new CVs...")
                    st.info("📊 Last sync: Just now | CVs synced: 0 | Status: Active")


    with tab3:
        st.subheader("Explore CV")

        explore_tabs = st.tabs([
            "a. Filter CVs",
            "b. LLM"
        ])

        with explore_tabs[0]:
            st.markdown("### Filter CVs")
            st.info("Filter and search through uploaded CVs.")

            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                status_filter = st.selectbox("Filter by Status", ["All", "Processed", "Pending"], index=0, key="explore_status_filter")
                skill_filter = st.text_input("Filter by Skill", placeholder="e.g., Python, AWS", key="explore_skill_filter")
            with col2:
                name_search = st.text_input("Search by Name", placeholder="Enter candidate name", key="explore_name_search")
                experience_filter = st.selectbox("Experience Level", ["All", "Entry", "Mid", "Senior"], index=0, key="explore_exp_filter")

            # Apply filters
            filtered_cvs = MOCK_CVS.copy()
            if status_filter != "All":
                filtered_cvs = [cv for cv in filtered_cvs if cv["status"].lower() == status_filter.lower()]
            if skill_filter:
                filtered_cvs = [cv for cv in filtered_cvs if skill_filter.lower() in cv["skills"].lower()]
            if name_search:
                filtered_cvs = [cv for cv in filtered_cvs if name_search.lower() in cv["name"].lower()]

            if filtered_cvs:
                st.dataframe(pd.DataFrame(filtered_cvs), use_container_width=True)
                st.info(f"Showing {len(filtered_cvs)} of {len(MOCK_CVS)} CVs")
            else:
                st.info("No CVs match the current filters.")

        with explore_tabs[1]:
            st.markdown("### LLM Analysis")

            llm_subtabs = st.tabs([
                "1. Query Inform - from Individual Bulk",
                "2. Organize - CV - In Folder",
                "3. Summarise CV - Analysis"
            ])

            with llm_subtabs[0]:
                st.markdown("#### Query Inform - from Individual Bulk")
                st.info("Query specific information from individual or bulk CVs using LLM.")

                query_type = st.selectbox("Select Query Type", ["Individual CV", "Bulk Analysis"], key="query_type")
                if query_type == "Individual CV":
                    selected_cv = st.selectbox("Select CV", [cv["name"] for cv in MOCK_CVS], key="selected_cv_query")
                    query = st.text_area("Enter your query", placeholder="e.g., What is the candidate's experience with Python?", key="cv_query")
                    if st.button("Run Query", key="run_cv_query"):
                        result = llm_call(f"Query: {query} for CV: {selected_cv}", "Query CV")
                        st.markdown(f"**Query Result for {selected_cv}:**")
                        st.markdown(result)
                else:
                    query_bulk = st.text_area("Enter bulk query", placeholder="e.g., Summarize skills across all CVs", key="bulk_query")
                    if st.button("Run Bulk Query", key="run_bulk_query"):
                        result = llm_call(f"Bulk Query: {query_bulk}", "Bulk Query")
                        st.markdown("**Bulk Query Result:**")
                        st.markdown(result)

            with llm_subtabs[1]:
                st.markdown("#### Organize - CV - In Folder")
                st.info("Organize CVs into folders based on criteria using LLM.")

                organize_criteria = st.selectbox("Organize by", ["Skills", "Experience", "Industry", "Location"], key="organize_criteria")
                folder_name = st.text_input("Folder Name", placeholder="e.g., Python_Developers", key="folder_name")
                if st.button("Create Folder & Organize", key="organize_cvs"):
                    with st.spinner("Organizing CVs..."):
                        time.sleep(2)
                    st.success(f"✅ CVs organized into folder '{folder_name}' based on {organize_criteria}")
                    st.info("Folder created with organized CVs (mocked)")

            with llm_subtabs[2]:
                st.markdown("#### Summarise CV - Analysis")
                st.info("Generate summaries and analysis of CVs using LLM.")

                summary_type = st.selectbox("Summary Type", ["Individual CV", "Bulk Summary"], key="summary_type")
                if summary_type == "Individual CV":
                    selected_cv_summary = st.selectbox("Select CV", [cv["name"] for cv in MOCK_CVS], key="selected_cv_summary")
                    if st.button("Generate Summary", key="generate_cv_summary"):
                        summary = llm_call(f"Summarize CV: {selected_cv_summary}", "Summarize CV")
                        st.markdown(f"**Summary for {selected_cv_summary}:**")
                        st.markdown(summary)
                else:
                    if st.button("Generate Bulk Summary", key="generate_bulk_summary"):
                        bulk_summary = llm_call("Summarize all CVs in repository", "Bulk Summary")
                        st.markdown("**Bulk CV Summary:**")
                        st.markdown(bulk_summary)

    with tab4:
        st.subheader("Match CVs with JD")

        match_tabs = st.tabs([
            "a. For Specific JD - Match CVs",
            "b. Rank",
            "c. Deep Analysis",
            "d. Dump into CSV"
        ])

        with match_tabs[0]:
            st.markdown("### For Specific JD - Match CVs")
            st.info("Match CVs against a specific Job Description.")

            selected_jd_match = st.selectbox("Select Job Description", [jd['title'] for jd in MOCK_JDS], key="selected_jd_match")
            match_threshold = st.slider("Match Threshold (%)", min_value=0, max_value=100, value=70, key="match_threshold")

            if st.button("Match CVs", key="match_cvs_button"):
                with st.spinner("Matching CVs with JD..."):
                    time.sleep(2)
                # Mock matching results
                matched_cvs = []
                for cv in MOCK_CVS:
                    score = random.randint(50, 95)
                    if score >= match_threshold:
                        matched_cvs.append({
                            "CV Name": cv["name"],
                            "Skills": cv["skills"],
                            "Match Score": f"{score}%",
                            "Status": cv["status"]
                        })

                if matched_cvs:
                    st.success(f"Found {len(matched_cvs)} CVs matching {selected_jd_match} above {match_threshold}%")
                    st.dataframe(pd.DataFrame(matched_cvs), use_container_width=True)
                else:
                    st.info(f"No CVs found matching {selected_jd_match} above {match_threshold}% threshold")

        with match_tabs[1]:
            st.markdown("### Rank")
            st.info("Rank matched CVs based on various criteria.")

            ranking_criteria = st.multiselect("Select Ranking Criteria",
                                            ["Match Score", "Experience", "Skills Relevance", "Education"],
                                            default=["Match Score"], key="ranking_criteria")

            if st.button("Rank CVs", key="rank_cvs_button"):
                # Mock ranking
                ranked_cvs = []
                for i, cv in enumerate(MOCK_CVS, 1):
                    ranked_cvs.append({
                        "Rank": i,
                        "CV Name": cv["name"],
                        "Skills": cv["skills"],
                        "Score": random.randint(70, 95),
                        "Status": cv["status"]
                    })

                st.dataframe(pd.DataFrame(ranked_cvs), use_container_width=True)
                st.success("CVs ranked successfully!")

        with match_tabs[2]:
            st.markdown("### Deep Analysis")
            st.info("Perform detailed analysis for CVs against specific JDs.")

            analysis_type = st.selectbox("Select Analysis Type", ["SWOT Analysis", "Gap Analysis", "Skills Comparison"], key="analysis_type")
            selected_jd_analysis = st.selectbox("Select Job Description", [jd['title'] for jd in MOCK_JDS], key="selected_jd_analysis")
            selected_cv_analysis = st.selectbox("Select CV for Analysis", [cv["name"] for cv in MOCK_CVS], key="selected_cv_analysis")

            if st.button("Perform Deep Analysis", key="deep_analysis_button"):
                if analysis_type == "SWOT Analysis":
                    analysis_result = llm_call(f"SWOT analysis for CV: {selected_cv_analysis} vs JD: {selected_jd_analysis}", "SWOT Analysis")
                elif analysis_type == "Gap Analysis":
                    analysis_result = llm_call(f"Gap analysis for CV: {selected_cv_analysis} vs JD: {selected_jd_analysis}", "Gap Analysis")
                else:
                    analysis_result = llm_call(f"Skills comparison for CV: {selected_cv_analysis} vs JD: {selected_jd_analysis}", "Skills Comparison")

                st.markdown(f"**{analysis_type} for {selected_cv_analysis} vs {selected_jd_analysis}:**")
                st.markdown(analysis_result)

        with match_tabs[3]:
            st.markdown("### Dump into CSV")
            st.info("Extract and dump contact details of selected CVs into CSV format.")

            st.markdown("#### i. Select CVs")
            selected_cvs_download = st.multiselect("Select CVs to Extract Contact Details",
                                                 [cv["name"] for cv in MOCK_CVS],
                                                 key="selected_cvs_download")

            if selected_cvs_download:
                st.info(f"Selected {len(selected_cvs_download)} CV(s) for contact extraction")

                if st.button("Extract & Download CSV", key="extract_csv_button"):
                    # Mock contact details extraction
                    contact_data = []
                    for cv_name in selected_cvs_download:
                        contact_data.append({
                            "Name": cv_name,
                            "Email": f"{cv_name.lower().replace(' ', '.')}@example.com",
                            "Phone": f"+1-{random.randint(100,999)}-{random.randint(100,999)}-{random.randint(1000,9999)}",
                            "LinkedIn": f"https://linkedin.com/in/{cv_name.lower().replace(' ', '-')}",
                            "Location": random.choice(["New York", "San Francisco", "London", "Remote"])
                        })

                    df_contacts = pd.DataFrame(contact_data)
                    st.dataframe(df_contacts, use_container_width=True)

                    # Mock CSV download
                    csv = df_contacts.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name="matched_cv_contacts.csv",
                        mime="text/csv",
                        key="download_csv"
                    )
                    st.success("Contact details extracted and CSV ready for download!")
            else:
                st.warning("Please select at least one CV to extract contact details.")

    with tab5:
        st.subheader("Screen - Basic Screening")

        # Initialize session state for AI Chat Bot
        if 'chat_step' not in st.session_state:
            st.session_state.chat_step = 0
        if 'profile_data' not in st.session_state:
            st.session_state.profile_data = {}

        screen_tabs = st.tabs([
            "1.AI Chat Bot",
            "2.Quizz",
            "3. If all Satisfactory"
        ])

        with screen_tabs[0]:
            st.markdown("### AI Chat Bot - Profile Details Collection")
            st.info("Interactive AI-powered chat bot to collect candidate profile details systematically.")

            # Profile Details Collection Steps
            profile_steps = [
                "Current Company",
                "Current Salary",
                "Expected Salary",
                "Notice Period",
                "Notice Buy Option",
                "Current Working Location",
                "Job Location & Relocation"
            ]

            # Display current step
            current_step = st.session_state.chat_step

            if current_step < len(profile_steps):
                st.markdown(f"**Step {current_step + 1} of {len(profile_steps)}: {profile_steps[current_step]}**")

                # Step-specific input collection
                if current_step == 0:  # Current Company
                    company = st.text_input("Enter your current company name:", key="current_company")
                    if st.button("Next", key="next_company"):
                        if company:
                            st.session_state.profile_data['current_company'] = company
                            st.session_state.chat_step += 1
                            st.success("✅ Current company recorded!")
                            st.rerun()
                        else:
                            st.error("Please enter your current company name.")

                elif current_step == 1:  # Current Salary
                    salary = st.number_input("Enter your current annual salary (in INR):", min_value=0, key="current_salary")
                    if st.button("Next", key="next_salary"):
                        st.session_state.profile_data['current_salary'] = salary
                        st.session_state.chat_step += 1
                        st.success("✅ Current salary recorded!")
                        st.rerun()

                elif current_step == 2:  # Expected Salary
                    expected_salary = st.number_input("Enter your expected annual salary (in INR):", min_value=0, key="expected_salary")
                    if st.button("Next", key="next_expected_salary"):
                        st.session_state.profile_data['expected_salary'] = expected_salary
                        st.session_state.chat_step += 1
                        st.success("✅ Expected salary recorded!")
                        st.rerun()

                elif current_step == 3:  # Notice Period
                    notice_period_options = ["15 days", "30 days", "45 days", "60 days", "90 days", "Immediate"]
                    notice_period = st.selectbox("Select your notice period:", notice_period_options, key="notice_period")
                    if st.button("Next", key="next_notice_period"):
                        st.session_state.profile_data['notice_period'] = notice_period
                        st.session_state.chat_step += 1
                        st.success("✅ Notice period recorded!")
                        st.rerun()

                elif current_step == 4:  # Notice Buy Option
                    notice_buy = st.radio("Are you open to buying out your notice period?", ["Yes", "No"], key="notice_buy")
                    if notice_buy == "Yes":
                        buyout_cost = st.number_input("Buyout cost (in INR):", min_value=0, key="buyout_cost")
                        st.session_state.profile_data['notice_buy'] = f"Yes - ₹{buyout_cost}"
                    else:
                        st.session_state.profile_data['notice_buy'] = "No"
                    if st.button("Next", key="next_notice_buy"):
                        st.session_state.chat_step += 1
                        st.success("✅ Notice buy option recorded!")
                        st.rerun()

                elif current_step == 5:  # Current Working Location
                    current_location = st.text_input("Enter your current working location (City, State):", key="current_location")
                    if st.button("Next", key="next_current_location"):
                        if current_location:
                            st.session_state.profile_data['current_location'] = current_location
                            st.session_state.chat_step += 1
                            st.success("✅ Current working location recorded!")
                            st.rerun()
                        else:
                            st.error("Please enter your current working location.")

                elif current_step == 6:  # Job Location & Relocation
                    job_location = st.text_input("Enter preferred job location (City, State):", key="job_location")
                    relocation_needed = st.radio("Is relocation required for this job?", ["Yes", "No"], key="relocation_radio")

                    if relocation_needed == "Yes":
                        relocation_willing = st.radio("Are you willing to relocate?", ["Yes", "No"], key="relocation_willing")
                        if relocation_willing == "Yes":
                            relocation_assistance = st.radio("Do you need relocation assistance?", ["Yes", "No"], key="relocation_assistance")
                            st.session_state.profile_data['relocation'] = f"Willing to relocate - Assistance needed: {relocation_assistance}"
                        else:
                            st.session_state.profile_data['relocation'] = "Not willing to relocate"
                    else:
                        st.session_state.profile_data['relocation'] = "No relocation required"

                    if st.button("Complete Profile", key="complete_profile"):
                        if job_location:
                            st.session_state.profile_data['job_location'] = job_location
                            st.session_state.chat_step += 1
                            st.success("✅ Profile collection completed!")
                            st.balloons()
                        else:
                            st.error("Please enter preferred job location.")

            else:
                # Profile completed - show summary
                st.markdown("### 🎉 Profile Collection Completed!")
                st.markdown("**Collected Profile Details:**")

                profile_summary = pd.DataFrame(list(st.session_state.profile_data.items()), columns=['Field', 'Value'])
                profile_summary['Value'] = profile_summary['Value'].astype(str)
                st.dataframe(profile_summary, use_container_width=True)

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Download Profile as CSV", key="download_profile"):
                        csv_profile = profile_summary.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_profile,
                            file_name="candidate_profile.csv",
                            mime="text/csv",
                            key="download_profile_csv"
                        )
                with col2:
                    if st.button("Start New Collection", key="reset_profile"):
                        st.session_state.chat_step = 0
                        st.session_state.profile_data = {}
                        st.success("Profile collection reset!")
                        st.rerun()

            # Progress indicator
            progress = min(current_step / len(profile_steps), 1.0)
            st.progress(progress)
            st.caption(f"Progress: {current_step}/{len(profile_steps)} steps completed")

        with screen_tabs[1]:
            st.markdown("### Quizz - Technical Skills Assessment")
            st.info("AI-powered quiz to assess technical skills, projects, and key roles.")

            # Initialize quiz session state
            if 'quiz_step' not in st.session_state:
                st.session_state.quiz_step = 0
            if 'quiz_responses' not in st.session_state:
                st.session_state.quiz_responses = {}
            if 'quiz_candidate' not in st.session_state:
                st.session_state.quiz_candidate = None

            # Select candidate for quiz
            selected_candidate = st.selectbox("Select Candidate for Quiz Assessment:",
                                            [cv["name"] for cv in MOCK_CVS],
                                            key="quiz_candidate_select")

            if selected_candidate != st.session_state.quiz_candidate:
                st.session_state.quiz_candidate = selected_candidate
                st.session_state.quiz_step = 0
                st.session_state.quiz_responses = {}

            if selected_candidate:
                quiz_steps = [
                    "Duration of experience in Key Skills",
                    "Projects Done - Brief Description",
                    "Roles & Responsibilities - At Each Company",
                    "Achievements & Key Roles - Brief"
                ]

                current_quiz_step = st.session_state.quiz_step

                if current_quiz_step < len(quiz_steps):
                    st.markdown(f"**Quiz Step {current_quiz_step + 1} of {len(quiz_steps)}: {quiz_steps[current_quiz_step]}**")

                    # Step-specific quiz questions
                    if current_quiz_step == 0:  # Duration of experience in Key Skills
                        st.markdown("**1. Duration of Experience in Key Skills**")
                        key_skills = st.multiselect("Select key skills you have experience in:",
                                                  ["Python", "JavaScript", "AWS", "Docker", "Kubernetes", "React", "SQL", "Machine Learning"],
                                                  key="key_skills")

                        skill_experience = {}
                        for skill in key_skills:
                            years = st.slider(f"Years of experience in {skill}:", 0, 20, 2, key=f"exp_{skill}")
                            skill_experience[skill] = years

                        if st.button("Next", key="next_skill_duration"):
                            st.session_state.quiz_responses['key_skills_experience'] = skill_experience
                            st.session_state.quiz_step += 1
                            st.success("✅ Skills experience recorded!")
                            st.rerun()

                    elif current_quiz_step == 1:  # Projects Done - Brief
                        st.markdown("**2. Projects Done - Brief Description**")
                        st.info("Describe 2-3 key projects you've worked on.")

                        project_count = st.number_input("Number of projects to describe:", min_value=1, max_value=5, value=2, key="project_count")

                        projects = []
                        for i in range(project_count):
                            with st.expander(f"Project {i+1}"):
                                project_name = st.text_input(f"Project {i+1} Name:", key=f"project_name_{i}")
                                project_desc = st.text_area(f"Brief Description of Project {i+1}:", key=f"project_desc_{i}")
                                technologies = st.text_input(f"Technologies used in Project {i+1}:", key=f"project_tech_{i}")
                                if project_name and project_desc:
                                    projects.append({
                                        "name": project_name,
                                        "description": project_desc,
                                        "technologies": technologies
                                    })

                        if st.button("Next", key="next_projects"):
                            if projects:
                                st.session_state.quiz_responses['projects'] = projects
                                st.session_state.quiz_step += 1
                                st.success("✅ Projects recorded!")
                                st.rerun()
                            else:
                                st.error("Please describe at least one project.")

                    elif current_quiz_step == 2:  # Roles & Responsibilities
                        st.markdown("**3. Roles & Responsibilities - At Each Company**")
                        st.info("Describe your roles and responsibilities at each company you've worked for.")

                        company_count = st.number_input("Number of companies to describe:", min_value=1, max_value=5, value=2, key="company_count")

                        company_roles = []
                        for i in range(company_count):
                            with st.expander(f"Company {i+1}"):
                                company_name = st.text_input(f"Company {i+1} Name:", key=f"company_name_{i}")
                                role_title = st.text_input(f"Your Role/Title at Company {i+1}:", key=f"role_title_{i}")
                                responsibilities = st.text_area(f"Key Responsibilities at Company {i+1}:", key=f"responsibilities_{i}")
                                duration = st.text_input(f"Duration at Company {i+1} (e.g., 2 years):", key=f"duration_{i}")
                                if company_name and role_title:
                                    company_roles.append({
                                        "company": company_name,
                                        "role": role_title,
                                        "responsibilities": responsibilities,
                                        "duration": duration
                                    })

                        if st.button("Next", key="next_roles"):
                            if company_roles:
                                st.session_state.quiz_responses['company_roles'] = company_roles
                                st.session_state.quiz_step += 1
                                st.success("✅ Roles and responsibilities recorded!")
                                st.rerun()
                            else:
                                st.error("Please describe at least one company role.")

                    elif current_quiz_step == 3:  # Achievements & Key Roles
                        st.markdown("**4. Achievements & Key Roles - Brief**")
                        st.info("Highlight your key achievements and roles.")

                        achievements = st.text_area("Key Achievements (brief):", height=100, key="achievements")
                        key_roles = st.text_area("Key Roles Played (brief):", height=100, key="key_roles")

                        if st.button("Complete Quiz", key="complete_quiz"):
                            if achievements and key_roles:
                                st.session_state.quiz_responses['achievements'] = achievements
                                st.session_state.quiz_responses['key_roles'] = key_roles
                                st.session_state.quiz_step += 1
                                st.success("✅ Quiz completed successfully!")
                                st.balloons()
                            else:
                                st.error("Please fill in both achievements and key roles.")

                else:
                    # Quiz completed - show results and next steps
                    st.markdown("### 🎉 Quiz Assessment Completed!")
                    st.markdown(f"**Candidate: {selected_candidate}**")

                    # Display quiz responses
                    st.markdown("**Quiz Responses Summary:**")
                    quiz_summary = []
                    for key, value in st.session_state.quiz_responses.items():
                        if key == 'key_skills_experience':
                            skills_str = ", ".join([f"{skill}: {years} years" for skill, years in value.items()])
                            quiz_summary.append(["Key Skills Experience", skills_str])
                        elif key == 'projects':
                            projects_str = "\n".join([f"- {p['name']}: {p['description'][:50]}..." for p in value])
                            quiz_summary.append(["Projects", projects_str])
                        elif key == 'company_roles':
                            roles_str = "\n".join([f"- {r['company']}: {r['role']} ({r['duration']})" for r in value])
                            quiz_summary.append(["Company Roles", roles_str])
                        else:
                            quiz_summary.append([key.replace('_', ' ').title(), str(value)[:100] + "..." if len(str(value)) > 100 else str(value)])

                    quiz_df = pd.DataFrame(quiz_summary, columns=['Category', 'Details'])
                    st.dataframe(quiz_df, use_container_width=True)

                    # Next steps based on satisfactory performance
                    st.markdown("---")
                    st.markdown("### 3. Next Steps")

                    satisfaction_level = st.selectbox("Overall Assessment:",
                                                    ["Highly Satisfactory", "Satisfactory", "Needs Improvement", "Not Satisfactory"],
                                                    key="satisfaction_level")

                    if satisfaction_level in ["Highly Satisfactory", "Satisfactory"]:
                        st.success("✅ Candidate qualifies for next round!")

                        # Schedule next round
                        st.markdown("**a. Schedule for Next Round**")
                        round_type = st.selectbox("Select Next Round Type:",
                                                ["Technical Round", "Face to Face Round", "AI Round"],
                                                key="round_type")

                        col1, col2 = st.columns(2)
                        with col1:
                            next_date = st.date_input("Interview Date", key="next_date")
                            next_time = st.time_input("Interview Time", key="next_time")
                        with col2:
                            interviewer = st.text_input("Interviewer Name", key="next_interviewer")
                            meeting_link = st.text_input("Meeting Link", placeholder="https://meet.google.com/...", key="next_meeting_link")

                        if st.button("Schedule Interview", key="schedule_next_round"):
                            st.success(f"✅ {round_type} scheduled for {next_date} at {next_time}")
                            st.info("📧 Interview details sent to candidate via email (mocked)")
                            st.info("📅 Added to calendar (agentic AI - mocked)")

                        # Analysis and Ranking
                        st.markdown("---")
                        st.markdown("**c. Analysis and Ranking**")

                        # Mock AI analysis
                        ai_score = random.randint(75, 95)
                        st.metric("AI Match Score", f"{ai_score}%")

                        # Ranking criteria
                        ranking_factors = {
                            "Technical Skills": random.randint(70, 95),
                            "Project Experience": random.randint(75, 95),
                            "Role Fit": random.randint(70, 90),
                            "Communication": random.randint(75, 95)
                        }

                        st.markdown("**Detailed Scoring:**")
                        for factor, score in ranking_factors.items():
                            st.write(f"- {factor}: {score}%")

                        overall_score = sum(ranking_factors.values()) / len(ranking_factors)
                        st.metric("Overall Candidate Score", f"{overall_score:.1f}%")

                    else:
                        st.error("❌ Candidate does not qualify for next round based on current assessment.")

                    # CSV Export
                    st.markdown("---")
                    st.markdown("**d. Export Contact Details**")

                    if st.button("Generate Contact Details CSV", key="export_contacts"):
                        # Mock contact details with CV links
                        contact_data = {
                            "Name": selected_candidate,
                            "Email": f"{selected_candidate.lower().replace(' ', '.')}@example.com",
                            "Phone": f"+91-{random.randint(70000,99999)}-{random.randint(1000,9999)}",
                            "Brief_Profile": f"Experience: {random.randint(3,8)} years, Skills: {', '.join(random.sample(['Python', 'AWS', 'React', 'ML'], 2))}",
                            "Match_Score_AI": f"{random.randint(75,95)}%",
                            "CV_Link": f"https://drive.google.com/file/d/mock_cv_{selected_candidate.replace(' ', '_')}/view"
                        }

                        contact_df = pd.DataFrame([contact_data])
                        st.dataframe(contact_df, use_container_width=True)

                        csv_contacts = contact_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv_contacts,
                            file_name=f"{selected_candidate.replace(' ', '_')}_contact_details.csv",
                            mime="text/csv",
                            key="download_contacts_csv"
                        )

                        st.success("Contact details exported!")

                    # Reset quiz
                    if st.button("Start New Quiz Assessment", key="reset_quiz"):
                        st.session_state.quiz_step = 0
                        st.session_state.quiz_responses = {}
                        st.session_state.quiz_candidate = None
                        st.success("Quiz assessment reset!")
                        st.rerun()

                # Quiz progress indicator
                quiz_progress = min(current_quiz_step / len(quiz_steps), 1.0)
                st.progress(quiz_progress)
                st.caption(f"Quiz Progress: {current_quiz_step}/{len(quiz_steps)} steps completed")

        with screen_tabs[2]:
            st.markdown("### 3. If all Satisfactory")

            # 1. Schedule for Tech Round or Face to Face round or AI Round
            st.markdown("#### 1. Schedule for Tech Round or Face to Face round or AI Round")

            # Automatically consider all candidates as satisfactory for scheduling
            satisfactory_candidates = [cv["name"] for cv in MOCK_CVS]

            if satisfactory_candidates:
                round_type = st.selectbox(
                    "Select Round Type",
                    ["Tech Round", "Face to Face Round", "AI Round"],
                    key="round_type_satisfactory"
                )

                col1, col2 = st.columns(2)
                with col1:
                    schedule_date = st.date_input("Interview Date", key="schedule_date")
                    schedule_time = st.time_input("Interview Time", key="schedule_time")
                with col2:
                    interviewer = st.text_input("Interviewer Name", key="interviewer_satisfactory")
                    meeting_link = st.text_input("Meeting Link", placeholder="https://meet.google.com/...", key="meeting_link_satisfactory")

                if st.button("Schedule Round", key="schedule_round"):
                    st.success(f"✅ {round_type} scheduled for selected candidates on {schedule_date} at {schedule_time}")
                    st.info("📧 Interview details sent to candidates via email (mocked)")
                    st.info("📅 Added to calendar (agentic AI - mocked)")

            # b. Schedule & Conduct
            st.markdown("#### b. Schedule & Conduct")

            st.markdown("##### i. Email - add to calendar (Agentic)")
            st.info("Automated email scheduling and calendar integration for interviews.")

            # Mock email and calendar integration
            if st.button("Send Interview Emails & Add to Calendar", key="send_emails_calendar"):
                st.success("✅ Interview emails sent and calendar events created!")
                st.info("Agentic AI handled email scheduling and calendar integration (mocked)")

            # c. Analyse and Filter Candidate / Rank Candidate - All So far
            st.markdown("#### c. Analyse and Filter Candidate / Rank Candidate - All So far")

            st.markdown("##### i. Match Basic Query and Response with Expectations")

            st.markdown("###### 1. Give Score for each Candidate and Evaluate")

            # Mock analysis and scoring
            candidate_scores = []
            for candidate in satisfactory_candidates:
                score = random.randint(75, 95)
                candidate_scores.append({
                    "Candidate": candidate,
                    "Score": score,
                    "Evaluation": "Strong technical skills" if score > 85 else "Good fit with some areas for improvement"
                })

            if candidate_scores:
                df_scores = pd.DataFrame(candidate_scores)
                st.dataframe(df_scores, use_container_width=True)

                # Ranking
                df_scores = df_scores.sort_values("Score", ascending=False)
                st.markdown("**Ranked Candidates:**")
                for idx, row in df_scores.iterrows():
                    st.write(f"{idx+1}. {row['Candidate']} - Score: {row['Score']}%")

            # d. Download of Extract Key Contact Details of match - Dump into CSV
            st.markdown("#### d. Download of Extract Key Contact Details of match - Dump into CSV")

            # Automatically export all satisfactory candidates
            selected_candidates_csv = satisfactory_candidates
            st.info(f"Will export contact details for {len(selected_candidates_csv)} candidate{'s' if len(selected_candidates_csv) > 1 else ''}")

            if st.button("Generate Contact Details CSV", key="generate_csv_satisfactory"):
                    # Mock contact details
                    export_data = []
                    for candidate_name in selected_candidates_csv:
                        candidate_info = next((c for c in MOCK_CVS if c["name"] == candidate_name), None)
                        if candidate_info:
                            contact_data = {
                                "Name": candidate_name,
                                "Email": f"{candidate_name.lower().replace(' ', '.')}@example.com",
                                "Phone": f"+91-{random.randint(70000,99999)}-{random.randint(1000,9999)}",
                                "Brief_Profile_Edu_Exp": f"Experience: {random.randint(3,8)} years, Skills: {candidate_info['skills']}, Education: {random.choice(['B.Tech', 'M.Tech', 'MCA', 'BCA'])}",
                                "Match_Score_AI": f"{random.randint(75,95)}%",
                                "Link_of_CVs_Drive": f"https://drive.google.com/file/d/mock_cv_{candidate_name.replace(' ', '_')}/view"
                            }
                            export_data.append(contact_data)

                    df_export = pd.DataFrame(export_data)
                    st.dataframe(df_export, use_container_width=True)

                    csv_export = df_export.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_export,
                        file_name="satisfactory_candidates_contact_details.csv",
                        mime="text/csv",
                        key="download_csv_satisfactory"
                    )

                    st.success("Contact details exported successfully!")

                    # i. Select CVs - Open the Link
                    st.markdown("##### i. Select CVs - Open the Link")
                    selected_cv_link = st.selectbox(
                        "Select CV to open link:",
                        [f"{data['Name']} - {data['Link_of_CVs_Drive']}" for data in export_data],
                        key="selected_cv_link_satisfactory"
                    )

                    if selected_cv_link:
                        cv_link = selected_cv_link.split(" - ")[1]
                        st.markdown(f"[🔗 Open CV Link]({cv_link})")

    with tab6:
        st.subheader("Candidate Profile Track")

        # 1. Select JD
        st.markdown("### 1. Select JD")
        selected_jd_track = st.selectbox("Select Job Description", [jd['title'] for jd in MOCK_JDS], key="selected_jd_track")

        # i. Applied Candidate
        st.markdown("#### i. Applied Candidate")
        st.info("View candidates who have applied for the selected JD.")

        # Mock applied candidates
        applied_candidates = []
        for cv in MOCK_CVS:
            applied_candidates.append({
                "Candidate Name": cv["name"],
                "Applied Date": "2025-11-01",
                "Skills": cv["skills"],
                "Status": cv["status"],
                "Match Score": f"{random.randint(70, 95)}%"
            })

        if applied_candidates:
            st.dataframe(pd.DataFrame(applied_candidates), use_container_width=True)
            st.info(f"Total applications: {len(applied_candidates)}")
        else:
            st.info("No candidates have applied yet.")

        # ii. Tracking Progress of Each Candidate
        st.markdown("#### ii. Tracking Progress of Each Candidate")
        st.info("Track the progress of candidates through the hiring pipeline.")

        # Define stages
        stages = [
            "1. Applied",
            "2. Basic Screening & Selected for 1st round",
            "3. Schedule AI Round (Tech Round)",
            "4. Schedule AI Round (HR)",
            "Selected or Rejected - for Face to Face Round etc"
        ]

        # Mock progress data
        progress_data = []
        for candidate in applied_candidates:
            current_stage = random.choice(stages)
            progress_data.append({
                "Candidate": candidate["Candidate Name"],
                "Current Stage": current_stage,
                "Last Updated": "2025-11-03",
                "Next Action": "Schedule Interview" if "Selected" in current_stage else "Review Application",
                "Comments": f"Strong {candidate['Skills'].split(',')[0]} skills" if random.choice([True, False]) else "Needs further evaluation"
            })

        df_progress = pd.DataFrame(progress_data)
        st.dataframe(df_progress, use_container_width=True)

        # Progress visualization
        st.markdown("---")
        st.markdown("**Pipeline Overview:**")
        stage_counts = df_progress["Current Stage"].value_counts()
        st.bar_chart(stage_counts)

        # Update progress
        st.markdown("---")
        st.markdown("**Update Candidate Progress:**")
        candidate_to_update = st.selectbox("Select Candidate", [c["Candidate Name"] for c in applied_candidates], key="candidate_to_update")
        new_stage = st.selectbox("Update to Stage", stages, key="new_stage")
        update_notes = st.text_area("Update Notes", key="update_notes")

        if st.button("Update Progress", key="update_progress"):
            st.success(f"✅ Progress updated for {candidate_to_update} to '{new_stage}'")
            st.info("Update logged in system (mocked)")

        # iv. Download of Extract Key Contact Details of match - Dump into CSV
        st.markdown("#### iv. Download of Extract Key Contact Details of match - Dump into CSV")

        selected_candidates_export = st.multiselect(
            "Select Candidates to Export Contact Details",
            [c["Candidate Name"] for c in applied_candidates],
            key="selected_candidates_export"
        )

        if selected_candidates_export:
            st.info(f"Selected {len(selected_candidates_export)} candidate{'s' if len(selected_candidates_export) > 1 else ''} for contact export")

            if st.button("Generate Contact Details CSV", key="generate_contact_csv_tab6"):
                # Mock contact details
                export_data = []
                for candidate_name in selected_candidates_export:
                    candidate_info = next((c for c in applied_candidates if c["Candidate Name"] == candidate_name), None)
                    if candidate_info:
                        contact_data = {
                            "Name": candidate_name,
                            "Email": f"{candidate_name.lower().replace(' ', '.')}@example.com",
                            "Phone": f"+91-{random.randint(70000,99999)}-{random.randint(1000,9999)}",
                            "Brief_Profile_Edu_Exp": f"Experience: {random.randint(3,8)} years, Skills: {candidate_info['Skills']}, Education: {random.choice(['B.Tech', 'M.Tech', 'MCA', 'BCA'])}",
                            "Match_Score_AI": candidate_info["Match Score"],
                            "Link_of_CVs_Drive": f"https://drive.google.com/file/d/mock_cv_{candidate_name.replace(' ', '_')}/view"
                        }
                        export_data.append(contact_data)

                df_export = pd.DataFrame(export_data)
                st.dataframe(df_export, use_container_width=True)

                csv_export = df_export.to_csv(index=False)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_export,
                    file_name=f"candidates_contact_details_{selected_jd_track.replace(' ', '_')}.csv",
                    mime="text/csv",
                    key="download_contact_csv_tab6"
                )

                st.success("Contact details exported successfully!")
        else:
            st.warning("Please select at least one candidate to export contact details.")



# --- Main App Execution ---

def main():
    """Main routing function based on authentication state."""
    # API key configuration
    with st.sidebar:
        st.text_input("Groq API Key", type="password", key="api_key")

    if not st.session_state.authenticated:
        login_signup_page()
    else:
        # User is authenticated, route to the correct dashboard
        if st.session_state.role == "admin":
            admin_dashboard()
        elif st.session_state.role == "candidate":
            candidate_dashboard()
        elif st.session_state.role == "hiring_company":
            hiring_company_dashboard()

if __name__ == "__main__":
    main()
