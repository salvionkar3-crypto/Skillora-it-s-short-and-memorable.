"""
Skillora AI — Resume-to-Skills Learning Platform
Main Streamlit Application Entrypoint
"""

import os
import json
from datetime import date, datetime
import streamlit as st

from analyzer.parser import extract_text_from_file, ResumeParseResult
from analyzer.skills_db import ROLE_REQUIREMENTS, ROLE_METADATA, SKILL_TAXONOMY
from analyzer.matcher import SkillMatcher, GapAnalysisResult
from learning.roadmap import RoadmapGenerator, RoadmapPlan
from learning.youtube import YouTubeHub, VideoLesson
from progress.database import (
    init_db,
    get_profile,
    save_profile,
    get_completed_lessons,
    remove_completed_lesson,
    reset_all_progress,
    save_skill_override,
    get_skill_overrides,
    get_db_path,
)
from progress.tracker import ProgressTracker, StreakInfo, ProgressSummary
from ai.gemma_service import get_ai_service, AIHealthStatus


# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="Skillora AI — Resume-to-Skills Learning Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database schema on startup
init_db()

# Initialize Tracker, Matcher, and AI Service
tracker = ProgressTracker()
matcher = SkillMatcher()
roadmap_gen = RoadmapGenerator()
youtube_hub = YouTubeHub()
ai_service = get_ai_service()


@st.cache_data(ttl=15, show_spinner=False)
def check_ai_health() -> AIHealthStatus:
    """Cached Ollama Gemma 3:1B health check to keep UI responsive."""
    return ai_service.check_health()



# ---------------------------------------------------------
# Custom Modern CSS Design System
# ---------------------------------------------------------
CUSTOM_CSS = """
<style>
/* Import Modern Typography */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

/* Hero & Header Styling */
.hero-header {
    background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 50%, #2563EB 100%);
    color: white;
    padding: 2.2rem 2.5rem;
    border-radius: 18px;
    margin-bottom: 2rem;
    box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.3);
}

.hero-title {
    font-size: 2.4rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.02em;
}

.hero-subtitle {
    font-size: 1.1rem;
    opacity: 0.92;
    margin-top: 0.5rem;
    font-weight: 400;
}

/* Metric / Stat Cards */
.stat-card {
    background: #ffffff;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
}

.stat-number {
    font-size: 2.1rem;
    font-weight: 800;
    color: #1E293B;
    line-height: 1.2;
}

.stat-label {
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-top: 0.25rem;
}

/* Badge Pills */
.skill-badge-matched {
    display: inline-block;
    background: #ECFDF5;
    color: #065F46;
    border: 1px solid #A7F3D0;
    border-radius: 9999px;
    padding: 0.35rem 0.85rem;
    font-size: 0.88rem;
    font-weight: 600;
    margin: 0.25rem;
}

.skill-badge-missing {
    display: inline-block;
    background: #FEF2F2;
    color: #991B1B;
    border: 1px solid #FECACA;
    border-radius: 9999px;
    padding: 0.35rem 0.85rem;
    font-size: 0.88rem;
    font-weight: 600;
    margin: 0.25rem;
}

.skill-badge-review {
    display: inline-block;
    background: #FFFBEB;
    color: #92400E;
    border: 1px solid #FDE68A;
    border-radius: 9999px;
    padding: 0.35rem 0.85rem;
    font-size: 0.88rem;
    font-weight: 600;
    margin: 0.25rem;
}

.priority-high {
    background: #FEE2E2;
    color: #991B1B;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.75rem;
    text-transform: uppercase;
}

.priority-medium {
    background: #FEF3C7;
    color: #92400E;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-weight: 700;
    font-size: 0.75rem;
    text-transform: uppercase;
}

/* Roadmap Step Card */
.roadmap-step-card {
    background: #ffffff;
    border: 1px solid #E2E8F0;
    border-left: 6px solid #4F46E5;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
}

/* Video Card */
.video-card {
    background: #ffffff;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.03);
}

/* Streak Banner */
.streak-banner {
    background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
    border: 1px solid #FDBA74;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
    color: #9A3412;
    font-weight: 600;
}

/* Empty State Box */
.empty-state {
    text-align: center;
    padding: 3rem 1.5rem;
    background: #F8FAFC;
    border: 2px dashed #CBD5E1;
    border-radius: 16px;
    margin: 1.5rem 0;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------
if "resume_text" not in st.session_state:
    st.session_state["resume_text"] = ""
if "parsed_result" not in st.session_state:
    st.session_state["parsed_result"] = None
if "resume_filename" not in st.session_state:
    st.session_state["resume_filename"] = ""
if "job_description" not in st.session_state:
    st.session_state["job_description"] = ""
if "target_role" not in st.session_state:
    user_prof = get_profile()
    st.session_state["target_role"] = user_prof.get("target_role", "Python Developer")
    st.session_state["skill_level"] = user_prof.get("skill_level", "Beginner")
    st.session_state["preferred_language"] = user_prof.get("preferred_language", "English")
    st.session_state["daily_goal_minutes"] = user_prof.get("daily_goal_minutes", 30)


# ---------------------------------------------------------
# Realistic Sample Resumes for 1-Click Instant Demo Testing
# ---------------------------------------------------------
DEMO_RESUMES = {
    "Junior Python Developer": (
        "ALEX RIVERA\n"
        "Email: alex.rivera@example.com | GitHub: github.com/alexrivera\n\n"
        "PROFESSIONAL SUMMARY\n"
        "Enthusiastic Junior Software Developer with 1.5 years of experience building Python scripts, "
        "relational databases with SQL, and automation workflows. Strong foundation in object-oriented "
        "programming, Linux environments, and Git version control.\n\n"
        "SKILLS\n"
        "Languages: Python, SQL, Bash\n"
        "Databases & Tools: SQLite, Git, GitHub, Linux\n"
        "Concepts: Object-Oriented Programming, Data Structures, Automation\n\n"
        "PROJECTS\n"
        "1. Automated Inventory Scraper (Python, BeautifulSoup, SQLite)\n"
        "Built scheduled scraper parsing daily stock updates and storing in SQLite.\n"
        "2. Customer Sales CLI Report Tool (Python, SQL)\n"
        "Created command-line utility generating monthly revenue aggregates.\n\n"
        "EDUCATION\n"
        "B.S. in Computer Science, 2024"
    ),
    "Aspiring AI Engineer": (
        "PRIYA SHARMA\n"
        "Email: priya.sharma@example.com | LinkedIn: linkedin.com/in/priyasharma\n\n"
        "SUMMARY\n"
        "Data enthusiast passionate about Artificial Intelligence and Machine Learning. Proficient in Python, "
        "Pandas, NumPy, and statistical hypothesis testing. Completed coursework in Linear Algebra and Probability.\n\n"
        "SKILLS\n"
        "Languages: Python, SQL\n"
        "Libraries: Pandas, NumPy, Scikit-Learn, Matplotlib, Data Visualization\n"
        "Tools: Git, Jupyter Notebook, Statistics\n\n"
        "PROJECTS\n"
        "1. Exploratory Housing Price Predictor (Python, Scikit-Learn, Pandas)\n"
        "Engineered features and evaluated linear regression and random forest models.\n"
        "2. Customer Churn Analysis (SQL, Pandas, Data Visualization)\n"
        "Queried customer transactions and produced exploratory correlation matrices.\n\n"
        "EDUCATION\n"
        "B.Tech in Artificial Intelligence & Data Science, 2025"
    ),
    "Junior Web Developer": (
        "JORDAN LEE\n"
        "Email: jordan.lee@example.com | Portfolio: jordanlee.dev\n\n"
        "SUMMARY\n"
        "Creative Frontend Developer passionate about accessible, responsive web interfaces. Experienced in "
        "HTML5, modern CSS3 (Flexbox/Grid), and vanilla JavaScript (ES6+).\n\n"
        "SKILLS\n"
        "Web Technologies: HTML5, CSS3, JavaScript, Responsive Design\n"
        "Tools & Platforms: Git, GitHub, VS Code\n\n"
        "PROJECTS\n"
        "1. Interactive Restaurant Menu Web App (HTML5, CSS3, JavaScript)\n"
        "Dynamic filtering and shopping cart simulation with localStorage.\n"
        "2. Accessible Personal Portfolio (Semantic HTML5, CSS Variables)\n"
        "Mobile-first portfolio scoring 98 on Lighthouse accessibility.\n\n"
        "EDUCATION\n"
        "Associate Degree in Web Development, 2024"
    )
}


# ---------------------------------------------------------
# Sidebar Navigation & Student Profile
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎓 **Skillora AI**")
    st.caption("Resume-to-Skills Learning Platform")
    
    # Visible Local AI Status Indicator
    ai_health = check_ai_health()
    if ai_health.is_connected and ai_health.model_available:
        ms_text = f"{ai_health.response_time_ms:.0f}ms" if ai_health.response_time_ms else "Active"
        st.markdown(
            f"""
            <div style="background:#ECFDF5; border:1px solid #A7F3D0; border-radius:10px; padding:0.6rem 0.75rem; margin-bottom:0.85rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.85rem; font-weight:700; color:#065F46;">🟢 Gemma 3:1B</span>
                    <span style="font-size:0.7rem; background:#D1FAE5; color:#065F46; padding:0.15rem 0.4rem; border-radius:4px; font-weight:600;">Local AI</span>
                </div>
                <div style="font-size:0.74rem; color:#047857; margin-top:0.25rem;">Ollama active ({ms_text}) • 100% Private</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    elif ai_health.is_connected and not ai_health.model_available:
        st.markdown(
            f"""
            <div style="background:#FFFBEB; border:1px solid #FDE68A; border-radius:10px; padding:0.6rem 0.75rem; margin-bottom:0.85rem;">
                <span style="font-size:0.85rem; font-weight:700; color:#92400E;">🟡 Model Not Loaded</span>
                <div style="font-size:0.74rem; color:#B45309; margin-top:0.25rem;">Run: <code>ollama pull gemma3:1b</code></div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:10px; padding:0.6rem 0.75rem; margin-bottom:0.85rem;">
                <span style="font-size:0.85rem; font-weight:700; color:#475569;">⚪ Local AI: Offline</span>
                <div style="font-size:0.74rem; color:#64748B; margin-top:0.25rem;">Deterministic mode active. Run <code>ollama run gemma3:1b</code></div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Active Streak Widget
    streak_info = tracker.get_streak_info()
    st.markdown(
        f"""
        <div style="background:#EEF2FF; border:1px solid #C7D2FE; border-radius:10px; padding:0.75rem; text-align:center; margin-bottom:1rem;">
            <div style="font-size:1.4rem; font-weight:800; color:#4338CA;">🔥 {streak_info.current_streak} Day Streak</div>
            <div style="font-size:0.75rem; color:#6366F1; font-weight:600;">Best: {streak_info.best_streak} Days | Total: {streak_info.total_active_days} Days Active</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    nav_selection = st.radio(
        "Navigation",
        [
            "📊 Dashboard",
            "📄 Resume Analyzer",
            "🎯 Skill Gap Report",
            "🗺️ Learning Roadmap",
            "📺 YouTube Learning Hub",
            "📈 My Progress",
            "⚙️ Settings"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("#### 👤 Student Profile")
    st.write(f"**Target Role:** {st.session_state['target_role']}")
    st.write(f"**Skill Level:** {st.session_state['skill_level']}")
    st.write(f"**Language:** {st.session_state['preferred_language']}")
    st.write(f"**Daily Goal:** {st.session_state['daily_goal_minutes']} mins")

    if st.button("🔄 Refresh AI Status", key="refresh_ai_sidebar_btn", use_container_width=True):
        check_ai_health.clear()
        st.rerun()

    st.markdown("---")
    st.caption("🔒 Privacy First: In-memory parsing only. Uploaded resumes are never saved or sent to external servers.")



# ---------------------------------------------------------
# SECTION 1: DASHBOARD
# ---------------------------------------------------------
if nav_selection == "📊 Dashboard":
    st.markdown(
        """
        <div class="hero-header">
            <h1 class="hero-title">Skillora AI</h1>
            <p class="hero-subtitle">Turn your resume into a personalized, step-by-step career learning roadmap with verified video tutorials.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Streak alert banner
    st.markdown(
        f"""
        <div class="streak-banner">
            🔥 <strong>Learning Streak:</strong> {streak_info.streak_status_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    # Perform quick analysis on current state
    user_overrides = get_skill_overrides()
    gap_result = matcher.analyze_gaps(
        resume_text=st.session_state["resume_text"],
        target_role=st.session_state["target_role"],
        job_description=st.session_state["job_description"],
        manual_overrides=user_overrides
    )
    roadmap_plan = roadmap_gen.generate_roadmap(
        missing_skills=gap_result.missing_skills,
        target_role=st.session_state["target_role"],
        skill_level=st.session_state["skill_level"]
    )
    progress_summary = tracker.get_progress_summary([s.skill_name for s in roadmap_plan.steps])

    # Top Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">{gap_result.match_score}%</div>
                <div class="stat-label">Role Match Score</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number" style="color:#059669;">{len(gap_result.matched_skills)}</div>
                <div class="stat-label">Skills Matched</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col3:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number" style="color:#DC2626;">{len(gap_result.missing_skills)}</div>
                <div class="stat-label">Skill Gaps to Learn</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col4:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number" style="color:#4F46E5;">{progress_summary.progress_percentage}%</div>
                <div class="stat-label">Roadmap Completed</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Overview split: Status & Quick Action
    left_col, right_col = st.columns([3, 2])
    with left_col:
        st.subheader("🎯 Career Goal Snapshot")
        st.write(f"**Target Role:** {st.session_state['target_role']}")
        st.caption(ROLE_METADATA.get(st.session_state['target_role'], ""))

        if not st.session_state["resume_text"]:
            st.info("💡 You haven't uploaded a resume yet. Upload your PDF/DOCX resume or load a demo candidate to generate your tailored gap report.")
        else:
            st.success(f"✅ Active Resume: **{st.session_state.get('resume_filename', 'Loaded Resume')}** ({len(st.session_state['resume_text'].split())} words)")
            
            st.write("##### Matched Strengths:")
            if gap_result.matched_skills:
                badges = "".join([f'<span class="skill-badge-matched">✓ {s}</span>' for s in gap_result.matched_skills])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.write("No matching role skills detected yet.")

            st.write("##### Next Skills to Learn:")
            if gap_result.missing_skills:
                badges = "".join([f'<span class="skill-badge-missing">! {s}</span>' for s in gap_result.missing_skills[:5]])
                st.markdown(badges, unsafe_allow_html=True)
                if len(gap_result.missing_skills) > 5:
                    st.caption(f"... and {len(gap_result.missing_skills) - 5} more in your roadmap.")
            else:
                st.write("🎉 Congratulations! You have covered all required skills for this role.")

    with right_col:
        st.subheader("⚡ Quick Actions")
        st.markdown("""
        1. **Analyze Resume**: Upload or paste resume to extract detected skills.
        2. **Inspect Gap Report**: Review matched vs missing role requirements.
        3. **Follow Roadmap**: Step-by-step syllabus with time estimates & mini-projects.
        4. **Watch YouTube Lessons**: Verified curated video tutorials in your preferred language.
        5. **Track Streaks**: Mark lessons complete to keep your daily learning streak alive!
        """)
        
        st.write("##### 🚀 Fast Test with Demo Resumes:")
        demo_cols = st.columns(3)
        with demo_cols[0]:
            if st.button("Python Dev Demo", use_container_width=True):
                st.session_state["resume_text"] = DEMO_RESUMES["Junior Python Developer"]
                st.session_state["resume_filename"] = "demo_junior_python_dev.txt"
                st.session_state["target_role"] = "Python Developer"
                save_profile("Python Developer", st.session_state["skill_level"], st.session_state["preferred_language"], st.session_state["daily_goal_minutes"])
                st.rerun()
        with demo_cols[1]:
            if st.button("AI Engineer Demo", use_container_width=True):
                st.session_state["resume_text"] = DEMO_RESUMES["Aspiring AI Engineer"]
                st.session_state["resume_filename"] = "demo_ai_engineer.txt"
                st.session_state["target_role"] = "AI Engineer"
                save_profile("AI Engineer", st.session_state["skill_level"], st.session_state["preferred_language"], st.session_state["daily_goal_minutes"])
                st.rerun()
        with demo_cols[2]:
            if st.button("Web Dev Demo", use_container_width=True):
                st.session_state["resume_text"] = DEMO_RESUMES["Junior Web Developer"]
                st.session_state["resume_filename"] = "demo_web_developer.txt"
                st.session_state["target_role"] = "Web Developer (Full Stack)"
                save_profile("Web Developer (Full Stack)", st.session_state["skill_level"], st.session_state["preferred_language"], st.session_state["daily_goal_minutes"])
                st.rerun()


# ---------------------------------------------------------
# SECTION 2: RESUME ANALYZER
# ---------------------------------------------------------
elif nav_selection == "📄 Resume Analyzer":
    st.title("📄 Resume Analyzer")
    st.markdown("Upload your resume in PDF or DOCX format, or paste your resume text below.")

    tab1, tab2, tab3 = st.tabs(["📤 File Upload (PDF/DOCX)", "✍️ Paste Resume Text", "🎯 Load Sample Resume"])

    with tab1:
        uploaded_file = st.file_uploader(
            "Choose your resume file (PDF or DOCX)",
            type=["pdf", "docx", "txt"],
            help="Your file is parsed in-memory and is never stored permanently on a server."
        )

        if uploaded_file is not None:
            with st.spinner("Extracting and analyzing resume text safely..."):
                parse_result = extract_text_from_file(uploaded_file, uploaded_file.name)
                if parse_result.success:
                    st.session_state["resume_text"] = parse_result.text
                    st.session_state["parsed_result"] = parse_result
                    st.session_state["resume_filename"] = uploaded_file.name
                    st.success(f"Successfully parsed **{uploaded_file.name}** ({parse_result.word_count} words extracted).")
                    if parse_result.warning_message:
                        st.warning(parse_result.warning_message)
                else:
                    st.error(f"Failed to parse resume: {parse_result.error_message}")

    with tab2:
        pasted_text = st.text_area(
            "Paste your resume plain text here:",
            value=st.session_state.get("resume_text", ""),
            height=250,
            placeholder="Paste work experience, skills section, projects, and education..."
        )
        if st.button("Save Pasted Resume Text", type="primary"):
            if pasted_text.strip():
                st.session_state["resume_text"] = pasted_text
                st.session_state["resume_filename"] = "pasted_resume.txt"
                st.success("Resume text saved successfully!")
                st.rerun()
            else:
                st.warning("Please paste some resume text first.")

    with tab3:
        st.write("Need a quick test? Select one of our pre-built realistic resumes to test the analyzer in 1 click:")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Load: Junior Python Dev", key="demo_btn_1"):
                st.session_state["resume_text"] = DEMO_RESUMES["Junior Python Developer"]
                st.session_state["resume_filename"] = "demo_junior_python_dev.txt"
                st.session_state["target_role"] = "Python Developer"
                st.success("Loaded Junior Python Developer resume!")
                st.rerun()
        with c2:
            if st.button("Load: Aspiring AI Engineer", key="demo_btn_2"):
                st.session_state["resume_text"] = DEMO_RESUMES["Aspiring AI Engineer"]
                st.session_state["resume_filename"] = "demo_ai_engineer.txt"
                st.session_state["target_role"] = "AI Engineer"
                st.success("Loaded Aspiring AI Engineer resume!")
                st.rerun()
        with c3:
            if st.button("Load: Junior Web Dev", key="demo_btn_3"):
                st.session_state["resume_text"] = DEMO_RESUMES["Junior Web Developer"]
                st.session_state["resume_filename"] = "demo_web_developer.txt"
                st.session_state["target_role"] = "Web Developer (Full Stack)"
                st.success("Loaded Junior Web Developer resume!")
                st.rerun()

    # Resume preview and extracted skills
    st.markdown("---")
    if st.session_state["resume_text"]:
        st.subheader("🔍 Extraction Insights")
        col_meta1, col_meta2, col_meta3 = st.columns(3)
        words = len(st.session_state["resume_text"].split())
        col_meta1.metric("File Name", st.session_state.get("resume_filename", "Custom Resume"))
        col_meta2.metric("Extracted Words", words)
        
        detected_all = matcher.extract_skills_from_text(st.session_state["resume_text"])
        col_meta3.metric("Detected Skills", len(detected_all))

        st.write("##### All Detected Technical Skills from Resume:")
        if detected_all:
            badges = "".join([f'<span class="skill-badge-matched">{s}</span>' for s in sorted(list(detected_all))])
            st.markdown(badges, unsafe_allow_html=True)
        else:
            st.info("No recognized technical skills were detected. Check the text formatting.")

        with st.expander("📄 View Raw Extracted Resume Text"):
            st.text(st.session_state["resume_text"])

        # AI Evidence & Context Explanation (Gemma 3:1B)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🤖 AI Resume Evidence & Context (Gemma 3:1B)")
        st.markdown(
            "Understand how your skills are demonstrated in your resume. "
            "Gemma 3:1B summarizes specific projects and responsibilities without fabricating unlisted experience."
        )

        ai_status = check_ai_health()
        if not ai_status.is_connected or not ai_status.model_available:
            st.info(
                f"ℹ️ **Local Ollama AI is currently offline.** Showing verified deterministic excerpts. "
                "To enable AI project summaries, run `ollama run gemma3:1b` in PowerShell."
            )

        if detected_all:
            sel_col, btn_col = st.columns([2, 1])
            with sel_col:
                selected_evidence_skill = st.selectbox(
                    "Select a detected skill to inspect evidence & context:",
                    options=sorted(list(detected_all)),
                    key="evidence_skill_select"
                )
            with btn_col:
                st.write("")
                st.write("")
                analyze_clicked = st.button(
                    f"Analyze '{selected_evidence_skill}' Context",
                    type="primary",
                    use_container_width=True
                )

            if analyze_clicked or st.session_state.get("last_analyzed_skill") == selected_evidence_skill:
                st.session_state["last_analyzed_skill"] = selected_evidence_skill
                with st.spinner(f"Analyzing resume context for {selected_evidence_skill} with Gemma 3:1B..."):
                    evidence_result = ai_service.explain_skill_evidence(
                        st.session_state["resume_text"],
                        selected_evidence_skill
                    )

                e_col1, e_col2 = st.columns(2)
                with e_col1:
                    st.markdown("**✓ Verified Ground-Truth Excerpt:**")
                    st.markdown(
                        f"""
                        <div style="background:#F8FAFC; border:1px solid #CBD5E1; border-left:4px solid #059669; border-radius:8px; padding:0.85rem; font-family:monospace; font-size:0.88rem; white-space:pre-wrap;">
{evidence_result['evidence_text']}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    st.caption("Extracted verbatim from resume text using deterministic pattern matching.")

                with e_col2:
                    st.markdown("**🤖 Gemma 3:1B Context Summary:**")
                    if evidence_result["ai_summary"]:
                        st.markdown(
                            f"""
                            <div style="background:#EEF2FF; border:1px solid #C7D2FE; border-left:4px solid #6366F1; border-radius:8px; padding:0.85rem; font-size:0.9rem;">
                                {evidence_result['ai_summary']}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )
                    else:
                        st.info("AI summary unavailable (Ollama offline). Ground-truth excerpt shown on the left.")
                    st.caption(f"Status: {evidence_result['status_note']}")

        st.markdown(
            """
            <div class="empty-state">
                <h3>No Resume Uploaded Yet</h3>
                <p>Upload a PDF/DOCX or pick a demo candidate above to see extraction in action.</p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ---------------------------------------------------------
# SECTION 3: SKILL GAP REPORT
# ---------------------------------------------------------
elif nav_selection == "🎯 Skill Gap Report":
    st.title("🎯 Skill Gap Analysis Report")
    st.markdown("Compare your detected resume skills against industry standards for your target role.")

    # Target Role & JD configuration
    col_role, col_jd = st.columns([1, 1])
    with col_role:
        target_role = st.selectbox(
            "Select Your Target Career Role:",
            options=list(ROLE_REQUIREMENTS.keys()),
            index=list(ROLE_REQUIREMENTS.keys()).index(st.session_state["target_role"])
            if st.session_state["target_role"] in ROLE_REQUIREMENTS else 0
        )
        if target_role != st.session_state["target_role"]:
            st.session_state["target_role"] = target_role
            save_profile(target_role, st.session_state["skill_level"], st.session_state["preferred_language"], st.session_state["daily_goal_minutes"])
            st.rerun()

        st.caption(f"Role Mission: {ROLE_METADATA.get(target_role, '')}")

    with col_jd:
        st.session_state["job_description"] = st.text_area(
            "Optional: Paste Specific Job Description (JD)",
            value=st.session_state.get("job_description", ""),
            height=100,
            placeholder="Paste requirements from a job posting to factor in custom requirements..."
        )

    st.markdown("---")

    # If no resume text, show friendly empty state
    if not st.session_state["resume_text"]:
        st.markdown(
            """
            <div class="empty-state">
                <h3>Awaiting Resume Data</h3>
                <p>Please upload your resume in the Resume Analyzer, or load a sample resume to generate your gap report.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Load Junior Python Developer Demo Now"):
            st.session_state["resume_text"] = DEMO_RESUMES["Junior Python Developer"]
            st.session_state["resume_filename"] = "demo_junior_python_dev.txt"
            st.session_state["target_role"] = "Python Developer"
            st.rerun()
    else:
        # Perform gap analysis with user overrides
        user_overrides = get_skill_overrides()
        gap_result = matcher.analyze_gaps(
            resume_text=st.session_state["resume_text"],
            target_role=st.session_state["target_role"],
            job_description=st.session_state["job_description"],
            manual_overrides=user_overrides
        )

        # Transparent Match Score Box
        st.subheader("📊 Transparent Match Score")
        score_col1, score_col2 = st.columns([1, 2])
        with score_col1:
            st.markdown(
                f"""
                <div style="background:#F8FAFC; border:2px solid #6366F1; border-radius:16px; padding:1.5rem; text-align:center;">
                    <div style="font-size:3rem; font-weight:800; color:#4F46E5;">{gap_result.match_score}%</div>
                    <div style="font-weight:700; color:#334155; margin-top:0.25rem;">Role Keyword Alignment</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with score_col2:
            st.info(f"**How this is calculated:**\n\n{gap_result.score_breakdown}")

        st.markdown("<br>", unsafe_allow_html=True)

        # 3 Categorized Skill Groups
        tab_matched, tab_missing, tab_review = st.tabs([
            f"✅ Matched Skills ({len(gap_result.matched_skills)})",
            f"❌ Skill Gaps to Learn ({len(gap_result.missing_skills)})",
            f"⚠️ Needs Review & Strengths ({len(gap_result.additional_skills) + len(gap_result.needs_review)})"
        ])

        with tab_matched:
            st.write("##### Skills verified in your resume matching this role:")
            if gap_result.matched_skills:
                badges = "".join([f'<span class="skill-badge-matched">✓ {s}</span>' for s in gap_result.matched_skills])
                st.markdown(badges, unsafe_allow_html=True)
                st.caption(f"Core: {', '.join(gap_result.core_matched) or 'None'} | Recommended: {', '.join(gap_result.recommended_matched) or 'None'}")
            else:
                st.warning("No role-specific skills matched yet.")

        with tab_missing:
            st.write("##### Key technical skills missing for this role:")
            if gap_result.missing_skills:
                badges = "".join([f'<span class="skill-badge-missing">✕ {s}</span>' for s in gap_result.missing_skills])
                st.markdown(badges, unsafe_allow_html=True)
                st.caption(f"Core Gaps: {', '.join(gap_result.core_missing) or 'None'} | Recommended Gaps: {', '.join(gap_result.recommended_missing) or 'None'}")
            else:
                st.success("Awesome! You possess all primary skills required for this role.")

        with tab_review:
            st.write("##### Candidate Additional Strengths (Detected in Resume outside this role):")
            if gap_result.additional_skills:
                badges = "".join([f'<span class="skill-badge-review">★ {s}</span>' for s in gap_result.additional_skills])
                st.markdown(badges, unsafe_allow_html=True)
            else:
                st.write("No additional non-role skills detected.")

            if gap_result.needs_review:
                st.write("##### Skills Requested in Job Description:")
                for item in gap_result.needs_review:
                    st.write(f"- {item}")

            if st.session_state.get("job_description", "").strip():
                st.markdown("<br>", unsafe_allow_html=True)
                st.write("##### 🤖 AI Job Description Context (Gemma 3:1B):")
                with st.spinner("Analyzing Job Description context with Gemma 3:1B..."):
                    jd_insights = ai_service.extract_job_insights(
                        st.session_state["job_description"],
                        st.session_state["target_role"],
                        gap_result.jd_skills_detected
                    )
                st.markdown(
                    f"""
                    <div style="background:#F0FDF4; border:1px solid #BBF7D0; border-left:4px solid #16A34A; border-radius:8px; padding:0.85rem; font-size:0.9rem;">
                        {jd_insights['insights']}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if jd_insights.get("status_note"):
                    st.caption(f"ℹ️ {jd_insights['status_note']}")


        # Interactive Confirmation & Skill Overrides
        st.markdown("---")
        st.subheader("🛠️ Verify or Adjust Your Detected Skills")
        st.markdown(
            "Did our deterministic parser miss a skill you possess? Or did it match something you don't know? "
            "You can manually confirm or uncheck skills below:"
        )

        role_info = ROLE_REQUIREMENTS.get(st.session_state["target_role"], {})
        all_role_skills = sorted(list(set(role_info.get("core", []) + role_info.get("recommended", []))))

        override_cols = st.columns(3)
        for idx, skill in enumerate(all_role_skills):
            col_target = override_cols[idx % 3]
            is_matched_currently = skill in gap_result.matched_skills
            
            user_checked = col_target.checkbox(
                f"{skill}",
                value=is_matched_currently,
                key=f"skill_chk_{skill}"
            )

            # If user toggled state, save override to database
            if user_checked != is_matched_currently:
                save_skill_override(skill, user_checked)
                st.rerun()


# ---------------------------------------------------------
# SECTION 4: LEARNING ROADMAP
# ---------------------------------------------------------
elif nav_selection == "🗺️ Learning Roadmap":
    st.title("🗺️ Personalized Learning Roadmap")
    st.markdown("A structured, prioritized step-by-step roadmap to close your skill gaps.")

    user_overrides = get_skill_overrides()
    gap_result = matcher.analyze_gaps(
        resume_text=st.session_state["resume_text"],
        target_role=st.session_state["target_role"],
        job_description=st.session_state["job_description"],
        manual_overrides=user_overrides
    )

    if not gap_result.missing_skills:
        if not st.session_state["resume_text"]:
            st.markdown(
                """
                <div class="empty-state">
                    <h3>No Active Roadmap Available</h3>
                    <p>Upload a resume or load a demo profile to calculate missing skills and generate a tailored roadmap.</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Load Demo Profile & Build Roadmap"):
                st.session_state["resume_text"] = DEMO_RESUMES["Junior Python Developer"]
                st.session_state["resume_filename"] = "demo_junior_python_dev.txt"
                st.session_state["target_role"] = "Python Developer"
                st.rerun()
        else:
            st.success("🎉 You have matched all required skills for this role! No missing skills to roadmap.")
    else:
        roadmap_plan = roadmap_gen.generate_roadmap(
            missing_skills=gap_result.missing_skills,
            target_role=st.session_state["target_role"],
            skill_level=st.session_state["skill_level"]
        )

        # Overview Stats
        stat_c1, stat_c2, stat_c3 = st.columns(3)
        stat_c1.metric("Total Learning Milestones", f"{roadmap_plan.total_steps} Steps")
        stat_c2.metric("Estimated Total Effort", f"{roadmap_plan.total_estimated_hours} Hours")
        days_estimate = max(1, round((roadmap_plan.total_estimated_hours * 60) / max(15, st.session_state["daily_goal_minutes"])))
        stat_c3.metric(f"Timeline (@ {st.session_state['daily_goal_minutes']}m/day)", f"~{days_estimate} Days")

        st.markdown("<br>", unsafe_allow_html=True)

        # AI Career Mentor Strategy (Gemma 3:1B)
        with st.expander("🤖 AI Career Mentor Strategy (Gemma 3:1B)", expanded=True):
            mentor_key = f"mentor_strat_{st.session_state['target_role']}_{len(gap_result.missing_skills)}"
            if mentor_key not in st.session_state or st.button("🔄 Refresh Mentor Advice", key="regen_mentor_btn"):
                with st.spinner("Generating personalized transition advice with Gemma 3:1B..."):
                    st.session_state[mentor_key] = ai_service.generate_mentor_guidance(
                        target_role=st.session_state["target_role"],
                        matched_skills=gap_result.matched_skills,
                        missing_skills=gap_result.missing_skills,
                        skill_level=st.session_state["skill_level"]
                    )
            
            mentor_info = st.session_state[mentor_key]
            st.markdown(mentor_info["guidance"])
            st.caption(f"ℹ️ {mentor_info.get('status_note', 'Grounded mentor advice')}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Display Each Roadmap Step
        completed_records = get_completed_lessons()
        completed_titles = {c["lesson_title"] for c in completed_records}

        for step in roadmap_plan.steps:
            priority_cls = "priority-high" if step.priority == "High" else "priority-medium"
            is_done = f"Roadmap Step: {step.skill_name}" in completed_titles

            status_icon = "✅" if is_done else f"Step {step.step_number}"
            
            with st.container():
                st.markdown(
                    f"""
                    <div class="roadmap-step-card" style="border-left-color: {'#10B981' if is_done else '#4F46E5'};">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h3 style="margin:0; font-size:1.3rem;">{status_icon}: {step.skill_name}</h3>
                            <div>
                                <span class="{priority_cls}">{step.priority} Priority</span>
                                <span style="background:#F1F5F9; color:#475569; padding:0.2rem 0.6rem; border-radius:6px; font-weight:600; font-size:0.75rem; margin-left:0.5rem;">⏱️ ~{step.estimated_hours} Hours</span>
                            </div>
                        </div>
                        <p style="color:#475569; margin-top:0.75rem; font-size:0.95rem;"><strong>Why this matters:</strong> {step.reason}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Objectives & Mini Project inside an expander or container
                col_obj, col_proj = st.columns([1, 1])
                with col_obj:
                    st.write("**Learning Objectives:**")
                    for obj in step.learning_objectives:
                        st.write(f"- {obj}")
                with col_proj:
                    st.write("**Practical Portfolio Mini-Project:**")
                    st.markdown(
                        f"""
                        <div style="background:#F8FAFC; border:1px dashed #CBD5E1; border-radius:8px; padding:0.85rem; font-size:0.9rem;">
                            🛠️ {step.mini_project}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Mark as Complete action button
                lesson_title = f"Roadmap Step: {step.skill_name}"
                btn_col1, btn_col2 = st.columns([1, 3])
                with btn_col1:
                    if not is_done:
                        if st.button(f"Mark Step {step.step_number} Complete", key=f"btn_step_{step.step_number}", type="primary"):
                            success, msg, _ = tracker.record_lesson_completion(
                                skill_name=step.skill_name,
                                lesson_title=lesson_title,
                                lesson_type="roadmap_step"
                            )
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.info(msg)
                    else:
                        if st.button(f"Undo Completion", key=f"undo_step_{step.step_number}"):
                            remove_completed_lesson(step.skill_name, lesson_title)
                            st.rerun()

                st.markdown("---")


# ---------------------------------------------------------
# SECTION 5: YOUTUBE LEARNING HUB
# ---------------------------------------------------------
elif nav_selection == "📺 YouTube Learning Hub":
    st.title("📺 YouTube Learning Hub")
    st.markdown("Curated, verified video lessons to master your skill gaps with zero fabricated links.")

    user_overrides = get_skill_overrides()
    gap_result = matcher.analyze_gaps(
        resume_text=st.session_state["resume_text"],
        target_role=st.session_state["target_role"],
        job_description=st.session_state["job_description"],
        manual_overrides=user_overrides
    )

    # Filter controls
    f_col1, f_col2, f_col3 = st.columns(3)
    
    # Skill choices: gaps first, then all available taxonomy skills
    available_skills = gap_result.missing_skills if gap_result.missing_skills else ["Python", "SQL", "Git", "Docker", "React"]
    for cat_s in SKILL_TAXONOMY.values():
        for s in cat_s:
            if s not in available_skills:
                available_skills.append(s)

    with f_col1:
        selected_skill = st.selectbox("Select Technical Skill:", options=available_skills)
    with f_col2:
        selected_lang = st.selectbox(
            "Preferred Language:",
            options=["English", "Hindi", "Marathi"],
            index=["English", "Hindi", "Marathi"].index(st.session_state["preferred_language"])
            if st.session_state["preferred_language"] in ["English", "Hindi", "Marathi"] else 0
        )
    with f_col3:
        selected_diff = st.selectbox(
            "Difficulty Level:",
            options=["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(st.session_state["skill_level"])
            if st.session_state["skill_level"] in ["Beginner", "Intermediate", "Advanced"] else 0
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Fetch lessons
    lessons = youtube_hub.get_lessons_for_skill(
        skill=selected_skill,
        preferred_language=selected_lang,
        difficulty=selected_diff
    )

    completed_records = get_completed_lessons()
    completed_titles = {c["lesson_title"] for c in completed_records}

    for idx, lesson in enumerate(lessons):
        lesson_key = f"{lesson.skill} - {lesson.title}"
        is_done = lesson_key in completed_titles

        if lesson.is_curated:
            st.markdown(
                f"""
                <div class="video-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h4 style="margin:0; font-size:1.15rem;">{'✅ ' if is_done else ''}{lesson.title}</h4>
                        <span style="background:#DEF7EC; color:#03543F; font-size:0.75rem; font-weight:700; padding:0.25rem 0.6rem; border-radius:6px;">✓ Curated & Verified</span>
                    </div>
                    <p style="color:#64748B; margin:0.35rem 0 0.75rem 0; font-size:0.9rem;">
                        <strong>Channel:</strong> {lesson.channel_name} | <strong>Language:</strong> {lesson.language} | <strong>Level:</strong> {lesson.difficulty}
                        {f' | ⏱️ {lesson.duration_minutes} mins' if lesson.duration_minutes else ''}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Embedded YouTube player
            st.video(lesson.url)

            # Action buttons
            v_col1, v_col2 = st.columns([1, 4])
            with v_col1:
                if not is_done:
                    if st.button("Mark as Complete", key=f"complete_video_{idx}", type="primary"):
                        success, msg, _ = tracker.record_lesson_completion(
                            skill_name=lesson.skill,
                            lesson_title=lesson_key,
                            lesson_type="youtube_video"
                        )
                        if success:
                            st.success(msg)
                            st.rerun()
                else:
                    if st.button("Undo Completion", key=f"undo_video_{idx}"):
                        remove_completed_lesson(lesson.skill, lesson_key)
                        st.rerun()

            with v_col2:
                st.markdown(f"[🔗 Open in New Tab on YouTube]({lesson.url})")

        else:
            # Safe official search fallback
            st.markdown(
                f"""
                <div class="video-card" style="border:1px dashed #F59E0B; background:#FFFBEB;">
                    <h4 style="color:#92400E; margin:0;">🔎 Verified YouTube Search Fallback</h4>
                    <p style="color:#78350F; margin-top:0.4rem; font-size:0.92rem;">{lesson.note}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
            st.markdown(f"👉 [**Search YouTube for '{lesson.skill}' ({lesson.language})**]({lesson.url})")

        st.markdown("---")


# ---------------------------------------------------------
# SECTION 6: MY PROGRESS
# ---------------------------------------------------------
elif nav_selection == "📈 My Progress":
    st.title("📈 Learning Progress & Activity")
    st.markdown("Track your completed milestones, study statistics, and daily streak history.")

    user_overrides = get_skill_overrides()
    gap_result = matcher.analyze_gaps(
        resume_text=st.session_state["resume_text"],
        target_role=st.session_state["target_role"],
        job_description=st.session_state["job_description"],
        manual_overrides=user_overrides
    )
    roadmap_plan = roadmap_gen.generate_roadmap(
        missing_skills=gap_result.missing_skills,
        target_role=st.session_state["target_role"],
        skill_level=st.session_state["skill_level"]
    )
    summary = tracker.get_progress_summary([s.skill_name for s in roadmap_plan.steps])
    streak = tracker.get_streak_info()

    # Stat Row
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Current Streak", f"🔥 {streak.current_streak} Days")
    c2.metric("Best Streak", f"🏆 {streak.best_streak} Days")
    c3.metric("Lessons Completed", f"{summary.completed_lessons_count}")
    c4.metric("Completed Today", f"{summary.completed_today_count}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Progress Bar
    st.write(f"##### Overall Roadmap Progress: {summary.progress_percentage}%")
    st.progress(summary.progress_percentage / 100.0)

    st.markdown("<br>", unsafe_allow_html=True)

    # Completed Lessons Log
    st.subheader("📋 Completed Activity Log")
    completed_items = get_completed_lessons()

    if completed_items:
        for idx, item in enumerate(completed_items):
            c_row1, c_row2, c_row3 = st.columns([3, 1, 1])
            with c_row1:
                st.write(f"**{item['lesson_title']}** ({item['skill_name']})")
                st.caption(f"Type: {item['lesson_type']} | Date: {item['completed_date']}")
            with c_row2:
                st.write("✅ Completed")
            with c_row3:
                if st.button("Delete", key=f"del_item_{idx}"):
                    remove_completed_lesson(item["skill_name"], item["lesson_title"])
                    st.rerun()
            st.markdown("<hr style='margin:0.5rem 0;'>", unsafe_allow_html=True)
    else:
        st.info("No completed lessons yet. Head to the Learning Roadmap or YouTube Hub and mark lessons complete to record progress!")

    st.markdown("---")
    st.write("##### ⚠️ Reset Progress")
    with st.expander("Reset all completion history and streaks"):
        st.warning("This will permanently delete all completed lessons and reset your streak back to 0.")
        if st.button("Confirm Reset Everything", type="primary"):
            reset_all_progress()
            st.success("All progress has been reset.")
            st.rerun()

    st.caption("ℹ️ Data is persisted locally in `skillora.db`. Local SQLite data does not automatically synchronize across devices.")


# ---------------------------------------------------------
# SECTION 7: SETTINGS
# ---------------------------------------------------------
elif nav_selection == "⚙️ Settings":
    st.title("⚙️ Profile & System Settings")
    st.markdown("Customize your career preferences and explore system diagnostics.")

    prof = get_profile()

    with st.form("settings_form"):
        st.subheader("Student Profile Defaults")
        new_role = st.selectbox(
            "Target Career Role:",
            options=list(ROLE_REQUIREMENTS.keys()),
            index=list(ROLE_REQUIREMENTS.keys()).index(prof.get("target_role", "Python Developer"))
        )
        new_level = st.selectbox(
            "Current Experience Level:",
            options=["Beginner", "Intermediate", "Advanced"],
            index=["Beginner", "Intermediate", "Advanced"].index(prof.get("skill_level", "Beginner"))
        )
        new_lang = st.selectbox(
            "Preferred Learning Language:",
            options=["English", "Hindi", "Marathi"],
            index=["English", "Hindi", "Marathi"].index(prof.get("preferred_language", "English"))
        )
        new_goal = st.slider(
            "Daily Learning Goal (minutes):",
            min_value=15,
            max_value=120,
            value=int(prof.get("daily_goal_minutes", 30)),
            step=15
        )

        submitted = st.form_submit_button("Save Profile Settings", type="primary")
        if submitted:
            save_profile(new_role, new_level, new_lang, new_goal)
            st.session_state["target_role"] = new_role
            st.session_state["skill_level"] = new_level
            st.session_state["preferred_language"] = new_lang
            st.session_state["daily_goal_minutes"] = new_goal
            st.success("Profile settings updated successfully!")
            st.rerun()

    st.markdown("---")
    st.subheader("🤖 Local AI Engine Configuration (Gemma 3:1B)")
    st.markdown(
        "Skillora AI integrates locally with Google's open-weight **Gemma 3:1B** model via Ollama. "
        "All resume parsing and prompt inferences run 100% on your local machine with zero data transmitted "
        "to external clouds, zero paid subscriptions, and zero hardcoded secrets."
    )

    ai_diag = check_ai_health()
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.write(f"**Ollama Endpoint:** `{ai_service.base_url}`")
        st.write(f"**Configured Model:** `{ai_service.model_name}`")
        st.write(f"**Connection Status:** {ai_diag.status_summary}")
        if ai_diag.response_time_ms:
            st.write(f"**Health Ping Latency:** `{ai_diag.response_time_ms:.1f} ms`")

    with d_col2:
        st.write(f"**Available Local Models in Ollama:**")
        if ai_diag.available_models:
            for m in ai_diag.available_models:
                st.write(f"- `{m}`")
        else:
            st.caption("None detected (Ollama is offline or no models pulled yet).")

    # Live Interactive Gemma Test Console
    st.markdown("##### 🧪 Live Gemma 3:1B Interactive Test")
    st.caption("Send a live test prompt to Ollama to verify that Gemma 3:1B is loaded and responding.")

    test_prompt = st.text_input(
        "Test Prompt:",
        value="Explain what Skillora AI does in one concise, encouraging sentence.",
        key="test_gemma_prompt_input"
    )

    if st.button("🚀 Run Live Gemma Inference Test", type="primary"):
        with st.spinner("Connecting to local Ollama and running Gemma 3:1B..."):
            test_res = ai_service.generate(prompt=test_prompt, temperature=0.2, max_tokens=100)
            if test_res.success:
                st.success(f"✅ Success! Response generated in {test_res.response_time_ms:.0f}ms by `{test_res.model_used}`:")
                st.markdown(
                    f"""
                    <div style="background:#EEF2FF; border:1px solid #C7D2FE; border-left:4px solid #4F46E5; border-radius:8px; padding:0.85rem; font-size:0.95rem;">
                        {test_res.text}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.error(f"❌ Inference failed: {test_res.error}")

    st.markdown("##### 💻 Windows PowerShell Quick Setup Guide:")
    st.code(
        "# 1. Ensure Ollama is installed and running\n"
        "ollama --version\n\n"
        "# 2. Pull and test Gemma 3:1B (one-time setup)\n"
        "ollama run gemma3:1b\n\n"
        "# 3. Check installed models\n"
        "ollama list",
        language="powershell"
    )

    st.markdown("---")
    st.subheader("💾 Local Persistence Diagnostics")
    st.write(f"**Database Path:** `{get_db_path()}`")
    st.write(f"**Database Exists:** {'Yes' if os.path.exists(get_db_path()) else 'No'}")
    completed_cnt = len(get_completed_lessons())
    st.write(f"**Total Completed Records in DB:** {completed_cnt}")

