## Scope

This project is a **single-user resume optimizer** for my own resume. The system will:
- Accept a **job description (JD)** as either:
  - **Pasted text**, or
  - A **URL link** to a job posting.
- Extract and analyse JD content.
- Generate a **job-targeted resume** by modifying only specific sections of my base resume:
  - **Technical skills**
  - **Projects**
  - (Optionally) a short **summary/profile** section
- Keep all other sections **unchanged** (name, contact, education, experience text unless explicitly extended later).

---

## High-level User Flow

1. **User opens the website**
   - Lands on a simple UI with:
     - A **textarea** to paste JD text.
     - An **input field** to paste a JD **URL**.
     - A toggle / radio button to choose **“Text”** vs **“Link”** as source.

2. **User provides JD**
   - **Case A – Text JD**: User pastes the full JD into the textarea.
   - **Case B – Link JD**: User pastes the job link into the URL field.

3. **If JD is a link**
   - Backend will:
     - Validate the URL.
     - Fetch the HTML page (HTTP GET).
     - **Web-scrape** relevant content:
       - Job title
       - Job description / responsibilities
       - Required skills / qualifications
       - Preferred skills
     - Convert scraped HTML into **clean text JD**.

4. **Process JD**
   - Normalize the JD text (remove HTML artifacts, boilerplate, headers/footers).
   - Use an **LLM (OpenAI API)** to:
     - Extract **key responsibilities**.
     - Extract **required / preferred skills**.
     - Identify **keywords** and **ATS-friendly terms**.

5. **Generate targeted resume**
   - Start from a **base resume representation** (my single source-of-truth resume) stored as:
     - Either a structured file (e.g., JSON/YAML) or
     - A well-defined template with placeholders.
   - Update only:
     - **Technical skills section** (prioritize and phrase skills to match JD).
     - **Projects section** (select, emphasize, and rephrase projects most relevant to the JD).
     - (Optionally) **Summary section** to align with role.
   - Keep other sections **unchanged**.

6. **Preview and iterate**
   - Show the generated **resume preview** in the browser (HTML view).
   - Options:
     - **Download** as PDF/Docx.
     - **Regenerate** (e.g., “make it more concise”, “more senior”, etc.) via additional prompts.

---

## Functional Requirements

### Input & Validation
- **FR1**: User can input **JD text** directly via a large textarea.
- **FR2**: User can input a **JD URL** via a URL field.
- **FR3**: System must validate:
  - That at least one of JD text or JD URL is provided.
  - That the JD URL has a valid format.

### Web Scraping (for JD URL)
- **FR4**: For URL input, backend must:
  - Fetch page HTML.
  - Extract the main JD content (title, description, skills).
  - Handle common job site patterns where possible.
- **FR5**: Provide a **fallback**: if scraping fails, show a message asking the user to paste the JD text manually.

### JD Processing & Keyword Extraction
- **FR6**: Normalize the JD into clean text (strip HTML, remove navigation, etc.).
- **FR7**: Use **OpenAI** to:
  - Identify **role title** and level (e.g., “Senior Data Analyst”).
  - Extract **required skills** and **preferred skills**.
  - Extract **keywords / ATS-focused phrases** grouped by category (technical skills, tools, responsibilities, domain knowledge).

### Resume Base & Template
- **FR8**: Store my **base resume** in a **structured format** (e.g., JSON) with fields:
  - Personal details
  - Education
  - Experience
  - Projects (each with title, tech stack, description, impact)
  - Skills (grouped technical skills, tools, languages, etc.)
  - Summary (optional)
- **FR9**: Define a **resume template** (e.g., Jinja2 HTML template) that:
  - Maps structured resume data to sections.
  - Allows selective modification of only:
    - `technical_skills`
    - `projects`
    - `summary` (optional).

### Resume Optimization Logic
- **FR10**: From JD analysis, determine:
  - Which **skills** from my base resume to highlight / prioritize.
  - Which **projects** best match the JD and should be included or emphasized.
- **FR11**: Use OpenAI to:
  - Rephrase technical skills descriptions to better match JD phrases while staying truthful.
  - Rephrase project descriptions and bullet points to align with JD responsibilities and keywords.
- **FR12**: Ensure:
  - No hallucinated experiences or technologies I don’t actually have.
  - Only **reframing and prioritizing** existing content.

### Output & Download
- **FR13**: Render the final resume as **HTML** for preview in the browser.
- **FR14**: Provide **download** options:
  - PDF (preferred)
  - Optionally Docx.
- **FR15**: Provide a **“Regenerate”** option so user can:
  - Ask for another version (e.g., emphasize different projects, be shorter/longer).

---

## Non-Functional Requirements

- **NFR1**: Tech stack
  - Backend: **Python**
  - Preferred web framework: **FastAPI** or **Flask** (to be decided during implementation).
  - Templating engine: **Jinja2** (if HTML-based).
- **NFR2**: Performance
  - JD processing and resume generation should normally complete within **5–10 seconds** per request, depending on OpenAI latency.
- **NFR3**: Security & Privacy
  - Do **not** log raw JD or resume content in plaintext (or at least allow easy deletion).
  - Keep OpenAI API key in **environment variables** (e.g., `.env`, not in code).
- **NFR4**: Single-user assumption
  - System assumes only **my** base resume.
  - No multi-user auth or persistence is required initially.

---

## OpenAI Integration Requirements

- **OAI1**: Store `OPENAI_API_KEY` in environment configuration (e.g., `.env` + `python-dotenv`).
- **OAI2**: Create a small **Python client wrapper** for OpenAI that:
  - Handles model selection.
  - Accepts structured prompts (JD text, base resume data, instructions).
  - Returns structured outputs (skills list, projects to highlight, rewritten bullets).
- **OAI3**: Design **prompt templates** for:
  - JD analysis (extract roles, skills, responsibilities, keywords).
  - Resume optimization:
    - “Given this base resume and this JD analysis, rewrite only the skills and projects sections to optimize for ATS and relevance, without adding fake skills or experiences.”

---

## Backend Logic Checklist

- **Input layer**
  - Endpoint to accept:
    - `jd_text` (string)
    - `jd_url` (string)
  - Basic validation and error responses.

- **Scraping layer**
  - If `jd_url` present:
    - Fetch HTML.
    - Extract main JD.
    - Fallback if scraping fails.

- **JD analysis layer**
  - Normalize text.
  - Call OpenAI to extract:
    - Role, skills, keywords, responsibilities.

- **Resume data layer**
  - Load base resume JSON from disk.
  - Pass base resume + JD analysis to optimization logic.

- **Optimization layer**
  - Use OpenAI to:
    - Propose updated skills listing and projects bullets.
  - Merge updates into base resume structure:
    - **Only** modify:
      - Technical skills section.
      - Projects section.
      - (Optional) summary.

- **Rendering layer**
  - Render updated resume via template (HTML).
  - Expose HTML for preview.
  - Convert to PDF/Docx for download.

---

## Future Extensions (Optional)

- Support **multiple base resumes** (different role tracks).
- Save and list **previously generated resumes**.
- Add **simple authentication** if opened beyond personal use.
- Add **analytics**: which skills and projects are being used most often.

