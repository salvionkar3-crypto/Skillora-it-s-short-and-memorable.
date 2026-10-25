"""Comprehensive Skill Taxonomy, Role Definitions, and Aliases for Skillora AI."""

from typing import Dict, List, Set

# Full taxonomy categorized by domain
SKILL_TAXONOMY: Dict[str, List[str]] = {
    "Programming Languages": [
        "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "Go",
        "Rust", "PHP", "Ruby", "SQL", "HTML5", "CSS3", "Bash"
    ],
    "Frontend Development": [
        "React", "Vue.js", "Angular", "Next.js", "Tailwind CSS", "Redux",
        "Svelte", "Bootstrap", "Responsive Design"
    ],
    "Backend & Frameworks": [
        "Node.js", "Express", "Django", "FastAPI", "Flask", "Spring Boot",
        "ASP.NET Core", "REST APIs", "GraphQL", "Microservices"
    ],
    "Databases & Storage": [
        "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
        "Cassandra", "Elasticsearch"
    ],
    "Cloud & DevOps": [
        "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
        "CI/CD", "GitHub Actions", "Linux", "Nginx", "Git"
    ],
    "AI, ML & Data Science": [
        "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "Pandas",
        "NumPy", "Scikit-Learn", "NLP", "LLMs", "Computer Vision", "Statistics",
        "Power BI", "Tableau", "Data Visualization", "Vector Databases"
    ],
    "Testing & Quality": [
        "pytest", "Unit Testing", "Jest", "Postman", "TDD", "Integration Testing"
    ]
}

# Role metadata and requirement weights
# 'core': essential skills (weight 1.5)
# 'recommended': beneficial skills (weight 1.0)
ROLE_REQUIREMENTS: Dict[str, Dict[str, List[str]]] = {
    "Python Developer": {
        "core": ["Python", "SQL", "Git", "REST APIs", "pytest"],
        "recommended": ["Django", "FastAPI", "Docker", "PostgreSQL", "Linux", "Redis"]
    },
    "AI Engineer": {
        "core": ["Python", "Machine Learning", "Deep Learning", "PyTorch", "Git"],
        "recommended": ["NLP", "LLMs", "Docker", "TensorFlow", "Pandas", "Vector Databases", "MLOps"]
    },
    "Data Analyst": {
        "core": ["SQL", "Python", "Pandas", "Data Visualization", "Statistics"],
        "recommended": ["Power BI", "Tableau", "Excel", "NumPy", "Git", "PostgreSQL"]
    },
    "Web Developer (Full Stack)": {
        "core": ["JavaScript", "HTML5", "CSS3", "React", "Node.js", "Git"],
        "recommended": ["TypeScript", "Express", "MongoDB", "PostgreSQL", "REST APIs", "Docker", "Tailwind CSS"]
    },
    "Cloud & DevOps Engineer": {
        "core": ["Linux", "Docker", "Kubernetes", "AWS", "Git", "CI/CD"],
        "recommended": ["Terraform", "GitHub Actions", "Python", "Bash", "GCP", "Azure", "Nginx"]
    },
    "Frontend Developer": {
        "core": ["JavaScript", "HTML5", "CSS3", "React", "Git", "Responsive Design"],
        "recommended": ["TypeScript", "Next.js", "Tailwind CSS", "Redux", "REST APIs", "Jest"]
    },
    "Backend Developer": {
        "core": ["Python", "SQL", "REST APIs", "Git", "PostgreSQL"],
        "recommended": ["Docker", "FastAPI", "Node.js", "Redis", "Microservices", "Linux", "CI/CD"]
    }
}

ROLE_METADATA: Dict[str, str] = {
    "Python Developer": "Focuses on backend architectures, automation, and API development with clean Python code.",
    "AI Engineer": "Designs, trains, and deploys machine learning and deep learning models and LLM systems.",
    "Data Analyst": "Uncovers actionable insights through statistical analysis, SQL queries, and interactive dashboards.",
    "Web Developer (Full Stack)": "Builds end-to-end modern web applications covering client-side UI and server logic.",
    "Cloud & DevOps Engineer": "Orchestrates scalable cloud infrastructure, CI/CD pipelines, and containerization.",
    "Frontend Developer": "Creates captivating, accessible, and high-performance user interfaces and web experiences.",
    "Backend Developer": "Architects reliable server-side services, databases, caching layers, and secure APIs."
}

# Skill synonyms, aliases, and abbreviations mapping to canonical skill names
SKILL_ALIASES: Dict[str, str] = {
    # Programming Languages
    "py": "Python",
    "python3": "Python",
    "python 3": "Python",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "golang": "Go",
    "go lang": "Go",
    "cpp": "C++",
    "c plus plus": "C++",
    "c#": "C#",
    "c sharp": "C#",
    "csharp": "C#",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "shell script": "Bash",
    "shell scripting": "Bash",
    "bash scripting": "Bash",
    
    # Frontend
    "react.js": "React",
    "reactjs": "React",
    "react": "React",
    "vue": "Vue.js",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "angular.js": "Angular",
    "angularjs": "Angular",
    "next": "Next.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "tailwind-css": "Tailwind CSS",
    
    # Backend
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express.js": "Express",
    "expressjs": "Express",
    "fast api": "FastAPI",
    "fastapi": "FastAPI",
    "restful": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful api": "REST APIs",
    "restful apis": "REST APIs",
    
    # Databases
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "psql": "PostgreSQL",
    "my sql": "MySQL",
    "mysql": "MySQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "elastic search": "Elasticsearch",
    "elastic": "Elasticsearch",
    
    # Cloud & DevOps
    "k8s": "Kubernetes",
    "kube": "Kubernetes",
    "amazon web services": "AWS",
    "aws cloud": "AWS",
    "google cloud": "GCP",
    "google cloud platform": "GCP",
    "azure cloud": "Azure",
    "microsoft azure": "Azure",
    "github actions": "GitHub Actions",
    "gh actions": "GitHub Actions",
    "ci cd": "CI/CD",
    "ci/cd": "CI/CD",
    "continuous integration": "CI/CD",
    
    # AI & ML
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "tf": "TensorFlow",
    "tensorflow": "TensorFlow",
    "torch": "PyTorch",
    "pytorch": "PyTorch",
    "sklearn": "Scikit-Learn",
    "scikit learn": "Scikit-Learn",
    "scikit-learn": "Scikit-Learn",
    "natural language processing": "NLP",
    "nlp": "NLP",
    "large language models": "LLMs",
    "llm": "LLMs",
    "llms": "LLMs",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "data viz": "Data Visualization",
    "data visualization": "Data Visualization",
    "vector db": "Vector Databases",
    "vector dbs": "Vector Databases",
    "vector databases": "Vector Databases",
    
    # Testing
    "unit test": "Unit Testing",
    "unit testing": "Unit Testing",
    "py.test": "pytest",
    "pytest": "pytest"
}
