import streamlit as st
import os
import tempfile
import json
import re
import traceback
from datetime import date
from typing import Dict, Any, List

# ==============================================================================
# 1. DEPENDENCIES & HELPER FUNCTIONS (Stubs for demonstration)
# ==============================================================================

# --- Utility Functions ---

def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def clear_interview_state():
    """Clears all generated questions, answers, and the evaluation report."""
    st.session_state.interview_qa = []
    st.session_state.iq_output = ""
    st.session_state.evaluation_report = ""
    st.toast("Practice answers cleared.")

def generate_education_string(entry: Dict[str, str]) -> str:
    """Formats a structured education entry into a single string for storage."""
    degree = entry.get('degree', 'N/A')
    college = entry.get('college', 'N/A')
    university = entry.get('university', 'N/A')
    from_year = entry.get('from_year', 'N/A')
    to_year = entry.get('to_year', 'Present')

    if from_year == to_year:
        duration = f"({from_year})"
    elif from_year != 'N/A' and to_year != 'N/A':
        duration = f"({from_year} - {to_year})"
    else:
        duration = ""

    # Example format: "B.Tech. in Electrical Engg. (2014-2018) | College of Technology | University of Example"
    return f"{degree} {duration} | {college} | {university}"


# --- External LLM/File Logic (Simplified or Stubbed for standalone copy) ---
question_section_options = ["skills","experience", "certifications", "projects", "education"]
DEFAULT_JOB_TYPES = ["Full-time", "Contract", "Internship", "Remote", "Part-time"]
DEFAULT_ROLES = ["Software Engineer", "Data Scientist", "Product Manager", "HR Manager", "Marketing Specialist", "Operations Analyst"]

# STUBS for functions that require the actual full application code or external APIs
def extract_jd_from_linkedin_url(url: str) -> str:
    """Stub: Simulates JD content extraction."""
    return f"--- Simulated JD for: {url}\n\nJob Description content extracted from LinkedIn URL. This includes role details, requirements, and company information."

def extract_jd_metadata(jd_text):
    """Stub: Simulates extraction of structured metadata."""
    # Simple logic to return different data based on content to make the dashboard dynamic
    if "Software Engineer" in jd_text:
        return {"role": "Software Engineer", "job_type": "Full-time", "key_skills": ["Python", "Flask", "AWS", "SQL", "CI/CD"]}
    elif "Data Scientist" in jd_text:
        return {"role": "Data Scientist", "job_type": "Contract", "key_skills": ["Python", "Machine Learning", "TensorFlow", "Pandas", "Statistics"]}
    return {"role": "General Analyst", "job_type": "Full-time", "key_skills": ["Python", "SQL", "Cloud"]}

def parse_and_store_resume(file_input, file_name_key='default', source_type='file'):
    """Stub: Simulates parsing and stores results into a structure."""
    if st.session_state.get('parsed', {}).get('name') and st.session_state.parsed.get('name') != "":
          return {"parsed": st.session_state.parsed, "full_text": st.session_state.full_text, "excel_data": None, "name": st.session_state.parsed['name']}

    # Placeholder data for a fresh parse
    if source_type == 'file':
        name_from_file = getattr(file_input, 'name', 'Uploaded_Resume').split('.')[0].replace('_', ' ')
    else:
        name_from_file = "Parsed Text CV"

    parsed_data = {
        "name": name_from_file, 
        "email": "candidate@example.com", 
        "phone": "555-123-4567",
        "linkedin": "linkedin.com/in/candidate", 
        "github": "github.com/candidate",
        "skills": ["Python", "SQL", "Streamlit", "Data Analysis", "Git"], 
        "experience": ["5 years at TechCorp as a Data Analyst, focusing on ETL and reporting."], 
        "education": [
            "M.Sc. Computer Science (2016 - 2018) | University of Excellence | City University",
            "B.Tech. Information Technology (2012 - 2016) | College of Engineering | State University"
        ], 
        "certifications": ["AWS Certified Cloud Practitioner"], 
        "projects": ["Built this Streamlit Dashboard"], 
        "strength": ["Problem Solver", "Quick Learner"], 
        "personal_details": "Highly motivated and results-oriented professional."
    }
    
    # Create a placeholder full_text 
    compiled_text = ""
    for k, v in parsed_data.items():
        if v:
            compiled_text += f"{k.replace('_', ' ').title()}:\n"
            if isinstance(v, list):
                compiled_text += "\n".join([f"- {item}" for item in v]) + "\n\n"
            else:
                compiled_text += str(v) + "\n\n"

    return {"parsed": parsed_data, "full_text": compiled_text, "excel_data": None, "name": parsed_data['name']}

def qa_on_resume(question):
    """Stub: Simulates Q&A on resume."""
    if "skills" in question.lower():
        return f"Based on the resume, the key skills are: {', '.join(st.session_state.parsed.get('skills', ['No skills found']))}. The candidate has a strong background in data tools."
    return f"Based on the resume, the answer to '{question}' is: [Simulated Answer - Check experience/projects section for details]."

def qa_on_jd(question, selected_jd_name):
    """Stub: Simulates Q&A on JD."""
    return f"Based on the JD '{selected_jd_name}', the answer to '{question}' is: [Simulated Answer - The JD content specifies a 5+ years experience requirement and mandatory Python/SQL skills]."

def evaluate_jd_fit(job_description, parsed_json):
    """Stub: Simulates JD fit evaluation."""
    # Use random score for variation
    import random
    score = random.randint(5, 9)
    skills = random.randint(60, 95)
    experience = random.randint(50, 90)
    
    return f"""Overall Fit Score: {score}/10
--- Section Match Analysis ---
Skills Match: {skills}%
Experience Match: {experience}%
Education Match: 80%

Strengths/Matches:
- Candidate's Python and SQL skills ({skills}%) are an excellent match for this JD.
- Experience ({experience}%) is relevant, though perhaps slightly under the ideal level.

Gaps/Areas for Improvement:
- Needs more specific experience in the [Niche Technology] mentioned in the JD.
- The resume summary could be tailored more closely to the [Specific Industry] focus of this role.

Overall Summary: This is a **Strong** fit. Focus on experience in the interview.
"""

def generate_interview_questions(parsed_json, section):
    """Stub: Simulates interview question generation."""
    return f"""[Behavioral]
Q1: Tell me about a time you applied your strongest skill, **{parsed_json.get('skills', ['No skill'])[0]}**, to solve a major problem.
Q2: Describe a project where your work in the **{section}** section directly led to a quantifiable business outcome.
[Technical]
Q3: How do you handle a scenario where a tool in your **{section}** section fails in production?
Q4: What is the most challenging concept you learned in your **{section}** area?
[General]
Q5: Why are you looking to move from your current role/studies?
"""

def evaluate_interview_answers(qa_list, parsed_json):
    """Stub: Simulates interview answer evaluation."""
    
    total_score = len(qa_list) * 7 # Average score for simulation
    
    feedback_parts = ["## Evaluation Results"]
    for i, qa_item in enumerate(qa_list):
        feedback_parts.append(f"""
### Question {i+1}: {qa_item['question']}
Score: 7/10
Feedback:
- **Clarity & Accuracy:** The answer for this question was good, addressing the core topic.
- **Improvements:** Try to use the **STAR** (Situation, Task, Action, Result) method, especially for behavioral questions. Quantify your results.
""")
        
    feedback_parts.append(f"""
---
## Final Assessment
Total Score: {total_score}/{len(qa_list) * 10}
Overall Summary: The candidate shows **Good** fundamental knowledge. To score higher, better integrate answers with accomplishments listed in the resume (e.g., mention specific projects).
""")
    
    return "\n".join(feedback_parts)

def generate_cv_html(parsed_data):
    """Stub: Simulates CV HTML generation."""
    skills_list = "".join([f"<li>{s}</li>" for s in parsed_data.get('skills', [])])
    education_list = "".join([f"<li>{e}</li>" for e in parsed_data.get('education', [])])
    return f"""
    <html>
    <head>
        <title>{parsed_data.get('name', 'CV Preview')}</title>
        <style>body{{font-family: Arial, sans-serif; margin: 40px;}} h1{{color: #2e6c80; border-bottom: 2px solid #2e6c80;}} h2{{color: #3d99b1;}} ul{{list-style-type: none; padding: 0;}}</style>
    </head>
    <body>
        <h1>{parsed_data.get('name', 'CV Preview')}</h1>
        <p>Email: {parsed_data.get('email', 'N/A')} | Phone: {parsed_data.get('phone', 'N/A')}</p>
        <p>LinkedIn: <a href="{parsed_data.get('linkedin', '#')}">{parsed_data.get('linkedin', 'N/A')}</a></p>
        
        <h2>Key Skills</h2>
        <ul>{skills_list}</ul>
        
        <h2>Experience</h2>
        <p>{' | '.join(parsed_data.get('experience', ['No experience listed']))}</p>
        
        <h2>Education</h2>
        <ul>{education_list}</ul>
        
        <p>Generated by AI Dashboard on {date.today()}</p>
    </body>
    </html>
    """

def format_parsed_json_to_markdown(parsed_data):
    """Stub: Simulates CV Markdown generation."""
    md = f"# **{parsed_data.get('name', 'CV Preview').upper()}**\n"
    md += f"**Contact:** {parsed_data.get('email', 'N/A')} | {parsed_data.get('phone', 'N/A')} | [LinkedIn]({parsed_data.get('linkedin', '#')})\n"
    md += "\n"
    md += f"## **SUMMARY**\n---\n"
    md += parsed_data.get('personal_details', 'No summary provided.') + "\n\n"
    md += "## **SKILLS**\n---\n"
    md += "- " + "\n- ".join(parsed_data.get('skills', ['No skills listed']))
    md += "\n\n## **EXPERIENCE**\n---\n"
    md += "- " + "\n- ".join(parsed_data.get('experience', ['No experience listed']))
    md += "\n\n## **EDUCATION**\n---\n"
    md += "- " + "\n- ".join(parsed_data.get('education', ['No education listed']))
    return md

# ==============================================================================
# 2. TAB CONTENT FUNCTIONS (Provided + Stubs)
# ==============================================================================

def resume_parsing_tab_content():
    st.header("📄 Resume Parsing")
    st.info("Upload your CV/Resume (PDF, DOCX, TXT) to automatically extract structured data or paste raw text.")
    
    tab_upload, tab_paste = st.tabs(["📤 Upload File", "📋 Paste Text"])
    
    with tab_upload:
        uploaded_file = st.file_uploader(
            "Upload your Resume/CV", 
            type=['pdf', 'docx', 'txt'], 
            accept_multiple_files=False,
            key="candidate_resume_upload"
        )
        if uploaded_file:
            st.warning("Parsing is a stub in this demo, but the file content is being registered.")
            # Simulate parsing
            with st.spinner(f"Parsing {uploaded_file.name}..."):
                # In a real app, you'd process the file content here
                parse_results = parse_and_store_resume(uploaded_file, file_name_key=uploaded_file.name, source_type='file')
                st.session_state.parsed = parse_results['parsed']
                st.session_state.full_text = parse_results['full_text']
                st.session_state.cv_form_data = st.session_state.parsed.copy()
            st.success(f"✅ Resume '{st.session_state.parsed['name']}' parsed and loaded. Go to the **CV Management** tab to review/edit the data.")
    
    with tab_paste:
        pasted_text = st.text_area(
            "Paste your CV/Resume raw text here", 
            height=300, 
            value=st.session_state.pasted_cv_text,
            key="pasted_cv_text_area"
        )
        parse_text_button = st.button("Parse Pasted Text", type="primary", use_container_width=True)
        
        if parse_text_button:
            if pasted_text:
                st.session_state.pasted_cv_text = pasted_text # Save for persistence
                with st.spinner("Parsing pasted text..."):
                    parse_results = parse_and_store_resume(pasted_text, file_name_key='pasted_text', source_type='text')
                    st.session_state.parsed = parse_results['parsed']
                    st.session_state.full_text = parse_results['full_text']
                    st.session_state.cv_form_data = st.session_state.parsed.copy()
                st.success("✅ Pasted text parsed and loaded. Go to the **CV Management** tab to review/edit the data.")
            else:
                st.error("Please paste some text into the box.")

def cv_management_tab_content():
    st.header("📝 Prepare Your CV")
    st.markdown("### 1. Form Based CV Builder")
    st.info("Fill out the details below to generate a parsed CV that can be used immediately for matching and interview prep, or start by parsing a file in the 'Resume Parsing' tab.")

    # Initialize the parsed data if not already existing
    default_parsed = {
        "name": "", "email": "", "phone": "", "linkedin": "", "github": "",
        "skills": [], "experience": [], "education": [], "certifications": [], 
        "projects": [], "strength": [], "personal_details": ""
    }
    
    if "cv_form_data" not in st.session_state:
        # Load from parsed if it exists
        if st.session_state.get('parsed', {}).get('name') and st.session_state.parsed.get('name') != "":
            st.session_state.cv_form_data = st.session_state.parsed.copy()
        else:
            st.session_state.cv_form_data = default_parsed
            
    # CRITICAL: Ensure education is a list of strings for compatibility
    if not isinstance(st.session_state.cv_form_data.get('education'), list):
          st.session_state.cv_form_data['education'] = []

    
    # --- CV Builder Form (Main Sections) ---
    with st.form("cv_builder_form"):
        st.subheader("Personal & Contact Details")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.cv_form_data['name'] = st.text_input(
                "Full Name", 
                value=st.session_state.cv_form_data['name'], 
                key="cv_name"
            )
        with col2:
            st.session_state.cv_form_data['email'] = st.text_input(
                "Email Address", 
                value=st.session_state.cv_form_data['email'], 
                key="cv_email"
            )
        with col3:
            st.session_state.cv_form_data['phone'] = st.text_input(
                "Phone Number", 
                value=st.session_state.cv_form_data['phone'], 
                key="cv_phone"
            )
        
        col4, col5 = st.columns(2)
        with col4:
            st.session_state.cv_form_data['linkedin'] = st.text_input(
                "LinkedIn Profile URL", 
                value=st.session_state.cv_form_data.get('linkedin', ''), 
                key="cv_linkedin"
            )
        with col5:
            st.session_state.cv_form_data['github'] = st.text_input(
                "GitHub Profile URL", 
                value=st.session_state.cv_form_data.get('github', ''), 
                key="cv_github"
            )
        
        st.markdown("---")
        st.subheader("Summary / Personal Details")
        st.session_state.cv_form_data['personal_details'] = st.text_area(
            "Professional Summary or Personal Details (e.g., date of birth, address, nationality)", 
            value=st.session_state.cv_form_data.get('personal_details', ''), 
            height=100,
            key="cv_personal_details"
        )
        
        st.markdown("---")
        st.subheader("Technical Sections (One Item per Line)")

        skills_text = "\n".join(st.session_state.cv_form_data.get('skills', []))
        new_skills_text = st.text_area(
            "Key Skills (Technical and Soft)", 
            value=skills_text,
            height=150,
            key="cv_skills"
        )
        st.session_state.cv_form_data['skills'] = [s.strip() for s in new_skills_text.split('\n') if s.strip()]
        
        experience_text = "\n".join(st.session_state.cv_form_data.get('experience', []))
        new_experience_text = st.text_area(
            "Professional Experience (Job Roles, Companies, Dates, Key Responsibilities)", 
            value=experience_text,
            height=150,
            key="cv_experience"
        )
        st.session_state.cv_form_data['experience'] = [e.strip() for e in new_experience_text.split('\n') if e.strip()]
        
        certifications_text = "\n".join(st.session_state.cv_form_data.get('certifications', []))
        new_certifications_text = st.text_area(
            "Certifications (Name, Issuing Body, Date)", 
            value=certifications_text,
            height=100,
            key="cv_certifications"
        )
        st.session_state.cv_form_data['certifications'] = [c.strip() for c in new_certifications_text.split('\n') if c.strip()]
        
        projects_text = "\n".join(st.session_state.cv_form_data.get('projects', []))
        new_projects_text = st.text_area(
            "Projects (Name, Description, Technologies)", 
            value=projects_text,
            height=150,
            key="cv_projects"
        )
        st.session_state.cv_form_data['projects'] = [p.strip() for p in new_projects_text.split('\n') if p.strip()]
        
        strength_text = "\n".join(st.session_state.cv_form_data.get('strength', []))
        new_strength_text = st.text_area(
            "Strengths / Key Personal Qualities (One per line)", 
            value=strength_text,
            height=100,
            key="cv_strength"
        )
        st.session_state.cv_form_data['strength'] = [s.strip() for s in new_strength_text.split('\n') if s.strip()]


        submit_form_button = st.form_submit_button("Generate and Load ALL CV Data", type="primary", use_container_width=True)

    # --- Education Input Form (New Structured Input) ---
    st.markdown("---")
    st.subheader("Education (Structured Input)")
    
    # Display existing education entries
    if st.session_state.cv_form_data.get('education'):
        st.markdown("##### Current Education Entries:")
        for i, entry in enumerate(st.session_state.cv_form_data['education']):
            col_entry, col_delete = st.columns([10, 1])
            with col_entry:
                st.write(f"**{i+1}.** {entry}")
            with col_delete:
                if st.button("🗑️", key=f"delete_edu_{i}"):
                    st.session_state.cv_form_data['education'].pop(i)
                    st.success("Entry deleted. Click 'Generate and Load ALL CV Data' to save changes.")
                    st.rerun() 
        st.markdown("---")

    
    with st.form("education_add_form"):
        col_d, col_c = st.columns(2)
        with col_d:
            degree = st.text_input("Degree / Qualification", key="edu_degree")
        with col_c:
            college = st.text_input("College / Institution Name", key="edu_college")
            
        col_u, col_f, col_t = st.columns(3)
        with col_u:
            university = st.text_input("University / Board", key="edu_university")
        with col_f:
            from_year = st.text_input("From Year (e.g., 2014)", key="edu_from_year", max_chars=4)
        with col_t:
            to_year = st.text_input("To Year (e.g., 2018 or Present)", key="edu_to_year", max_chars=7)
            
        # Button logic executed AFTER the form submission
        add_edu_button = st.form_submit_button("➕ Add Education Entry", use_container_width=True)
        
        if add_edu_button:
            if degree and college and from_year:
                new_entry_dict = {
                    'degree': degree,
                    'college': college,
                    'university': university if university else "N/A",
                    'from_year': from_year,
                    'to_year': to_year if to_year else "Present"
                }
                
                # Format the entry into the required string format
                new_entry_string = generate_education_string(new_entry_dict)
                
                # Append to the list and clear inputs by rerunning
                st.session_state.cv_form_data['education'].append(new_entry_string)
                st.success(f"Education entry added: {new_entry_string}. Click 'Generate and Load ALL CV Data' above to use it for AI tools.")
                
                # Clear the education form fields by using a temporary state update and rerun
                st.session_state.edu_degree = ""
                st.session_state.edu_college = ""
                st.session_state.edu_university = ""
                st.session_state.edu_from_year = ""
                st.session_state.edu_to_year = ""
                st.rerun() 
            else:
                st.error("Please fill in at least Degree, College/Institution, and From Year for the education entry.")

    # --- FINAL SUBMISSION LOGIC (for the main form) ---
    if submit_form_button:
        if not st.session_state.cv_form_data['name'] or not st.session_state.cv_form_data['email']:
            st.error("Please fill in at least your **Full Name** and **Email Address**.")
            return

        st.session_state.parsed = st.session_state.cv_form_data.copy()
        
        # Create a placeholder full_text for the AI tools
        compiled_text = ""
        for k, v in st.session_state.cv_form_data.items():
            if v:
                compiled_text += f"{k.replace('_', ' ').title()}:\n"
                if isinstance(v, list):
                    compiled_text += "\n".join([f"- {item}" for item in v]) + "\n\n"
                else:
                    compiled_text += str(v) + "\n\n"
        st.session_state.full_text = compiled_text
        
        st.session_state.candidate_match_results = []
        st.session_state.interview_qa = []
        st.session_state.evaluation_report = ""

        st.success(f"✅ CV data for **{st.session_state.parsed['name']}** successfully generated and loaded! You can now use the Chatbot, Match, and Interview Prep tabs.")
        
    st.markdown("---")
    st.subheader("2. Loaded CV Data Preview and Download")
    
    if st.session_state.get('parsed', {}).get('name') and st.session_state.parsed.get('name') != "":
        
        filled_data_for_preview = {
            k: v for k, v in st.session_state.parsed.items() 
            if v and (isinstance(v, str) and v.strip() or isinstance(v, list) and v)
        }
        
        tab_markdown, tab_json, tab_pdf = st.tabs(["📝 Markdown View", "💾 JSON View", "⬇️ PDF/HTML Download"])

        with tab_markdown:
            cv_markdown_preview = format_parsed_json_to_markdown(filled_data_for_preview)
            st.markdown(cv_markdown_preview)

            st.download_button(
                label="⬇️ Download CV as Markdown (.md)",
                data=cv_markdown_preview,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_CV_Document.md",
                mime="text/markdown",
                key="download_cv_markdown_final"
            )

        with tab_json:
            st.json(st.session_state.parsed)
            st.info("This is the raw, structured data used by the AI tools.")

            json_output = json.dumps(st.session_state.parsed, indent=2)
            st.download_button(
                label="⬇️ Download CV as JSON File",
                data=json_output,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_CV_Data.json",
                mime="application/json",
                key="download_cv_json_final"
            )

        with tab_pdf:
            st.markdown("### Download CV as HTML (Print-to-PDF)")
            st.info("Click the button below to download an HTML file. Open the file in your browser and use the browser's **'Print'** function, selecting **'Save as PDF'** to create your final CV document.")
            
            html_output = generate_cv_html(filled_data_for_preview)

            st.download_button(
                label="⬇️ Download CV as Print-Ready HTML File (for PDF conversion)",
                data=html_output,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_CV_Document.html",
                mime="text/html",
                key="download_cv_html"
            )
            
            st.markdown("---")
            st.markdown("### Raw Text Data Download (for utility)")
            st.download_button(
                label="⬇️ Download All CV Data as Raw Text (.txt)",
                data=st.session_state.full_text,
                file_name=f"{st.session_state.parsed.get('name', 'Generated_CV').replace(' ', '_')}_Raw_Data.txt",
                mime="text/plain",
                key="download_cv_txt_final"
            )
            
    else:
        st.info("Please fill out the form above and click 'Generate and Load ALL CV Data' or parse a resume in the 'Resume Parsing' tab to see the preview and download options.")


def jd_management_tab_content():
    st.header("🏢 JD Management")
    st.info("Load Job Descriptions (JDs) via text or URL. Extracted metadata (Role, Skills) is used for matching and filtering.")
    
    with st.form("jd_upload_form"):
        jd_name = st.text_input("Job Title/Reference Name (e.g., 'Senior Data Engineer - J-101')", key="jd_name_input")
        jd_url = st.text_input("LinkedIn/Job Board URL (Optional)", key="jd_url_input")
        jd_text = st.text_area("Paste Full Job Description Text", height=200, key="jd_text_input")
        
        submit_jd_button = st.form_submit_button("Extract and Save JD", type="primary", use_container_width=True)

    if submit_jd_button:
        content = ""
        if jd_url:
            content += extract_jd_from_linkedin_url(jd_url)
        if jd_text:
            content += "\n\n--- PASTED JD TEXT ---\n\n" + jd_text
        
        final_content = content.strip()
        
        if final_content and jd_name:
            metadata = extract_jd_metadata(final_content)
            
            new_jd = {
                "name": jd_name,
                "content": final_content,
                "url": jd_url,
                "role": metadata.get('role', 'General Role'),
                "job_type": metadata.get('job_type', 'Full-time'),
                "key_skills": metadata.get('key_skills', []),
            }
            st.session_state.candidate_jd_list.append(new_jd)
            st.success(f"✅ Job Description '{jd_name}' saved! Extracted Role: {new_jd['role']}, Skills: {', '.join(new_jd['key_skills'][:3])}...")
            # Rerun to clear the form visually (not critical, but good UX)
            st.session_state.jd_name_input = ""
            st.session_state.jd_url_input = ""
            st.session_state.jd_text_input = ""
            st.rerun()

        else:
            st.error("Please provide a Job Title and at least the JD URL or the pasted text.")
            
    st.markdown("---")
    st.subheader(f"Saved Job Descriptions ({len(st.session_state.candidate_jd_list)})")

    if st.session_state.candidate_jd_list:
        jd_display = []
        for i, jd in enumerate(st.session_state.candidate_jd_list):
            jd_display.append({
                "ID": i + 1,
                "Job Title": jd['name'],
                "Role": jd.get('role', 'N/A'),
                "Job Type": jd.get('job_type', 'N/A'),
                "Key Skills (Top 5)": ", ".join(jd.get('key_skills', [])[:5]),
            })
            
        st.dataframe(jd_display, use_container_width=True)
        
        st.markdown("##### Manage Saved JDs")
        col_list = st.columns(3)
        with col_list[0]:
            jd_to_delete = st.number_input("Enter ID to Delete:", min_value=1, max_value=len(st.session_state.candidate_jd_list) if st.session_state.candidate_jd_list else 1, step=1, key="jd_delete_id")
        with col_list[1]:
            if st.button(f"🗑️ Delete JD {jd_to_delete}", use_container_width=True):
                st.session_state.candidate_jd_list.pop(jd_to_delete - 1)
                st.success(f"JD {jd_to_delete} deleted.")
                st.rerun()
        with col_list[2]:
            if st.button("🗑️ Clear All JDs", use_container_width=True):
                st.session_state.candidate_jd_list = []
                st.success("All JDs cleared.")
                st.rerun()
    else:
        st.info("No JDs saved yet.")

def filter_jd_tab_content():
    # Content identical to the previous response's filter_jd_tab_content
    st.header("🔍 Filter Job Descriptions by Criteria")
    st.markdown("Use the filters below to narrow down your saved Job Descriptions.")

    if not st.session_state.candidate_jd_list:
        st.info("No Job Descriptions are currently loaded. Please add JDs in the 'JD Management' tab.")
        if 'filtered_jds_display' not in st.session_state:
            st.session_state.filtered_jds_display = []
        return
    
    unique_roles = sorted(list(set(
        [item.get('role', 'General Analyst') for item in st.session_state.candidate_jd_list] + DEFAULT_ROLES
    )))
    unique_job_types = sorted(list(set(
        [item.get('job_type', 'Full-time') for item in st.session_state.candidate_jd_list] + DEFAULT_JOB_TYPES
    )))
    
    STARTER_KEYWORDS = {
        "Python", "MySQL", "GCP", "cloud computing", "ML", 
        "API services", "LLM integration", "JavaScript", "SQL", "AWS" 
    }
    
    all_unique_skills = set(STARTER_KEYWORDS)
    for jd in st.session_state.candidate_jd_list:
        valid_skills = [
            skill.strip() for skill in jd.get('key_skills', []) 
            if isinstance(skill, str) and skill.strip()
        ]
        all_unique_skills.update(valid_skills)
    
    unique_skills_list = sorted(list(all_unique_skills))
    
    if not unique_skills_list:
        unique_skills_list = ["No skills extracted from current JDs"]

    all_jd_data = st.session_state.candidate_jd_list

    with st.form(key="jd_filter_form"):
        st.markdown("### Select Filters")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            selected_skills = st.multiselect(
                "Skills Keywords (Select multiple)",
                options=unique_skills_list,
                default=st.session_state.get('last_selected_skills', []),
                key="candidate_filter_skills_multiselect", 
                help="Select one or more skills. JDs containing ANY of the selected skills will be shown."
            )
            
        with col2:
            selected_job_type = st.selectbox(
                "Job Type",
                options=["All Job Types"] + unique_job_types,
                index=0, 
                key="filter_job_type_select"
            )
            
        with col3:
            selected_role = st.selectbox(
                "Role Title",
                options=["All Roles"] + unique_roles,
                index=0, 
                key="filter_role_select"
            )

        apply_filters_button = st.form_submit_button("✅ Apply Filters", type="primary", use_container_width=True)

    if apply_filters_button:
        st.session_state.last_selected_skills = selected_skills

        filtered_jds = []
        selected_skills_lower = [k.strip().lower() for k in selected_skills]
        
        for jd in all_jd_data:
            jd_role = jd.get('role', 'General Analyst')
            jd_job_type = jd.get('job_type', 'Full-time')
            jd_key_skills = [
                s.lower() for s in jd.get('key_skills', []) 
                if isinstance(s, str) and s.strip()
            ]
            
            role_match = (selected_role == "All Roles") or (selected_role == jd_role)
            job_type_match = (selected_job_type == "All Job Types") or (selected_job_type == jd_job_type)
            
            skill_match = True
            if selected_skills_lower:
                if not any(k in jd_key_skills for k in selected_skills_lower):
                    skill_match = False
            
            if role_match and job_type_match and skill_match:
                filtered_jds.append(jd)
                
        st.session_state.filtered_jds_display = filtered_jds
        st.success(f"Filter applied! Found {len(filtered_jds)} matching Job Descriptions.")

    st.markdown("---")
    
    if 'filtered_jds_display' not in st.session_state:
        st.session_state.filtered_jds_display = []
        
    filtered_jds = st.session_state.filtered_jds_display
    
    st.subheader(f"Matching Job Descriptions ({len(filtered_jds)} found)")
    
    if filtered_jds:
        display_data = []
        for jd in filtered_jds:
            display_data.append({
                "Job Description Title": jd['name'].replace("--- Simulated JD for: ", ""),
                "Role": jd.get('role', 'N/A'),
                "Job Type": jd.get('job_type', 'N/A'),
                "Key Skills": ", ".join(jd.get('key_skills', ['N/A'])[:5]) + "...",
            })
            
        st.dataframe(display_data, use_container_width=True)

        st.markdown("##### Detailed View")
        for idx, jd in enumerate(filtered_jds, 1):
            with st.expander(f"JD {idx}: {jd['name'].replace('--- Simulated JD for: ', '')} - ({jd.get('role', 'N/A')})"):
                st.markdown(f"**Job Type:** {jd.get('job_type', 'N/A')}")
                st.markdown(f"**Extracted Skills:** {', '.join(jd.get('key_skills', ['N/A']))}")
                st.markdown("---")
                st.text(jd['content'])
    elif st.session_state.candidate_jd_list and apply_filters_button:
        st.info("No Job Descriptions match the selected criteria. Try broadening your filter selections.")
    elif st.session_state.candidate_jd_list and not apply_filters_button:
        st.info("Use the filters above and click **'Apply Filters'** to view matching Job Descriptions.")


def jd_match_tab_content():
    st.header("🎯 CV-JD Match Score")
    if not st.session_state.get('parsed', {}).get('name'):
        st.error("Please load your CV data first in the **Resume Parsing** or **CV Management** tab.")
        return
    if not st.session_state.candidate_jd_list:
        st.error("Please load at least one Job Description in the **JD Management** tab.")
        return
        
    st.info(f"Current CV Loaded: **{st.session_state.parsed['name']}**")
    
    # Select JD
    jd_options = {jd['name']: jd for jd in st.session_state.candidate_jd_list}
    selected_jd_name = st.selectbox(
        "Select Job Description for Matching:",
        options=list(jd_options.keys()),
        key="jd_match_select"
    )
    
    if selected_jd_name:
        selected_jd = jd_options[selected_jd_name]
        st.markdown(f"**Target Role:** {selected_jd.get('role', 'N/A')} | **Type:** {selected_jd.get('job_type', 'N/A')}")
        st.markdown(f"**Key Skills in JD:** {', '.join(selected_jd.get('key_skills', [])[:5])}...")
        
        match_button = st.button("Calculate CV-JD Fit Score", type="primary", use_container_width=True)
        
        if match_button:
            with st.spinner("Analyzing CV against Job Description..."):
                fit_report = evaluate_jd_fit(selected_jd['content'], st.session_state.parsed)
                st.session_state.jd_fit_output = fit_report
                st.session_state.candidate_match_results.append({
                    "jd_name": selected_jd_name,
                    "report": fit_report,
                    "timestamp": date.today().isoformat()
                })
            st.success(f"Match analysis complete for {selected_jd_name}!")
            
        st.markdown("---")
        
        st.subheader("Match Analysis Report")
        if st.session_state.jd_fit_output:
            st.markdown(st.session_state.jd_fit_output)
        else:
            st.info("Click the button above to calculate the fit score.")

def chatbot_tab_content():
    st.header("🤖 Chatbot: Q&A on CV/JD")
    
    if not st.session_state.get('parsed', {}).get('name'):
        st.error("Please load your CV data first in the **Resume Parsing** or **CV Management** tab.")
        return
        
    st.info(f"Chatbot can answer questions about your loaded CV (**{st.session_state.parsed['name']}**) and saved JDs.")
    
    tab_resume, tab_jd = st.tabs(["Ask About CV", "Ask About JD"])
    
    with tab_resume:
        st.subheader("CV Q&A")
        st.markdown("Ask a question about your resume, e.g., *'What are my key skills?'* or *'What is my work experience?'*")
        resume_question = st.text_input("Your Question about the CV:", key="resume_qa_input")
        qa_resume_button = st.button("Get CV Answer", use_container_width=True)
        
        if qa_resume_button and resume_question:
            with st.spinner("Querying CV data..."):
                st.session_state.qa_answer_resume = qa_on_resume(resume_question)
            st.markdown("##### Answer")
            st.info(st.session_state.qa_answer_resume)
        elif qa_resume_button and not resume_question:
            st.error("Please enter a question.")
            
    with tab_jd:
        st.subheader("JD Q&A")
        if not st.session_state.candidate_jd_list:
            st.warning("No JDs loaded. Go to the **JD Management** tab.")
            return

        jd_options = {jd['name']: jd for jd in st.session_state.candidate_jd_list}
        selected_jd_name = st.selectbox(
            "Select JD to query:",
            options=list(jd_options.keys()),
            key="jd_qa_select"
        )
        
        st.markdown(f"Ask a question about the JD, e.g., *'What are the mandatory experience years for {selected_jd_name}?'*")
        jd_question = st.text_input("Your Question about the JD:", key="jd_qa_input")
        qa_jd_button = st.button("Get JD Answer", use_container_width=True)
        
        if qa_jd_button and jd_question:
            with st.spinner(f"Querying JD: {selected_jd_name}..."):
                st.session_state.qa_answer_jd = qa_on_jd(jd_question, selected_jd_name)
            st.markdown("##### Answer")
            st.info(st.session_state.qa_answer_jd)
        elif qa_jd_button and not jd_question:
            st.error("Please enter a question.")


def interview_prep_tab_content():
    st.header("🎙️ Interview Preparation")
    
    if not st.session_state.get('parsed', {}).get('name'):
        st.error("Please load your CV data first in the **Resume Parsing** or **CV Management** tab.")
        return
        
    st.info(f"Prepare for your interview using questions tailored to your loaded CV (**{st.session_state.parsed['name']}**).")
    
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        selected_section = st.selectbox(
            "Focus Question Generation on which CV Section?",
            options=question_section_options,
            key="interview_section_select",
            help="Questions will be focused on this part of your background."
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True) # Spacer
        generate_button = st.button("Generate New Questions", type="primary", use_container_width=True)
    
    if generate_button:
        with st.spinner(f"Generating questions focused on {selected_section}..."):
            st.session_state.iq_output = generate_interview_questions(st.session_state.parsed, selected_section)
            st.session_state.interview_qa = [] # Reset Q&A list
        st.success(f"5 questions generated for the {selected_section} section!")
        
    st.markdown("---")
    
    st.subheader("Question & Answer Practice")
    
    if st.session_state.iq_output:
        st.markdown("##### Generated Questions:")
        questions = [q.strip() for q in re.findall(r"(Q\d+:.*?)\n", st.session_state.iq_output, re.DOTALL)]

        if not questions:
            st.warning("Could not parse questions from the LLM output.")
            questions = ["Q1: Sample Question 1", "Q2: Sample Question 2"] # Fallback

        if len(st.session_state.interview_qa) < len(questions):
            current_q_index = len(st.session_state.interview_qa)
            current_question = questions[current_q_index]
            
            with st.form(key=f"interview_q_form_{current_q_index}"):
                st.markdown(f"**{current_question}**")
                user_answer = st.text_area("Your Answer (aim for 200-300 words for practice):", height=150, key=f"user_answer_{current_q_index}")
                submit_answer = st.form_submit_button(f"Submit Answer for Question {current_q_index + 1}", use_container_width=True)
                
                if submit_answer:
                    if user_answer.strip():
                        st.session_state.interview_qa.append({
                            "question": current_question,
                            "answer": user_answer
                        })
                        st.success(f"Answer for Question {current_q_index + 1} recorded.")
                        # Rerun to advance to the next question or the evaluation
                        st.rerun()
                    else:
                        st.error("Please provide an answer before submitting.")
        
        # All questions answered, show evaluation button
        if len(st.session_state.interview_qa) == len(questions):
            st.success("All questions have been answered. Ready for Evaluation.")
            st.markdown("---")
            st.subheader("Evaluation")
            col_eval, col_clear = st.columns(2)
            with col_eval:
                evaluate_button = st.button("Get Answer Evaluation Report", type="primary", use_container_width=True)
            with col_clear:
                clear_button = st.button("Clear Q&A Data and Start Over", on_click=clear_interview_state, use_container_width=True)
            
            if evaluate_button:
                with st.spinner("Generating detailed evaluation report..."):
                    st.session_state.evaluation_report = evaluate_interview_answers(st.session_state.interview_qa, st.session_state.parsed)
                st.success("Evaluation complete!")
                
            if st.session_state.evaluation_report:
                st.markdown(st.session_state.evaluation_report)

    else:
        st.info("Click **'Generate New Questions'** to start your interview practice.")


# ==============================================================================
# 3. MAIN CANDIDATE DASHBOARD FUNCTION
# ==============================================================================

def candidate_dashboard():
    st.set_page_config(
        page_title="Candidate AI Dashboard",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    st.header("👩‍🎓 Candidate AI Dashboard")
    st.markdown("Welcome! Use the tabs below to manage your CV and access AI preparation tools.")

    # --- Session State Initialization (CRITICAL BLOCK) ---
    if 'page' not in st.session_state: st.session_state.page = "login"
    if 'parsed' not in st.session_state: st.session_state.parsed = {}
    if 'full_text' not in st.session_state: st.session_state.full_text = ""
    if 'excel_data' not in st.session_state: st.session_state.excel_data = None
    if 'qa_answer_resume' not in st.session_state: st.session_state.qa_answer_resume = ""
    if 'qa_answer_jd' not in st.session_state: st.session_state.qa_answer_jd = ""
    if 'iq_output' not in st.session_state: st.session_state.iq_output = ""
    if 'jd_fit_output' not in st.session_state: st.session_state.jd_fit_output = ""
    if 'candidate_jd_list' not in st.session_state: st.session_state.candidate_jd_list = []
    if 'candidate_match_results' not in st.session_state: st.session_state.candidate_match_results = []
    if 'candidate_uploaded_resumes' not in st.session_state: st.session_state.candidate_uploaded_resumes = []
    if 'pasted_cv_text' not in st.session_state: st.session_state.pasted_cv_text = "" 
    if 'interview_qa' not in st.session_state: st.session_state.interview_qa = [] 
    if 'evaluation_report' not in st.session_state: st.session_state.evaluation_report = ""
    if "cv_form_data" not in st.session_state: 
        st.session_state.cv_form_data = {
            "name": "", "email": "", "phone": "", "linkedin": "", "github": "",
            "skills": [], "experience": [], "education": [], "certifications": [], 
            "projects": [], "strength": [], "personal_details": ""
        }
    if "candidate_filter_skills_multiselect" not in st.session_state:
        st.session_state.candidate_filter_skills_multiselect = []
    if "filtered_jds_display" not in st.session_state:
        st.session_state.filtered_jds_display = []
    if "last_selected_skills" not in st.session_state:
        st.session_state.last_selected_skills = []
        
    # Initialize fields for the dynamic education form to prevent Rerun errors
    if "edu_degree" not in st.session_state: st.session_state.edu_degree = ""
    if "edu_college" not in st.session_state: st.session_state.edu_college = ""
    if "edu_university" not in st.session_state: st.session_state.edu_university = ""
    if "edu_from_year" not in st.session_state: st.session_state.edu_from_year = ""
    if "edu_to_year" not in st.session_state: st.session_state.edu_to_year = ""
    # --- END Session State Initialization ---

    # --- NAVIGATION BLOCK (Sidebar) ---
    with st.sidebar:
        st.header("Resume/CV Status")
        
        if st.session_state.parsed.get("name") and st.session_state.parsed.get('name') != "":
            st.success(f"Currently loaded: **{st.session_state.parsed['name']}**")
        elif st.session_state.full_text:
            st.warning("Resume content is loaded (raw text).")
        else:
            st.error("No CV data loaded. Please use the Parsing/Management tabs.")

        st.header("Job Description Status")
        st.info(f"Loaded JDs: **{len(st.session_state.candidate_jd_list)}**")
        
        st.markdown("---")
        if st.button("Clear All Practice Data", use_container_width=True):
            clear_interview_state()
            st.session_state.jd_fit_output = ""
            st.session_state.qa_answer_resume = ""
            st.session_state.qa_answer_jd = ""
            st.success("Practice data cleared.")
            st.rerun()

    # --- MAIN CONTENT TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📄 Resume Parsing", 
        "📝 CV Management", 
        "🏢 JD Management",
        "🔍 JD Filter",
        "🎯 JD Match Score",
        "🤖 Chatbot Q&A",
        "🎙️ Interview Prep"
    ])

    with tab1:
        resume_parsing_tab_content()
    
    with tab2:
        cv_management_tab_content()

    with tab3:
        jd_management_tab_content()

    with tab4:
        filter_jd_tab_content()

    with tab5:
        jd_match_tab_content()
        
    with tab6:
        chatbot_tab_content()
        
    with tab7:
        interview_prep_tab_content()


# ==============================================================================
# 4. STREAMLIT APP EXECUTION
# ==============================================================================

if __name__ == "__main__":
    candidate_dashboard()
