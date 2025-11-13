import streamlit as st
import os
import tempfile
import json
import re
import traceback
from datetime import date
from typing import Dict, Any, List

# 1. DEPENDENCIES & HELPER FUNCTIONS (Stubs for demonstration)
#
======
==

#--- Utility Functions
def go_to(page_name):
    """Changes the current page in Streamlit's session state."""
    st.session_state.page = page_name

def clear_interview_state():
    """Clears all generated questions, answers, and the evaluation report."""
    # Resetting list with an empty list
    st.session_state.interview_qa = [] 
    st.session_state.iq_output = ""
    st.session_state.evaluation_report = ""
    st.toast("Practice answers cleared.")

# --- External LLM/File Logic (Simplified or Stubbed for standalone copy)
question_section_options = ["skills", "experience", "certifications", "projects", "education"]
DEFAULT_JOB_TYPES = ["Full-time", "Contract", "Internship", "Remote", "Part-time"]
DEFAULT_ROLES = ["Software Engineer", "Data Scientist", "Product Manager", "HR Manager",
"Marketing Specialist", "Operations Analyst"]

# STUBS for functions that require the actual full application code or external APIs
def extract_jd_from_linkedin_url(url: str) -> str:
    """Stub: Simulates JD content extraction."""
    return f"--- Simulated JD for: {url}\n\nJob Description content extracted from LinkedIn URL.\nThis includes role details, requirements, and company information."

def extract_jd_metadata(jd_text):
    """Stub: Simulates extraction of structured metadata."""
    # FIX APPLIED HERE: Ensure string literals are not broken across lines
    if "Software Engineer" in jd_text:
        return {"role": "Software Engineer", "job_type": "Full-time", "key_skills": ["Python", "Flask",
"AWS", "SQL", "CI/CD"]}
    elif "Data Scientist" in jd_text:
        return {"role": "Data Scientist", "job_type": "Contract", "key_skills": ["Python", "Machine Learning", "TensorFlow", "Pandas", "Statistics"]}
    return {"role": "General Analyst", "job_type": "Full-time", "key_skills": ["Python", "SQL",
"Cloud"]}

def parse_and_store_resume(file_input, file_name_key='default', source_type='file'):
    """Stub: Simulates parsing and stores results into a structure."""
    if st.session_state.get('parsed', {}).get('name') and st.session_state.parsed.get('name') != "":
        return {"parsed": st.session_state.parsed, "full_text": st.session_state.full_text,
        "excel_data": None, "name": st.session_state.parsed['name']}
    
    # Placeholder data for a fresh parse
    if source_type == 'file':
        name_from_file = getattr(file_input, 'name', 'Uploaded_Resume').split('.')[0].replace('_', '')
    else:
        name_from_file = "Parsed Text CV"

    # Example structured data
    default_structured_experience = [
    {
        "company": "Prgayan AI",
        "role": "AIML Engineer",
        "from_year": "2025",
        "to_year": "Present",
        "ctc": "Negotiable",
        "responsibilities": "Developing and deploying AI/ML models for NLP and Computer Vision projects."
    },
    ]
    default_structured_education = [
    {
        "degree": "M.Sc. Computer Science",
        "college": "University of Excellence",
        "university": "City University",
        "from_year": "2020",
        "to_year": "2022",
        "score": "8.5",
        "type": "CGPA"
    }
    ]
    default_structured_certifications = [
    {
        "title": "AWS Certified Cloud Practitioner",
        "given_by": "Dr. Smith",
        "organization_name": "Amazon Web Services",
        "issue_date": "2023-10-01"
    }
    ]
    # NEW: Example structured projects
    default_structured_projects = [
    {
        "name": "Candidate Dashboard Builder",
        "link": "https://github.com/example/dashboard",
        "description": "Developed a full-stack candidate dashboard using Streamlit for CV editing, JD matching, and interview preparation.",
        "technologies": ["Streamlit", "Python", "Pandas", "JSON"]
    },
    {
        "name": "NLP Sentiment Analysis Model",
        "link": "https://github.com/example/nlp",
        "description": "Created a sentiment analysis model using TensorFlow and Keras to classify customer reviews with 92% accuracy.",
        "technologies": ["Python", "TensorFlow", "Keras", "NLTK"]
    }
    ]
    # In the new structure, 'projects' will hold the structured data
    parsed_data = {
    "name": name_from_file,
    "email": "candidate@example.com",
    "phone": "555-123-4567",
    "linkedin": "linkedin.com/in/candidate",
    "github": "github.com/candidate",
    "skills": ["Python", "Machine Learning", "Streamlit", "Data Analysis", "TensorFlow"],
    "experience": default_structured_experience,
    "structured_experience": default_structured_experience,
    "education": default_structured_education,
    "structured_education": default_structured_education,
    "certifications": default_structured_certifications,
    "structured_certifications": default_structured_certifications,
    "projects": default_structured_projects, # Storing structured data here
    "structured_projects": default_structured_projects, # New structured list for form
    "strength": ["Problem Solver", "Quick Learner"],
    "personal_details": "Highly motivated and results-oriented professional with 3+ years experience in AIML."
    }

    # Create a placeholder full_text
    compiled_text = ""
    for k, v in parsed_data.items():
        # Exclude structured lists from raw text generation, except for the main keys
        if v and k not in ["structured_experience", "structured_certifications",
        "structured_education", "structured_projects"]:
            compiled_text += f"{k.replace('_', ' ').title()}:\n"
            if isinstance(v, list):
                # For raw text, we will flatten the structured data into simple strings (JSON format)
                if all(isinstance(item, dict) for item in v):
                    compiled_text += "\n".join([json.dumps(item) for item in v]) + "\n\n"
                elif all(isinstance(item, str) for item in v):
                    compiled_text += "\n".join([f"- {item}" for item in v]) + "\n\n"
            else:
                compiled_text += str(v) + "\n\n"

    return {"parsed": parsed_data, "full_text": compiled_text, "excel_data": None, "name":
parsed_data['name']}

def qa_on_resume(question):
    """Stub: Simulates Q&A on resume."""
    if "skills" in question.lower():
        return f"Based on the resume, the key skills are: {', '.join(st.session_state.parsed.get('skills', ['No skills found']))}. The candidate has a strong background in data tools."
    return f"Based on the resume, the answer to '{question}' is: [Simulated Answer - Check experience/projects section for details. All data is stored as structured data.]"

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
Section Match Analysis
Skills Match: {skills}%
Experience Match: {experience}%
Projects Match: 85% (Based on projects like 'Candidate Dashboard Builder')
Education Match: 90% (Based on M.Sc. degrees)
Strengths/Matches:
- Candidate's Python and ML skills ({skills} %) are an excellent match for this JD.
- Experience ({experience} %) is relevant, particularly the **AIML Engineer at Prgayan AI** role.
- **Projects** are highly relevant and show practical application of skills.
Gaps/Areas for Improvement:
- Needs more specific experience in the [Niche Technology] mentioned in the JD.
Overall Summary: This is a **Strong** fit. Focus on experience and project accomplishments in the interview.
"""

def generate_interview_questions(parsed_json, section):
    """Stub: Simulates interview question generation."""
    # Custom question generation for projects
    if section == "projects":
        projects_data = parsed_json.get('projects', [])
        first_project = projects_data[0] if projects_data and isinstance(projects_data[0], dict) else {}
        if first_project:
            return f"""[Technical/Project Specific]
Q1: Can you walk me through your **{first_project.get('name', 'main project')}**? What was the most challenging technical hurdle you overcame?
Q2: You mentioned using **{', '.join(first_project.get('technologies', ['N/A']))}** in this project. Can you describe a specific design decision you made regarding one of those technologies?
Q3: How did your **{first_project.get('name', 'main project')}** lead to any measurable results or learning outcomes?
[Behavioral]
Q4: Describe a time a project failed to meet expectations and what you learned from it.
Q5: How do you prioritize tasks when working on multiple projects simultaneously?
"""
    # Custom question generation for education
    elif section == "education":
        education_data = parsed_json.get('education', [])
        first_degree = {}
        if education_data and isinstance(education_data[0], dict):
            first_degree = education_data[0]
            score_display = f"{first_degree.get('score', 'N/A')} {first_degree.get('type', 'Score')}"
        else:
            score_display = "N/A"
        return f"""[Technical/Academic]
Q1: Tell me about your **{first_degree.get('degree', 'highest degree')}** and how it prepared you for this role.
Q2: What was your favorite technical project or thesis during your time at **{first_degree.get('university', 'university')}**?
Q3: How do you think your academic performance (**{score_display}**) reflects your work ethic?
[Behavioral]
Q4: Describe a time you struggled academically and how you overcame it.
Q5: How do you keep your technical skills updated now that you've finished your formal education?
"""
    # Default behavior for other sections
    return f"""[Behavioral]
Q1: Tell me about a time you applied your strongest skill, **{parsed_json.get('skills', ['No skill'])[:1][0]}**, to solve a major problem.
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
## Final Assessment
Total Score: {total_score}/{len(qa_list) * 10}
Overall Summary: The candidate shows **Good** fundamental knowledge. To score higher, better integrate answers with accomplishments listed in the resume (e.g., mention specific projects from the Prgayan AI role or the dashboard project).
""")
    return "\n".join(feedback_parts)

#--- Simplified HTML/Markdown output for Structured Data
def generate_cv_html(parsed_data):
    """Generates CV HTML with simplified plain text output for structured sections."""
    skills_list = "".join([f"<li>{s}</li>" for s in parsed_data.get('skills', []) if isinstance(s, str)])
    
    # Education HTML
    education_list = ""
    for edu in parsed_data.get('education', []):
        if isinstance(edu, dict):
            score_display = f"{edu.get('score', 'N/A')} {edu.get('type', '')}".strip()
            education_list += f"""
<li>
**{edu.get('degree', 'N/A')}** ({score_display}) | {edu.get('college', 'N/A')}, {edu.get('university', 'N/A')}
<br>({edu.get('from_year', "")} - {edu.get('to_year', "")})
</li>
"""
    # Experience HTML
    experience_list = ""
    for exp in parsed_data.get('experience', []):
        if isinstance(exp, dict):
            experience_list += f"""
<li>
**{exp.get('role', 'N/A')}** at {exp.get('company', 'N/A')} ({exp.get('from_year', "")} - {exp.get('to_year', "")}).
<br>Responsibilities: {exp.get('responsibilities', 'N/A')}
</li>
"""
    # Projects HTML (NEW)
    projects_list = ""
    for proj in parsed_data.get('projects', []):
        if isinstance(proj, dict):
            link_html = f" (<a href='{proj.get('link', '#')}'>Link</a>)" if proj.get('link') else ""
            projects_list += f"""
<li>
**{proj.get('name', 'N/A')}**{link_html}
<br>Description: {proj.get('description', 'N/A')}
<br>Technologies: *{', '.join(proj.get('technologies', ['N/A']))}*
</li>
"""
    # Certifications HTML
    certifications_list = ""
    for cert in parsed_data.get('certifications', []):
        if isinstance(cert, dict):
            issuer_info = f"{cert.get('given_by', 'N/A')}"
            if cert.get('organization_name', 'N/A') and cert.get('organization_name', 'N/A') != 'N/A':
                issuer_info += f" ({cert.get('organization_name', 'N/A')})"
            certifications_list += f"""
<li>
{cert.get('title', 'N/A')} - Issued by: {issuer_info}, Date: {cert.get('issue_date', 'N/A')}
</li>
"""
    # ......
    return f"""
<html>
<head>
<title>{parsed_data.get('name', 'CV Preview')}</title>
<style>body{{font-family: Arial, sans-serif; margin: 40px;}} h1{{color: #2e6c80; border-bottom: 2px solid #2e6c80; }} h2{{color: #3d99b1;}} ul{{list-style-type: none; padding: 0;}} li{{margin-bottom: 10px;}}</style>
</head>
<body>
<h1>{parsed_data.get('name', 'CV Preview')}</h1>
<p>Email: {parsed_data.get('email', 'N/A')} | Phone: {parsed_data.get('phone', 'N/A')}</p>
<p>LinkedIn: <a href="{parsed_data.get('linkedin', '#')}">{parsed_data.get('linkedin', 'N/A')}</a></p>
<h2>Key Skills</h2>
<ul>{skills_list}</ul>
<h2>Experience</h2>
<ul>{experience_list}</ul>
<h2>Projects</h2>
<ul>{projects_list}</ul>
<h2>Education</h2>
<ul>{education_list}</ul>
<h2>Certifications</h2>
<ul>{certifications_list}</ul>
<p>Generated by AI Dashboard on {date.today()}</p>
</body>
</html>
"""

def format_parsed_json_to_markdown(parsed_data):
    """Generates CV Markdown with simplified plain text output for structured sections."""
    md = f"# **{parsed_data.get('name', 'CV Preview').upper()}**\n"
    md += f"**Contact:** {parsed_data.get('email', 'N/A')} | {parsed_data.get('phone', 'N/A')} | [LinkedIn]({parsed_data.get('linkedin', '#')})\n"
    md += "\n"
    md += f"## **SUMMARY**\n---\n"
    md += parsed_data.get('personal_details', 'No summary provided.') + "\n\n"

    md += "\n\n## **EXPERIENCE**\n---\n"
    experience_md = []
    for exp in parsed_data.get('experience', []):
        if isinstance(exp, dict):
            experience_md.append(
                f"**{exp.get('role', 'N/A')}** at {exp.get('company', 'N/A')} ({exp.get('from_year', '')} - {exp.get('to_year', '')}).\n"
            )
            experience_md.append(
                f"Responsibilities: {exp.get('responsibilities', 'N/A')}"
            )
    md += "\n\n".join(experience_md)

    # Projects Markdown (NEW)
    md += "\n\n## **PROJECTS**\n---\n"
    projects_md = []
    for proj in parsed_data.get('projects', []):
        if isinstance(proj, dict):
            link_md = f" ([Link]({proj.get('link', '#')}))" if proj.get('link') else ""
            projects_md.append(
                f"**{proj.get('name', 'N/A')}**{link_md}\n"
                f"*Technologies: {', '.join(proj.get('technologies', ['N/A']))}*\n"
                f"Description: {proj.get('description', 'N/A')}"
            )
    md += "\n\n".join(projects_md)

    md += "\n\n## **EDUCATION**\n---\n"
    education_md = []
    for edu in parsed_data.get('education', []):
        if isinstance(edu, dict):
            score_display = f"{edu.get('score', 'N/A')} {edu.get('type', '')}".strip()
            education_md.append(
                f"**{edu.get('degree', 'N/A')}** ({score_display}) at {edu.get('college', 'N/A')} / {edu.get('university', 'N/A')}\n"
            )
            education_md.append(
                f"Duration: {edu.get('from_year', '')} - {edu.get('to_year', '')}"
            )
    md += "\n\n".join(education_md)

    md += "\n\n## **CERTIFICATIONS**\n---\n"
    certifications_md = []
    for cert in parsed_data.get('certifications', []):
        if isinstance(cert, dict):
            issuer_info = f"{cert.get('given_by', 'N/A')}"
            if cert.get('organization_name', 'N/A') and cert.get('organization_name', 'N/A') != 'N/A':
                issuer_info += f" ({cert.get('organization_name', 'N/A')})"
            certifications_md.append(
                f"{cert.get('title', 'N/A')} - Issued by: {issuer_info}, Date: {cert.get('issue_date', 'N/A')}"
            )
    md += "- " + "\n- ".join(certifications_md)

    md += "\n\n## **SKILLS**\n---\n"
    md += "- " + "\n- ".join(parsed_data.get('skills', ['No skills listed']) if all(isinstance(s, str) for s in parsed_data.get('skills', [])) else ["Skills list structure mismatch"])

    md += "\n\n## **STRENGTHS**\n---\n"
    md += "- " + "\n- ".join(parsed_data.get('strength', ['No strengths listed']) if all(isinstance(s, str) for s in parsed_data.get('strength', [])) else ["Strengths list structure mismatch"])

    return md

# --- Dynamic Add/Remove Handlers (Completed and Consolidated) ---

def add_education_entry_handler():
    """Adds a new education entry from temporary form inputs."""
    edu_data = {
        "degree": st.session_state.get("temp_edu_degree_key", "").strip(),
        "college": st.session_state.get("temp_edu_college_key", "").strip(),
        "university": st.session_state.get("temp_edu_university_key", "").strip(),
        "from_year": st.session_state.get("temp_edu_from_year_key_sel", str(date.today().year)).strip(),
        "to_year": st.session_state.get("temp_edu_to_year_key_sel", "Present").strip(),
        "score": st.session_state.get("temp_edu_score_key", "").strip(),
        "type": st.session_state.get("temp_edu_type_key_sel", "CGPA").strip(),
    }
    if edu_data['degree'] and edu_data['college']:
        st.session_state.cv_form_data['structured_education'].append(edu_data)
        st.session_state.force_rerun_for_add = True

def remove_education_entry(index):
    """Removes an education entry by index and forces a rerun."""
    if 0 <= index < len(st.session_state.cv_form_data['structured_education']):
        st.session_state.cv_form_data['structured_education'].pop(index)
        st.session_state.force_rerun_for_add = True
        st.rerun()

def add_experience_entry_handler():
    """Adds a new experience entry from temporary form inputs."""
    exp_data = {
        "company": st.session_state.get("temp_exp_company_key", "").strip(),
        "role": st.session_state.get("temp_exp_role_key", "").strip(),
        "from_year": st.session_state.get("temp_exp_from_year_key_sel", str(date.today().year)).strip(),
        "to_year": st.session_state.get("temp_exp_to_year_key_sel", "Present").strip(),
        "ctc": st.session_state.get("temp_exp_ctc_key", "").strip(),
        "responsibilities": st.session_state.get("temp_exp_responsibilities_key", "").strip()
    }
    if exp_data['company'] and exp_data['role']:
        st.session_state.cv_form_data['structured_experience'].append(exp_data)
        st.session_state.force_rerun_for_add = True

def remove_experience_entry(index):
    """Removes an experience entry by index and forces a rerun."""
    if 0 <= index < len(st.session_state.cv_form_data['structured_experience']):
        st.session_state.cv_form_data['structured_experience'].pop(index)
        st.session_state.force_rerun_for_add = True
        st.rerun()

def add_certification_entry_handler():
    """Adds a new certification entry from temporary form inputs."""
    cert_data = {
        "title": st.session_state.get("temp_cert_title_key", "").strip(),
        "given_by": st.session_state.get("temp_cert_given_by_name_key", "").strip(),
        "organization_name": st.session_state.get("temp_cert_organization_name_key", "").strip(),
        "issue_date": st.session_state.get("temp_cert_issue_date_key", "").strip()
    }
    if cert_data['title'] and (cert_data['given_by'] or cert_data['organization_name']):
        st.session_state.cv_form_data['structured_certifications'].append(cert_data)
        st.session_state.force_rerun_for_add = True

def remove_certification_entry(index):
    """Removes a certification entry by index and forces a rerun."""
    if 0 <= index < len(st.session_state.cv_form_data['structured_certifications']):
        st.session_state.cv_form_data['structured_certifications'].pop(index)
        st.session_state.force_rerun_for_add = True
        st.rerun()

def add_project_entry_handler():
    """Adds a new project entry from temporary form inputs."""
    technologies_str = st.session_state.get("temp_proj_technologies_key", "").strip()
    
    proj_data = {
        "name": st.session_state.get("temp_proj_name_key", "").strip(),
        "link": st.session_state.get("temp_proj_link_key", "").strip(),
        "description": st.session_state.get("temp_proj_description_key", "").strip(),
        "technologies": [t.strip() for t in technologies_str.split(',') if t.strip()]
    }
    
    if proj_data['name'] and proj_data['description']:
        st.session_state.cv_form_data['structured_projects'].append(proj_data)
        st.session_state.force_rerun_for_add = True

def remove_project_entry(index):
    """Removes a project entry by index and forces a rerun."""
    if 0 <= index < len(st.session_state.cv_form_data['structured_projects']):
        st.session_state.cv_form_data['structured_projects'].pop(index)
        st.session_state.force_rerun_for_add = True
        st.rerun()

#
========================================================================
======

# 2. TAB CONTENT FUNCTIONS (Updated CV Management)
#
========================================================================
======


def cv_management_tab_content():
    st.header("📝 Prepare Your CV")
    st.markdown("### 1. Form Based CV Builder")
    
    st.info("""
    **CV Builder Workflow:** Use the dynamic input fields (e.g., Education, Experience, Projects) to add individual entries by clicking the corresponding **'Add Entry'** button. The current entries are listed below their respective input sections. When finished, click the final **'Generate and Load ALL CV Data'** button at the bottom to finalize all CV sections.
    """)

    # --- Session State Initialization for CV Builder ---
    default_parsed = {
        "name": "", "email": "", "phone": "", "linkedin": "", "github": "",
        "skills": [], "experience": [], "education": [], "certifications": [], 
        "projects": [], "strength": [], "personal_details": "",
        "structured_experience": [],
        "structured_certifications": [],
        "structured_education": [],
        "structured_projects": []
    }
    
    if "cv_form_data" not in st.session_state:
        st.session_state.cv_form_data = default_parsed
        if st.session_state.get('parsed'):
             st.session_state.cv_form_data.update(st.session_state.parsed)
             
    # Ensure lists are initialized correctly
    for key in ['structured_experience', 'structured_certifications', 'structured_education', 'structured_projects', 'skills', 'strength']:
         if not isinstance(st.session_state.cv_form_data.get(key), list):
             st.session_state.cv_form_data[key] = []
         
    if 'force_rerun_for_add' not in st.session_state:
        st.session_state.force_rerun_for_add = False
    
    if 'full_text' not in st.session_state:
        st.session_state.full_text = ""
        
    if 'parsed' not in st.session_state: # Ensure 'parsed' exists for the final download section
        st.session_state.parsed = {}

    # Initialize/reset year options for date pickers
    current_year = date.today().year
    year_options = [str(y) for y in range(current_year, 1950, -1)]
    to_year_options = ["Present"] + year_options
    
    
    # --- CV Builder Form (SINGLE BLOCK) ---
    with st.form("cv_builder_form", clear_on_submit=False):
        
        # --- 1. PERSONAL & CONTACT DETAILS ---
        st.subheader("1. Personal, Contact, and Summary Details")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.session_state.cv_form_data['name'] = st.text_input(
                "Full Name", 
                value=st.session_state.cv_form_data.get('name', ''), 
                key="cv_name_input"
            ).strip() 
        with col2:
            st.session_state.cv_form_data['email'] = st.text_input(
                "Email Address", 
                value=st.session_state.cv_form_data.get('email', ''), 
                key="cv_email_input"
            ).strip() 
        with col3:
            st.session_state.cv_form_data['phone'] = st.text_input(
                "Phone Number", 
                value=st.session_state.cv_form_data.get('phone', ''), 
                key="cv_phone_input"
            ).strip() 
        
        col4, col5 = st.columns(2)
        with col4:
            st.session_state.cv_form_data['linkedin'] = st.text_input(
                "LinkedIn Profile URL", 
                value=st.session_state.cv_form_data.get('linkedin', ''), 
                key="cv_linkedin_input"
            ).strip() 
        with col5:
            st.session_state.cv_form_data['github'] = st.text_input(
                "GitHub Profile URL", 
                value=st.session_state.cv_form_data.get('github', ''), 
                key="cv_github_input"
            ).strip() 
        
        st.session_state.cv_form_data['personal_details'] = st.text_area(
            "Professional Summary (A brief pitch about yourself)", 
            value=st.session_state.cv_form_data.get('personal_details', ''), 
            height=100,
            key="cv_personal_details_input"
        ).strip() 
        
        # --- 2. SKILLS ---
        st.markdown("---")
        st.subheader("2. Key Skills (One Item per Line)")

        skills_text = "\n".join(st.session_state.cv_form_data.get('skills', []))
        new_skills_text = st.text_area(
            "Technical and Soft Skills", 
            value=skills_text,
            height=100,
            key="cv_skills_input_form" 
        )
        st.session_state.cv_form_data['skills'] = [s.strip() for s in new_skills_text.split('\n') if s.strip()]
        
        # --- 3. DYNAMIC EDUCATION INPUT FIELDS & ADD BUTTON ---
        st.markdown("---")
        st.subheader("3. Dynamic Education Management")
        
        col_d, col_c = st.columns(2)
        with col_d:
            st.text_input("Degree/Qualification", key="temp_edu_degree_key", placeholder="e.g., M.Sc. Computer Science")
            
        with col_c:
            st.text_input("College Name", key="temp_edu_college_key", placeholder="e.g., MIT, Chennai")
            
        st.text_input("University Name", key="temp_edu_university_key", placeholder="e.g., Anna University")
        
        col_fy, col_ty = st.columns(2)
        with col_fy:
            st.selectbox("From Year", options=year_options, key="temp_edu_from_year_key_sel")
            
        with col_ty:
            st.selectbox("To Year", options=to_year_options, key="temp_edu_to_year_key_sel")
            
        col_s, col_st = st.columns([2, 1])
        with col_s:
            st.text_input("CGPA or Score Value", key="temp_edu_score_key", placeholder="e.g., 8.5 or 90")
        with col_st:
            st.selectbox("Type", options=["CGPA", "Percentage", "Grade"], key="temp_edu_type_key_sel")
            
        # Add Entry Button
        st.form_submit_button(
            "➕ Add Education Entry", 
            key="add_edu_button_form", 
            type="secondary", 
            use_container_width=True, 
            on_click=add_education_entry_handler,
            help="Adds the entry above and reloads the page to show the current list."
        )
        
        st.markdown("---") 
        
        # --- 4. DYNAMIC EXPERIENCE INPUT FIELDS & ADD BUTTON ---
        st.subheader("4. Dynamic Professional Experience Management")
        
        col_c, col_r = st.columns(2)
        with col_c:
            st.text_input("Company Name", key="temp_exp_company_key", placeholder="e.g., Google")
            
        with col_r:
            st.text_input("Role/Title", key="temp_exp_role_key", placeholder="e.g., Data Scientist")

        col_fy_exp, col_ty_exp, col_c3 = st.columns(3)
        
        with col_fy_exp:
            st.selectbox("From Year", options=year_options, key="temp_exp_from_year_key_sel")
            
        with col_ty_exp:
            st.selectbox("To Year", options=to_year_options, key="temp_exp_to_year_key_sel")
            
        with col_c3:
            st.text_input("CTC (Annual)", key="temp_exp_ctc_key", placeholder="e.g., $150k / 20L INR")

        st.text_area(
            "Key Responsibilities/Achievements (Brief summary)", 
            height=70, 
            key="temp_exp_responsibilities_key"
        )
        
        # Add Entry Button
        st.form_submit_button(
            "➕ Add This Experience", 
            key="add_exp_button_form", 
            type="secondary", 
            use_container_width=True, 
            on_click=add_experience_entry_handler,
            help="Adds the entry above and reloads the page to show the current list."
        )
        
        st.markdown("---") 

        # --- 5. DYNAMIC CERTIFICATION INPUT FIELDS & ADD BUTTON ---
        st.subheader("5. Dynamic Certifications Management")
        
        col_t, col_g, col_o = st.columns(3) 
        with col_t:
            st.text_input("Certification Title", key="temp_cert_title_key", placeholder="e.g., Google Cloud Architect")
            
        with col_g:
            st.text_input(
                "Issue By Name (Sir/Mam)", 
                key="temp_cert_given_by_name_key", 
                placeholder="e.g., Dr. Jane Doe"
            )
            
        with col_o:
            st.text_input(
                "Issuing Organization Name", 
                key="temp_cert_organization_name_key", 
                placeholder="e.g., Coursera, AWS, PMI"
            )

        col_d, _ = st.columns(2)
        with col_d:
            st.text_input("Issue Date (YYYY-MM-DD or Year)", key="temp_cert_issue_date_key", placeholder="e.g., 2024-05-15 or 2023")

        # Add Entry Button
        st.form_submit_button(
            "➕ Add Certificate", 
            key="add_cert_button_form", 
            type="secondary", 
            use_container_width=True, 
            on_click=add_certification_entry_handler,
            help="Adds the entry above and reloads the page to show the current list."
        )

        st.markdown("---")
        
        # --- 6. DYNAMIC PROJECTS INPUT FIELDS & ADD BUTTON ---
        st.subheader("6. Dynamic Projects Management")
        
        st.text_input("Project Name", key="temp_proj_name_key", placeholder="e.g., NLP Sentiment Analysis Model")
        st.text_input("Project Link (Optional)", key="temp_proj_link_key", placeholder="e.g., https://github.com/myuser/myproject")
        
        col_desc, col_tech = st.columns(2)
        with col_desc:
            st.text_area(
                "Project Description (Key goal and achievements)", 
                height=100, 
                key="temp_proj_description_key",
                placeholder="Developed a machine learning model to categorize customer reviews, improving service response time by 15%."
            )
        with col_tech:
             st.text_area(
                "Technologies Used (Comma separated list)", 
                height=100, 
                key="temp_proj_technologies_key",
                placeholder="e.g., Python, TensorFlow, Keras, Flask"
            )

        # Add Entry Button 
        st.form_submit_button(
            "➕ Add Project", 
            key="add_proj_button_form", 
            type="secondary", 
            use_container_width=True, 
            on_click=add_project_entry_handler,
            help="Adds the project above and reloads the page to show the current list."
        )
            
        st.markdown("---") 

        # --- 7. STRENGTHS ---
        st.subheader("7. Strengths (One Item per Line)")
        strength_text = "\n".join(st.session_state.cv_form_data.get('strength', []))
        new_strength_text = st.text_area(
            "Key Personal Qualities", 
            value=strength_text,
            height=70,
            key="cv_strength_input_form"
        )
        st.session_state.cv_form_data['strength'] = [s.strip() for s in new_strength_text.split('\n') if s.strip()]

        
        st.markdown("---") 

        # --- 8. FINAL SUBMISSION BUTTON (Inside the form) ---
        st.markdown("---")
        st.subheader("8. Generate or Load ALL CV Data")
        st.warning("Click the button below to **finalize** your entire CV data structure using the current form values and the added dynamic entries.")
        submit_form_button = st.form_submit_button("Generate and Load ALL CV Data", type="primary", use_container_width=True)

    
    # --- FORM SUBMISSION LOGIC & RERUN CHECK ---
    if submit_form_button:
        # Final CV Generation
        if not st.session_state.cv_form_data['name'] or not st.session_state.cv_form_data['email']:
            st.error("Please fill in at least your **Full Name** and **Email Address**.")
        else:
            # 1. Synchronize the structured lists into the main keys for AI consumption
            st.session_state.cv_form_data['experience'] = st.session_state.cv_form_data.get('structured_experience', [])
            st.session_state.cv_form_data['certifications'] = st.session_state.cv_form_data.get('structured_certifications', [])
            st.session_state.cv_form_data['education'] = st.session_state.cv_form_data.get('structured_education', [])
            st.session_state.cv_form_data['projects'] = st.session_state.cv_form_data.get('structured_projects', []) 
            
            # 2. Update the main parsed state
            st.session_state.parsed = st.session_state.cv_form_data.copy()
            
            # 3. Create a placeholder full_text 
            compiled_text = ""
            EXCLUDE_KEYS = ["structured_experience", "structured_certifications", "structured_education", "structured_projects"] 
            
            for k, v in st.session_state.cv_form_data.items():
                if k in EXCLUDE_KEYS: continue
                if v and (isinstance(v, str) and v.strip() or isinstance(v, list) and v):
                    compiled_text += f"{k.replace('_', ' ').title()}:\n"
                    if isinstance(v, list):
                        if all(isinstance(item, dict) for item in v):
                             compiled_text += "\n".join([json.dumps(item) for item in v]) + "\n\n"
                        elif all(isinstance(item, str) for item in v):
                            compiled_text += "\n".join([f"- {item}" for item in v]) + "\n\n"
                    else:
                        compiled_text += str(v) + "\n\n"
                        
            st.session_state.full_text = compiled_text
            
            st.success(f"✅ CV data for **{st.session_state.parsed['name']}** successfully generated and loaded!")

    
    # --- Force Rerun for Dynamic Adds (CRITICAL WORKAROUND) ---
    if st.session_state.force_rerun_for_add:
        st.session_state.force_rerun_for_add = False
        st.rerun() # Force rerun to clear inputs and display list update
        
    
    # --- DYNAMIC DISPLAY SECTIONS (OUTSIDE THE FORM, REMOVE BUTTONS HERE) ---
    st.markdown("---") 
    st.markdown("## Current Dynamic Entries")
    
    # Education Display
    st.markdown("### 🎓 Current Education Entries")
    if st.session_state.cv_form_data['structured_education']:
        for i, entry in enumerate(st.session_state.cv_form_data['structured_education']):
            col_disp, col_rem = st.columns([6, 1])
            with col_disp:
                score_display = f"{entry.get('score', 'N/A')} {entry.get('type', '')}".strip()
                st.markdown(f"- **{entry['degree']}** - {entry.get('college', 'N/A')} ({entry['from_year']} - {entry['to_year']}) | Score: {score_display}")
            with col_rem:
                st.button("❌", 
                          key=f"remove_edu_{i}_out", 
                          on_click=remove_education_entry, 
                          args=(i,), 
                          type="primary", 
                          help=f"Remove: {entry['degree']}")
    else:
        st.info("No education entries added yet.")
        
    st.markdown("---")

    # Experience Display
    st.markdown("### 💼 Current Professional Experience Entries")
    if st.session_state.cv_form_data['structured_experience']:
        for i, entry in enumerate(st.session_state.cv_form_data['structured_experience']):
            col_disp, col_rem = st.columns([6, 1])
            with col_disp:
                st.markdown(f"- **{entry['role']}** at {entry['company']} ({entry['from_year']} - {entry['to_year']}) | CTC: {entry['ctc']}")
            with col_rem:
                st.button("❌", 
                          key=f"remove_exp_{i}_out", 
                          on_click=remove_experience_entry, 
                          args=(i,), 
                          type="primary",
                          help=f"Remove: {entry['company']}")
    else:
        st.info("No experience entries added yet.")

    st.markdown("---")
    
    # Certifications Display
    st.markdown("### 🏅 Current Certifications")
    if st.session_state.cv_form_data['structured_certifications']:
        for i, entry in enumerate(st.session_state.cv_form_data['structured_certifications']):
            col_disp, col_rem = st.columns([6, 1])
            with col_disp:
                issuer_info = f"{entry.get('given_by', 'N/A')}"
                if entry.get('organization_name', 'N/A') and entry.get('organization_name', 'N/A') != 'N/A':
                    issuer_info += f" ({entry.get('organization_name', 'N/A')})"
                st.markdown(f"- **{entry['title']}** by {issuer_info} (Issued: {entry['issue_date']})")
            with col_rem:
                st.button("❌", 
                          key=f"remove_cert_{i}_out", 
                          on_click=remove_certification_entry, 
                          args=(i,), 
                          type="primary",
                          help=f"Remove: {entry['title']}")
    else:
        st.info("No certifications added yet.")
        
    st.markdown("---")
    
    # Projects Display
    st.markdown("### 💻 Current Projects")
    if st.session_state.cv_form_data['structured_projects']:
        for i, entry in enumerate(st.session_state.cv_form_data['structured_projects']):
            col_disp, col_rem = st.columns([6, 1])
            with col_disp:
                link_icon = "🔗" if entry.get('link') else ""
                tech_list = ", ".join(entry.get('technologies', []))
                st.markdown(f"- **{entry['name']}** {link_icon} | *Tech: {tech_list}*")
                st.caption(entry.get('description', 'No description.'))
            with col_rem:
                st.button("❌", 
                          key=f"remove_proj_{i}_out", 
                          on_click=remove_project_entry, 
                          args=(i,), 
                          type="primary",
                          help=f"Remove: {entry['name']}")
    else:
        st.info("No projects added yet.")
        
    st.markdown("---")
    
    
    # --- CV Preview and Download ---
    st.markdown("---")
    st.subheader("9. Loaded CV Data Preview and Download")
    
    if st.session_state.get('parsed', {}).get('name') and st.session_state.parsed.get('name') != "":
        
        EXCLUDE_KEYS_PREVIEW = ["structured_experience", "structured_certifications", "structured_education", "structured_projects"]
        filled_data_for_preview = {
            k: v for k, v in st.session_state.parsed.items() 
            if v and k not in EXCLUDE_KEYS_PREVIEW and (isinstance(v, str) and v.strip() or isinstance(v, list) and v)
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
            st.json(filled_data_for_preview)
            st.info("This is the raw, structured data used by the AI tools.")

            json_output = json.dumps(filled_data_for_preview, indent=2)
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

# --- Main App Structure (Run the App) ---
if __name__ == '__main__':
    st.set_page_config(layout="wide", page_title="AI Candidate Dashboard")
    st.title("🤖 AI-Powered Candidate Dashboard")
    st.caption("Manage, Review, and Optimize your CV data.")

    # Call the main function
    cv_management_tab_content()

    st.sidebar.markdown("---")
    st.sidebar.markdown("## Current Session State")
    if st.sidebar.checkbox("Show Raw Session State"):
        st.sidebar.json({k: v for k, v in st.session_state.items() if k not in ['cv_form_data', 'parsed']})
        st.sidebar.markdown("---")
        st.sidebar.json(st.session_state.get('cv_form_data', {}))
