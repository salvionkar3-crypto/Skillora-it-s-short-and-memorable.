# Skillora AI — Resume-to-Skills Learning Platform 🎓

> **AI-powered learning platform that analyzes a student's resume, identifies skill gaps for a target career role, constructs a prioritized roadmap, recommends curated YouTube lessons in multiple languages, tracks daily learning streaks, and leverages local open-weight Gemma 3:1B for private, grounded career mentoring.**

---

## 🌟 Key Features

1. **🤖 Local Open-Weight AI (Gemma 3:1B via Ollama)**
   - Powered by Google's open-weight **Gemma 3:1B** running 100% locally via Ollama HTTP API (`http://localhost:11434`).
   - **Zero Cloud Calls & 100% Privacy:** Resume text is never sent to external AI servers or saved to disk.
   - **Zero Hallucination Guardrails:** AI answers are grounded strictly in the candidate's resume and job description.
   - **Offline Resilience:** If Ollama is offline or unavailable, Skillora automatically falls back to deterministic rule-based analysis without crashing.
   - **Visible Status Indicator:** A live status badge in the sidebar indicates whether Gemma 3:1B is reachable, along with ping latency.

2. **📄 Safe & Privacy-First Resume Analysis**
   - In-memory parsing for **PDF**, **DOCX**, and plain text.
   - Resumes are **never permanently stored** on external servers or local disk.
   - Built-in detection for empty files, corrupted files, and scanned documents with helpful user notices.
   - Includes **3 One-Click Demo Resumes** (Junior Python Developer, Aspiring AI Engineer, Junior Web Developer) for instant testing.
   - **AI Resume Evidence & Context:** Inspect any detected skill to see verified ground-truth excerpts alongside Gemma 3:1B's context summary.

3. **🎯 Deterministic Skill Gap Analysis & Transparent Scoring**
   - High-precision deterministic skill matcher supporting extensive aliases (`k8s` → Kubernetes, `postgres` → PostgreSQL, `js` → JavaScript, etc.).
   - Transparent, mathematical Match Score formula:
     $$\text{Score} = \frac{\sum (\text{Matched Core} \times 1.5) + \sum (\text{Matched Recommended} \times 1.0)}{\text{Total Role Requirement Weights}} \times 100$$
   - Clearly categorized into **Matched Skills**, **Skill Gaps to Learn**, and **Needs Review / Additional Strengths**.
   - Optional Job Description (JD) text field to factor in posting-specific requirements with **AI Job Description Context Insights**.
   - Interactive verification checkboxes allowing students to manually confirm or adjust detected skills.

4. **🗺️ Personalized Learning Roadmap & AI Career Mentor**
   - Topological prerequisite ordering (e.g., Python before Django/PyTorch; HTML/CSS before JavaScript before React).
   - Priority ratings (`High`, `Medium`), estimated study hours adapted by experience level (Beginner, Intermediate, Advanced), clear learning objectives, and practical portfolio mini-projects for every milestone.
   - **AI Career Mentor Strategy:** Gemma 3:1B generates encouraging, personalized transition advice explaining how your verified existing skills accelerate learning your missing gaps.

5. **📺 Curated YouTube Learning Hub**
   - Curated video lessons with **verified video IDs, channels, and URLs**.
   - Multi-language filtering: **English**, **Hindi**, and **Marathi**.
   - Difficulty filtering: **Beginner**, **Intermediate**, and **Advanced**.
   - Integrated YouTube player and direct external links.
   - **Safe Search Fallback:** If an uncataloged or rare skill is requested, Skillora generates an official YouTube search query rather than inventing a hallucinated recommendation.

6. **🔥 Daily Learning Streaks & Lesson Completion**
   - "Mark as Complete" action on all roadmap milestones and video lessons.
   - Persistent SQLite database (`skillora.db`) preventing duplicate completions.
   - Date-safe daily streak engine:
     - 1 qualifying lesson per day increments the streak.
     - Multiple completions on the same calendar day do not artificially inflate streaks.
     - Consecutive calendar days keep the streak burning.
     - Missed calendar days reset the streak back to 1 upon the next qualifying session.

---

## 📁 Project Structure

```text
skillora hactoberfest/
├── app.py                      # Main Streamlit application entry point
├── requirements.txt            # Minimal, exact Python dependencies
├── README.md                   # Comprehensive documentation and Windows guide
├── .env.example                # Configuration template
├── .gitignore                  # Git ignore rules
├── ai/                         # Reusable Local AI module (Ollama + Gemma 3:1B)
│   ├── __init__.py
│   └── gemma_service.py        # Gemma 3:1B HTTP client, health checks & fallbacks
├── analyzer/                   # Resume text extraction and skill gap matching
│   ├── __init__.py
│   ├── parser.py               # Safe PDF/DOCX parsing & scanned file detection
│   ├── skills_db.py            # Taxonomy of skills, career roles, and aliases
│   └── matcher.py              # Deterministic matcher & transparent score calculator
├── learning/                   # Roadmap generation and YouTube recommendations
│   ├── __init__.py
│   ├── roadmap.py              # Prioritized syllabus & prerequisite sorting
│   └── youtube.py              # Verified YouTube video catalog & search fallback
├── progress/                   # SQLite persistence and streak accounting
│   ├── __init__.py
│   ├── database.py             # SQLite tables, indexes, and connection manager
│   └── tracker.py              # Completion logic, duplicate prevention & streaks
├── data/
│   ├── __init__.py
│   └── sample_videos.json      # Verified video catalog with real IDs & channels
└── tests/                      # Automated unit test suite (44 passing tests)
    ├── __init__.py
    ├── test_ai_service.py      # Ollama health checks, timeouts, and Gemma generation
    ├── test_parser.py          # PDF/DOCX edge cases & error handling
    ├── test_matcher.py         # Skill matching, aliases, and JD gap calculation
    ├── test_roadmap.py         # Priority ordering & prerequisite sequence
    ├── test_youtube.py         # Curated lessons, language filters & search fallback
    ├── test_tracker.py         # Duplicate prevention & streak calendar rules
    └── test_database.py        # SQLite persistence and data integrity
```

---

## 💻 Windows Setup & Run Guide (PowerShell)

### Step 1: Open PowerShell and Navigate to the Project
```powershell
cd "c:\Users\salvi\OneDrive\Documents\skillora hactoberfest"
```

### Step 2: (Optional) Activate Virtual Environment
If you are using a virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Ensure Ollama is Running with Gemma 3:1B
Verify Ollama is installed and run Gemma 3:1B:
```powershell
# 1. Verify Ollama CLI
ollama --version

# 2. Start and test Gemma 3:1B in terminal (press Ctrl+D or type /bye to exit interactive mode)
ollama run gemma3:1b

# 3. Verify the model is listed
ollama list
```
*Note: Ollama serves its HTTP API locally at `http://localhost:11434`.*

### Step 5: Run the Automated Test Suite (44 Tests)
Verify that all unit and integration tests pass:
```powershell
python -m pytest tests/ -v
```

### Step 6: Launch the Skillora AI Application
```powershell
streamlit run app.py
```
*Your browser will automatically open `http://localhost:8501`.*

---

## 🔍 How to Demonstrate Gemma 3:1B is Being Called

You can verify that Gemma 3:1B is live and answering requests through multiple touchpoints:

1. **Visible AI Indicator in Sidebar:**
   - Look at the left sidebar under **Skillora AI**.
   - When Ollama is active, it renders: `🟢 Gemma 3:1B (Local AI)` with ping response time in milliseconds (e.g., `45ms`).
   - If Ollama is closed, it immediately transitions to: `⚪ Local AI: Offline (Deterministic Fallback)`.

2. **Live Inference Console in `⚙️ Settings`:**
   - Navigate to the **⚙️ Settings** tab.
   - Scroll to **🤖 Local AI Engine Configuration (Gemma 3:1B)**.
   - Click **🚀 Run Live Gemma Inference Test**.
   - It will execute a live HTTP request to `http://localhost:11434/api/generate` and display the generated response, model name (`gemma3:1b`), and latency in milliseconds.

3. **Resume Evidence Explanation in `📄 Resume Analyzer`:**
   - Upload a resume or click any of the 1-click demo buttons (e.g., *Junior Python Developer*).
   - Under **🤖 AI Resume Evidence & Context (Gemma 3:1B)**, pick any detected skill (e.g. `Python`) and click **Analyze Context**.
   - Gemma 3:1B will extract and summarize the specific project context directly from the resume text.

4. **AI Career Mentor Strategy in `🗺️ Learning Roadmap`:**
   - Navigate to **🗺️ Learning Roadmap**.
   - The card **🤖 AI Career Mentor Strategy (Gemma 3:1B)** displays personalized transition advice based on your verified skills and target gaps.

---

## 🔒 Privacy, Quality, and Safety Commitments

- **100% Local Inference:** No resume data, prompt, or career query is ever transmitted over the internet or sent to external cloud APIs.
- **In-Memory File Processing:** Uploaded resumes are read as in-memory streams and discarded once your session ends; nothing is saved to disk.
- **Deterministic Ground Truth:** Core matching, gap classification, and scoring are strictly mathematical and deterministic. AI is used solely for contextual explanation and mentoring advice.
- **Zero Hallucinated Recommendations:** YouTube learning resources are curated with real video IDs. Uncataloged skills use verified search queries rather than fabricated URLs.
- **Graceful Fallback:** If Ollama is turned off, the entire application remains 100% operational using curated blueprints and rule-based extractors.
