import streamlit as st
import os
import tempfile
import json
import re
import traceback
from datetime import date
from typing import Dict, Any, List
#
===
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
# Simple logic to return different data based on content to make the dashboard dynamic
if "Software Engineer" in jd_text:
    return {"role": "Software Engineer", "job_type": "Full-time", "key_skills": ["Python", "Flask",
"AWS", "SQL", "CI/CD"]}
elif "Data Scientist" in jd_text:
    return {"role": "Data Scientist", "job_type": "Contract", "key_skills": ["Python", "Machine
Learning", "TensorFlow", "Pandas", "Statistics"]}
return {"role": "General Analyst", "job_type": "Full-time", "key_skills": ["Python", "SQL",
"Cloud"]}
def parse_and_store_resume(file_input, file_name_key='default', source_type='file'):
"""Stub: Simulates parsing and stores results into a structure.
Updated default structured experience, education, certifications, and projects.
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
"responsibilities": "Developing and deploying AI/ML models for NLP and Computer
Vision projects."
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
#NEW: Example structured projects
default_structured_projects = [
{
"name": "Candidate Dashboard Builder",
"link": "[https://github.com/example/dashboard](https://github.com/example/dashboard)",
"description": "Developed a full-stack candidate dashboard using Streamlit for CV\nediting, JD matching, and interview preparation.",
"technologies": "Streamlit, Python, Pandas, JSON"
},
{
"name": "NLP Sentiment Analysis Model",
"link": "[https://github.com/example/nlp](https://github.com/example/nlp)",
"description": "Created a sentiment analysis model using TensorFlow and Keras to\nclassify customer reviews with 92% accuracy.",
"technologies": "Python, TensorFlow, Keras, NLTK"
}
]
# In the new structure, 'projects' will hold the structured data
parsed_data = {
"name": name_from_file,
"email": "candidate@example.com",
"phone": "555-123-4567",
"linkedin": "[linkedin.com/in/candidate](https://linkedin.com/in/candidate)",
"github": "[github.com/candidate](https://github.com/candidate)",
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
"personal_details": "Highly motivated and results-oriented professional with 3+ years\nexperience in AIML."
}
# Create a placeholder full_text
compiled_text = ""
for k, v in parsed_data.items():
# Exclude structured lists from raw text generation, except for the main keys
    if v and k not in ["structured_experience", "structured_certifications",
    "structured_education", "structured_projects"]:
        compiled_text += f"{k.replace('_', '').title()}:\n"
    if isinstance(v, list):
    # For raw text, we will flatten the structured data into simple strings (JSON format)
        if all(isinstance(item, dict) for item in v):
            compiled_text += "\n".join([json.dumps(item) for item in v]) + "\n\n"
        else:
            pass # Skipping this else block for better formatting
    else:
        compiled_text += "\n".join([f"- {item}" for item in v if isinstance(item, str)]) + "\n\n"
        compiled_text += str(v) + "\n\n"
return {"parsed": parsed_data, "full_text": compiled_text, "excel_data": None, "name":
parsed_data['name']}
def qa_on_resume(question):
"""Stub: Simulates Q&A on resume.""".
if "skills" in question.lower():
    return f"Based on the resume, the key skills are: {', '.join(st.session_state.parsed.get('skills',\n    ['No skills found']))}. The candidate has a strong background in data tools."
return f"Based on the resume, the answer to '{question}' is: [Simulated Answer - Check\nexperience/projects section for details. All data is stored as structured data.]"
def qa_on_jd(question, selected_jd_name):
"""Stub: Simulates Q&A on JD."""
return f"Based on the JD '{selected_jd_name}', the answer to '{question}' is: [Simulated\nAnswer - The JD content specifies a 5+ years experience requirement and mandatory\nPython/SQL skills]."
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
Overall Summary: This is a **Strong** fit. Focus on experience and project accomplishments in
the interview.
"""
def generate_interview_questions(parsed_json, section):
"""Stub: Simulates interview question generation."""
# Custom question generation for projects
if section == "projects":
    projects_data = parsed_json.get('projects', [])
    first_project = projects_data[0] if projects_data and isinstance(projects_data[0], dict) else {}
    if first_project:
        return f"""[Technical/Project Specific]
Q1: Can you walk me through your **{first_project.get('name', 'main project')}**? What was the
most challenging technical hurdle you overcame?
Q2: You mentioned using **{first_project.get('technologies', 'N/A')}** in this project. Can you
describe a specific design decision you made regarding one of those technologies?
Q3: How did your **{first_project.get('name', 'main project')}** lead to any measurable results or
learning outcomes?
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
Q1: Tell me about your **{first_degree.get('degree', 'highest degree')}** and how it prepared you
for this role.
Q2: What was your favorite technical project or thesis during your time at
**{first_degree.get('university', 'university')}**?
Q3: How do you think your academic performance (**{score_display}**) reflects your work ethic?
[Behavioral]
Q4: Describe a time you struggled academically and how you overcame it.
Q5: How do you keep your technical skills updated now that you've finished your formal
education?
"""
# Default behavior for other sections
return f"""[Behavioral]
Q1: Tell me about a time you applied your strongest skill, **{parsed_json.get('skills', ['No skill'])[:1][0]}**, to solve a major problem.
Q2: Describe a project where your work in the **{section}** section directly led to a quantifiable
business outcome.
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
- **Improvements:** Try to use the **STAR** (Situation, Task, Action, Result) method, especially
for behavioral questions. Quantify your results.
""")
feedback_parts.append(f"""
## Final Assessment
Total Score: {total_score}/{len(qa_list) * 10}
Overall Summary: The candidate shows **Good** fundamental knowledge. To score higher,
better integrate answers with accomplishments listed in the resume (e.g., mention specific
projects from the Prgayan AI role or the dashboard project).
""")
return "\n".join(feedback_parts)
#--- Simplified HTML/Markdown output for Structured Data
def generate_cv_html(parsed_data):
"""Generates CV HTML with simplified plain text output for structured sections."""
skills_list = "".join([f"<li>{s}</li>" for s in parsed_data.get('skills', []) if isinstance(s, str)])
#Education HTML
education_list = ""
for edu in parsed_data.get('education', []):
    if isinstance(edu, dict):
        score_display = f"{edu.get('score', 'N/A')} {edu.get('type', '')}".strip()
        education_list += f"""
<li>
**{edu.get('degree', 'N/A')}** ({score_display}) | {edu.get('college', 'N/A')},
{edu.get('university', 'N/A')}
<br>({edu.get('from_year', "")} - {edu.get('to_year', "")})
</li>
"""
# Experience HTML
experience_list = ""
for exp in parsed_data.get('experience', []):
    if isinstance(exp, dict):
        experience_list += f"""
<li>
**{exp.get('role', 'N/A')}** at {exp.get('company', 'N/A')} ({exp.get('from_year', "")} -
{exp.get('to_year', "")}).
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
<br>Technologies: *{proj.get('technologies', 'N/A')}*
</li>
"""
#Certifications HTML
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
<style>body{{font-family: Arial, sans-serif; margin: 40px;}} h1{{color: #2e6c80;
border-bottom: 2px solid #2e6c80; }} h2{{color: #3d99b1;}} ul{{list-style-type: none; padding: 0;}}
li{{margin-bottom: 10px;}}</style>
</head>
<body>
<h1>{parsed_data.get('name', 'CV Preview')}</h1>
<p>Email: {parsed_data.get('email', 'N/A')} | Phone: {parsed_data.get('phone', 'N/A')}</p>
<p>LinkedIn: <a href="{parsed_data.get('linkedin', '#')}">{parsed_data.get('linkedin',
'N/A')}</a></p>
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
md += f"**Contact:** {parsed_data.get('email', 'N/A')} | {parsed_data.get('phone', 'N/A')} |\n[LinkedIn]({parsed_data.get('linkedin', '#')})\n"
md += "\n"
md += f"## **SUMMARY**\n---\n"
md += parsed_data.get('personal_details', 'No summary provided.') + "\n\n"
md += "\n\n## **EXPERIENCE**\n---\n"
experience_md = []
for exp in parsed_data.get('experience', []):
    if isinstance(exp, dict):
        experience_md.append(
            f"**{exp.get('role', 'N/A')}** at {exp.get('company', 'N/A')} ({exp.get('from_year', "")} -\n{exp.get('to_year', "")}).\n"
        )
        experience_md.append(
            f"Responsibilities: {exp.get('responsibilities', 'N/A')}"
        )
md += "\n\n".join(experience_md)
#Projects Markdown (NEW)
md += "\n\n## **PROJECTS**\n---\n"
projects_md = []
for proj in parsed_data.get('projects', []):
    if isinstance(proj, dict):
        link_md = f" ([Link]({proj.get('link', '#')}))" if proj.get('link') else ""
        projects_md.append(
            f"**{proj.get('name', 'N/A')}**{link_md}\n"
            f"*Technologies: {proj.get('technologies', 'N/A')}*\n"
            f"Description: {proj.get('description', 'N/A')}"
        )
md += "\n\n".join(projects_md)
md += "\n\n## **EDUCATION**\n---\n"
education_md = []
for edu in parsed_data.get('education', []):
    if isinstance(edu, dict):
        score_display = f"{edu.get('score', 'N/A')} {edu.get('type', '')}".strip()
        education_md.append(
            f"**{edu.get('degree', 'N/A')}** ({score_display}) at {edu.get('college', 'N/A')} /\n{edu.get('university', 'N/A')}\n"
        )
        education_md.append(
            f"Duration: {edu.get('from_year', "")} - {edu.get('to_year', "")}"
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


md += "- " + "\n- ".join(parsed_data.get('skills', ['No skills listed']) if all(isinstance(s, str) for s in
parsed_data.get('skills', [])) else ["Skills list structure mismatch"])


md += "\n\n## **STRENGTHS**\n---\n"


md += "- " + "\n- ".join(parsed_data.get('strength', ['No strengths listed']) if all(isinstance(s, str)
for s in parsed_data.get('strength', [])) else ["Strengths list structure mismatch"])


return md

# --- Dynamic Add/Remove Handlers ---

def add_education_entry_handler():


# Retrieve values using the
widget_keys


    degree_val = st.session_state.get("temp_edu_degree_key", "").strip()


    college_val = st.session_state.get("temp_edu_college_key", "").strip()


    university_val = st.session_state.get("temp_edu_university_key", "").strip()


    from_year_val = st.session_state.get("temp_edu_from_year_key_sel", "").strip()


    to_year_val = st.session_state.get("temp_edu_to_year_key_sel", "Present").strip()
    
    # ... missing part for adding entry ...

    st.session_state["temp_edu_degree_key"] = ""


    st.session_state["temp_edu_college_key"] = ""


    st.session_state["temp_edu_university_key"] = ""


    st.session_state["temp_edu_score_key"] = ""


    st.session_state.force_rerun_for_add = True


    return True

def add_certification_entry_handler():


# Retrieve values using the widget keys


    title_val = st.session_state.get("temp_cert_title_key", "").strip()


    given_by_val = st.session_state.get("temp_cert_given_by_name_key", "").strip()


    organization_name_val = st.session_state.get("temp_cert_organization_name_key", "").strip()


    issue_date_val = st.session_state.get("temp_cert_issue_date_key",
    str(date.today().year)).strip()


    if

    not title_val or (not given_by_val and not organization_name_val):


        st.error("Error: Please fill in Certification Title and at least one issuer field before clicking\n    'Add Certificate'.")


        st.session_state.force_rerun_for_add = True


        return False


# new_en... missing part for adding entry ...

def add_experience_entry_handler():

    # The original document is missing the start of this function.
    company_val = st.session_state.get("temp_exp_company_key", "").strip() # Inferred
    role_val = st.session_state.get("temp_exp_role_key", "").strip() # Inferred
    
    from_year_val = st.session_state.get("temp_exp_from_year_key_sel", "").strip()


    to_year_val = st.session_state.get("temp_exp_to_year_key_sel", "Present").strip()


    ctc_val = st.session_state.get("temp_exp_ctc_key", "").strip()


    responsibilities_val = st.session_state.get("temp_exp_responsibilities_key", "").strip()

    if

    not company_val or not role_val or not from_year_val:


        st.error("Error: Please fill in Company, Role, and From Year fields before clicking 'Add\nExperience'.")


        st.session_state.force_rerun_for_add = True


        return False


    new_entry = {


        "company": company_val,


        "role": role_val,


        "from_year": from_year_val,


        "to_year": to_year_val,


        "ctc": ctc_val,


        "responsibilities": responsibilities_val


    }


    st.session_state.cv_form_data['structured_experience'].append(new_entry)


    st.toast(f"Experience\n    at {new_entry['company']} added (Form Submitted).")


# Reset temp state/widge ... missing part for resetting widgets ...

def add_project_entry_handler():
    
    # The original document is missing the start of this function.
    name_val = st.session_state.get("temp_proj_name_key", "").strip() # Inferred
    link_val = st.session_state.get("temp_proj_link_key", "").strip() # Inferred
    description_val = st.session_state.get("temp_proj_description_key", "").strip() # Inferred
    technologies_val = st.session_state.get("temp_proj_technologies_key", "").strip() # Inferred

    if not name_val:
        st.error("Error: Please fill in Project Name field before clicking 'Add Project'.")
        st.session_state.force_rerun_for_add = True
        return False
        
    new_entry = {


        "name": name_val,


        "link":

        link_val,


        "description": description_val,


        "technologies": technologies_val


    }


# Store in the structured projects list


    st.session_state.cv_form_data['structured_projects'].append(new_entry)


    st.toast(f"Project: {new_entry['name']} added (Form Submitted).")


# Reset temp state/widget
    values


    st.session_state["temp_proj_name_key"] = ""


    st.session_state["temp_proj_link_key"] = ""


    st.session_state["temp_proj_description_key"] = ""


    st.session_state["temp_proj_technologies_key"] = ""


    st.session_state.force_rerun_for_add = True


    return True


# Handlers for removing (these must trigger a direct state change and rerun)
def remove_education_entry(index):


# This handler is called directly by the st.button's on_click property (OUTSIDE THE FORM)


    if
    0 <= index < len(st.session_state.cv_form_data['structured_education']):


        removed_degree = st.session_state # Inferred from context that this line is incomplete

    st.rerun()


def remove_project_entry(index):


    if
    0 <= index < len(st.session_state.cv_form_data['structured_projects']):


        removed_name = st.session_state.cv_form_data['structured_projects'][index]['name']


        del st.session_state.cv_form_data['structured_projects'][index]


        st.toast(f"Project '{removed_name}' removed.")


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


    **CV Builder Workflow:** Fill in the dynamic entry data (e.g., Education, Projects) and click
    the corresponding **'Add Entry'** button to save it. Repeat for all entries.
    The current entries are
    listed right below their respective input sections. **Remove buttons are now
# Ensure the structured lists are present, falling back to the main list if needed


    if

    'structured_experience' not in st.session_state.cv_form_data:


        st.session_state.cv_form_data['structured_experience'] =
        st.session_state.cv_form_data.get('experience', []) if all(isinstance(i, dict) for i in
        st.session_state.cv_form_data.get('experience', [])) else []


    if

    'structured_certifications' not in st.session_state.cv_form_data:


        st.session_state.cv_form_data['structured_certifications'] =
        st.session_state.cv_form_data.get('certifications', []) if all(isinstance(i, dict) for i in
        st.session_state.cv_form_data.get('certifications', [])) else []

    if

    'structured_education' not in st.session_state.cv_form_data:


        st.session_state.cv_form_data['structured_education'] =
        st.session_state.cv_form_data.get('education', []) if all(isinstance(i, dict) for i in
        st.session_state.cv_form_data.get('education', [])) else []
# (Code continues in the original document, but the rest of the page is not fully present in the snippets)
