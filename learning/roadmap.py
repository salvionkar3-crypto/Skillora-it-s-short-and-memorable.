"""Personalized Learning Roadmap Generator with deterministic prioritization and optional AI enhancement."""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from analyzer.skills_db import ROLE_REQUIREMENTS


@dataclass
class RoadmapStep:
    """Represents a single milestone step in a learning roadmap."""
    step_number: int
    skill_name: str
    priority: str  # 'High', 'Medium', 'Low'
    reason: str
    learning_objectives: List[str]
    estimated_hours: int
    mini_project: str
    prerequisites: List[str] = field(default_factory=list)


@dataclass
class RoadmapPlan:
    """Complete personalized roadmap plan."""
    target_role: str
    skill_level: str
    total_steps: int
    total_estimated_hours: int
    steps: List[RoadmapStep] = field(default_factory=list)


# Curated learning blueprint metadata for skills
SKILL_BLUEPRINTS: Dict[str, Dict[str, Any]] = {
    "Python": {
        "prereqs": [],
        "base_hours": 20,
        "base_priority": "High",
        "reason": "The core language foundation required for scripting, backend services, and data workloads.",
        "objectives": [
            "Master data structures: lists, dicts, tuples, and sets",
            "Understand functional programming and list comprehensions",
            "Build robust error handling and file I/O operations",
            "Write modular code with functions, classes, and packages"
        ],
        "mini_project": "Personal Task Manager CLI with file persistence and JSON export."
    },
    "SQL": {
        "prereqs": [],
        "base_hours": 15,
        "base_priority": "High",
        "reason": "Indispensable for querying, filtering, and joining relational databases.",
        "objectives": [
            "Write SELECT queries with GROUP BY, HAVING, and Aggregates",
            "Master INNER, LEFT, RIGHT, and FULL OUTER JOINs",
            "Understand subqueries, Common Table Expressions (CTEs), and Window Functions",
            "Learn indexing basics and schema constraints"
        ],
        "mini_project": "E-Commerce Database Schema and Sales Analytics Query Suite."
    },
    "Git": {
        "prereqs": [],
        "base_hours": 8,
        "base_priority": "High",
        "reason": "Essential collaboration and version control standard across all engineering roles.",
        "objectives": [
            "Initialize repos, stage changes, commit, and manage branches",
            "Resolve merge conflicts safely and rebase cleanly",
            "Work with remotes on GitHub: push, pull, PRs, and code reviews",
            "Understand .gitignore and commit hygiene"
        ],
        "mini_project": "Multi-branch Git Workflow Demo with pull requests and merge conflict resolution."
    },
    "HTML5": {
        "prereqs": [],
        "base_hours": 8,
        "base_priority": "High",
        "reason": "The structural backbone of all web applications.",
        "objectives": [
            "Use semantic tags: header, main, nav, section, article",
            "Build accessible forms with client-side validation attributes",
            "Structure clean document trees with meta tags for SEO",
            "Embed audio, video, and responsive images"
        ],
        "mini_project": "Accessible Portfolio Landing Page with validated contact form."
    },
    "CSS3": {
        "prereqs": ["HTML5"],
        "base_hours": 12,
        "base_priority": "High",
        "reason": "Controls the visual presentation, responsive layout, and aesthetics of web interfaces.",
        "objectives": [
            "Master Flexbox alignment and CSS Grid layouts",
            "Build mobile-first responsive media queries",
            "Implement modern CSS variables and smooth transitions",
            "Understand the box model, specificity, and positioning"
        ],
        "mini_project": "Modern Glassmorphism Product Showcase with dynamic theme toggle."
    },
    "JavaScript": {
        "prereqs": ["HTML5"],
        "base_hours": 24,
        "base_priority": "High",
        "reason": "The universal programming language powering frontend interactivity and full-stack runtimes.",
        "objectives": [
            "Master ES6+ syntax: arrow functions, destructuring, modules",
            "Handle asynchronous logic: Promises, async/await, and Fetch API",
            "Manipulate the DOM dynamically and handle event bubbling",
            "Understand closures, scope, and array higher-order methods"
        ],
        "mini_project": "Interactive Kanban Task Board with local storage persistence."
    },
    "TypeScript": {
        "prereqs": ["JavaScript"],
        "base_hours": 14,
        "base_priority": "Medium",
        "reason": "Adds static typing to prevent runtime bugs and improves code maintainability.",
        "objectives": [
            "Define strict interfaces, type aliases, and union types",
            "Utilize generics for reusable components and utility types",
            "Configure tsconfig.json for strict compiler checks",
            "Type React props, events, and API payloads"
        ],
        "mini_project": "Type-Safe Expense Tracker with category analytics."
    },
    "React": {
        "prereqs": ["JavaScript", "HTML5", "CSS3"],
        "base_hours": 25,
        "base_priority": "High",
        "reason": "The most widely adopted UI component library in modern web development.",
        "objectives": [
            "Master JSX, component hierarchy, and props passing",
            "Utilize React Hooks: useState, useEffect, useRef, and useMemo",
            "Handle form inputs, component state, and conditional rendering",
            "Fetch data from REST APIs and manage loading/error states"
        ],
        "mini_project": "Recipe Finder Web App with search filtering and favorites system."
    },
    "FastAPI": {
        "prereqs": ["Python"],
        "base_hours": 16,
        "base_priority": "Medium",
        "reason": "Modern, high-performance web framework for building Python REST APIs with automatic OpenAPI docs.",
        "objectives": [
            "Define route operations, path parameters, and query parameters",
            "Enforce request validation using Pydantic models",
            "Implement dependency injection for auth and database sessions",
            "Handle background tasks and CORS middleware"
        ],
        "mini_project": "RESTful Course Enrollment API with interactive Swagger docs and JWT auth."
    },
    "Django": {
        "prereqs": ["Python", "SQL"],
        "base_hours": 25,
        "base_priority": "Medium",
        "reason": "Batteries-included web framework for building scalable, secure backend systems rapidly.",
        "objectives": [
            "Design relational models and run migrations using Django ORM",
            "Configure views, URL routing, and templates",
            "Build REST endpoints using Django REST Framework (DRF)",
            "Leverage the built-in authentication and admin dashboard"
        ],
        "mini_project": "Student Learning Management Portal with admin dashboard and user authentication."
    },
    "Docker": {
        "prereqs": ["Git"],
        "base_hours": 14,
        "base_priority": "Medium",
        "reason": "Ensures reproducible environments by packaging applications and dependencies into containers.",
        "objectives": [
            "Write multi-stage Dockerfiles for Python/Node apps",
            "Manage container lifecycles, port forwarding, and bind mounts",
            "Orchestrate multi-container setups using Docker Compose",
            "Optimize image size and security best practices"
        ],
        "mini_project": "Containerized Web App with backend service, PostgreSQL DB, and Redis cache."
    },
    "Kubernetes": {
        "prereqs": ["Docker"],
        "base_hours": 20,
        "base_priority": "Medium",
        "reason": "Industry standard for orchestrating container deployment, scaling, and self-healing.",
        "objectives": [
            "Understand Pods, Deployments, ReplicaSets, and Services",
            "Write declarative YAML manifests and manage ConfigMaps/Secrets",
            "Set up Ingress controllers for routing external traffic",
            "Test local deployments using Minikube or Kind"
        ],
        "mini_project": "High-Availability Web Cluster Deployment manifest with rolling update strategy."
    },
    "PostgreSQL": {
        "prereqs": ["SQL"],
        "base_hours": 12,
        "base_priority": "Medium",
        "reason": "The enterprise open-source database of choice with advanced JSON, indexing, and ACID guarantees.",
        "objectives": [
            "Work with JSONB columns and GIN indices",
            "Manage database transactions and isolation levels",
            "Set up foreign key constraints and cascade rules",
            "Perform query optimization with EXPLAIN ANALYZE"
        ],
        "mini_project": "Analytics Data Warehouse Schema with automated trigger functions."
    },
    "Pandas": {
        "prereqs": ["Python"],
        "base_hours": 16,
        "base_priority": "High",
        "reason": "The standard data manipulation library for filtering, grouping, and cleaning datasets.",
        "objectives": [
            "Load, clean, and impute missing values in DataFrames",
            "Perform groupby aggregations, pivots, and merges",
            "Handle datetime transformations and time-series analysis",
            "Export polished summary tables to CSV and Excel"
        ],
        "mini_project": "Automated Financial & Sales Data Cleanser with anomaly report generator."
    },
    "Machine Learning": {
        "prereqs": ["Python", "SQL", "Pandas"],
        "base_hours": 28,
        "base_priority": "High",
        "reason": "Underpins predictive modeling, feature engineering, and intelligent system development.",
        "objectives": [
            "Understand supervised vs unsupervised learning paradigms",
            "Perform feature scaling, train-test splitting, and cross-validation",
            "Train regression, classification, and clustering models",
            "Evaluate models with Precision, Recall, F1-Score, and ROC-AUC"
        ],
        "mini_project": "Customer Churn Prediction Model with feature importance report."
    },
    "Deep Learning": {
        "prereqs": ["Python", "Machine Learning"],
        "base_hours": 30,
        "base_priority": "High",
        "reason": "Enables neural networks for complex vision, speech, and sequence modeling tasks.",
        "objectives": [
            "Understand feedforward networks, activation functions, and backpropagation",
            "Tackle overfitting with Dropout, Batch Normalization, and Early Stopping",
            "Build Convolutional Neural Networks (CNNs) for image recognition",
            "Understand Recurrent Neural Networks and Transformer concepts"
        ],
        "mini_project": "Handwritten Digit & Character Classifier using deep neural networks."
    },
    "PyTorch": {
        "prereqs": ["Python", "Deep Learning"],
        "base_hours": 22,
        "base_priority": "High",
        "reason": "The leading research and production framework for AI and neural network engineering.",
        "objectives": [
            "Understand Tensors, Autograd, and GPU acceleration with CUDA",
            "Define custom neural modules using torch.nn.Module",
            "Build training loops with optimizers and loss functions",
            "Fine-tune pre-trained models from Hugging Face Hub"
        ],
        "mini_project": "Transfer Learning Image Classifier for custom object detection."
    },
    "pytest": {
        "prereqs": ["Python"],
        "base_hours": 8,
        "base_priority": "High",
        "reason": "Guarantees code reliability through automated unit, integration, and regression testing.",
        "objectives": [
            "Write modular test functions with assertions",
            "Use pytest fixtures for test setup and dependency injection",
            "Parameterize tests for comprehensive edge-case coverage",
            "Measure code coverage using pytest-cov"
        ],
        "mini_project": "Comprehensive Test Suite for a REST API with fixture mocking."
    },
    "REST APIs": {
        "prereqs": ["Python"],
        "base_hours": 10,
        "base_priority": "High",
        "reason": "Standard communication protocol connecting frontends, backends, and microservices.",
        "objectives": [
            "Understand HTTP methods: GET, POST, PUT, PATCH, DELETE",
            "Design clean RESTful resource naming and status code standards",
            "Implement pagination, sorting, and header authentication",
            "Handle rate limiting and idempotency"
        ],
        "mini_project": "Public Weather & Geolocation API consumer service."
    },
    "Linux": {
        "prereqs": [],
        "base_hours": 10,
        "base_priority": "Medium",
        "reason": "The operating system running modern cloud servers, containers, and production infrastructure.",
        "objectives": [
            "Navigate the filesystem and manage file permissions (chmod/chown)",
            "Inspect system processes (top, ps, kill) and memory usage",
            "Write basic Bash automation scripts and cron jobs",
            "Manage packages, system services (systemd), and SSH keys"
        ],
        "mini_project": "Automated Linux Server Backup & Health Monitoring Script."
    },
    "Power BI": {
        "prereqs": ["SQL"],
        "base_hours": 14,
        "base_priority": "Medium",
        "reason": "Leading business intelligence tool for creating interactive management dashboards.",
        "objectives": [
            "Import and transform data using Power Query",
            "Build calculated columns and measures with DAX",
            "Design executive dashboards with cross-filtering charts",
            "Configure automated dataset refreshes and reports"
        ],
        "mini_project": "Executive E-Commerce KPI Dashboard with sales trend projections."
    },
    "Tableau": {
        "prereqs": ["SQL"],
        "base_hours": 14,
        "base_priority": "Medium",
        "reason": "Powerful visual analytics platform for enterprise data storytelling.",
        "objectives": [
            "Connect to SQL databases and create live/extract connections",
            "Build bar charts, scatter plots, dual-axis graphs, and maps",
            "Create calculated fields, parameters, and dynamic filters",
            "Publish interactive dashboards with drill-down actions"
        ],
        "mini_project": "Global Healthcare Trends Storyboard with geo-mapping."
    },
    "Data Visualization": {
        "prereqs": ["Python"],
        "base_hours": 10,
        "base_priority": "Medium",
        "reason": "Transforms raw numbers into clear, persuasive visual narratives.",
        "objectives": [
            "Design charts using Matplotlib and Seaborn",
            "Choose appropriate chart types for distributions, correlations, and rankings",
            "Format chart labels, legends, and color scales for accessibility",
            "Build interactive browser charts with Plotly"
        ],
        "mini_project": "Interactive COVID/Vaccine Global Analytics Visualizer."
    },
    "Statistics": {
        "prereqs": [],
        "base_hours": 14,
        "base_priority": "High",
        "reason": "Provides mathematical foundation for testing hypotheses and validating data findings.",
        "objectives": [
            "Understand mean, median, variance, and standard deviation",
            "Master normal distributions, z-scores, and confidence intervals",
            "Perform hypothesis testing (t-tests, chi-square, p-values)",
            "Analyze correlation vs causation and linear regression basics"
        ],
        "mini_project": "A/B Testing Conversion Significance Calculator."
    },
    "NLP": {
        "prereqs": ["Python", "Machine Learning"],
        "base_hours": 20,
        "base_priority": "Medium",
        "reason": "Enables machines to analyze, understand, and derive meaning from human language.",
        "objectives": [
            "Perform tokenization, lemmatization, and stopword removal",
            "Extract features using TF-IDF and word embeddings (Word2Vec)",
            "Build text classification and sentiment analysis pipelines",
            "Explore attention mechanisms and Transformer architectures"
        ],
        "mini_project": "Product Review Sentiment Classifier with keyword extraction."
    },
    "LLMs": {
        "prereqs": ["Python", "NLP"],
        "base_hours": 22,
        "base_priority": "Medium",
        "reason": "Powers the new wave of generative AI, automated reasoning, and semantic search.",
        "objectives": [
            "Prompt engineering techniques: Few-shot, Chain-of-Thought, ReAct",
            "Integrate LLM APIs (Gemini, OpenAI) for structured outputs",
            "Build Retrieval-Augmented Generation (RAG) with vector databases",
            "Evaluate hallucination rates and output guardrails"
        ],
        "mini_project": "Document Q&A Assistant with RAG and semantic vector search."
    },
    "CI/CD": {
        "prereqs": ["Git"],
        "base_hours": 12,
        "base_priority": "Medium",
        "reason": "Automates the building, testing, and deployment of software to production.",
        "objectives": [
            "Write GitHub Actions workflow YAML files",
            "Automate automated testing and linting on pull requests",
            "Configure environment secrets and deploy pipelines",
            "Implement release tagging and rollback triggers"
        ],
        "mini_project": "Automated CI/CD Pipeline testing and building container images on PR merge."
    }
}


class RoadmapGenerator:
    """Generates a prioritized, structured learning roadmap from missing skills."""

    def __init__(self):
        self.blueprints = SKILL_BLUEPRINTS

    def _get_skill_blueprint(self, skill: str) -> Dict[str, Any]:
        """Retrieve or create fallback blueprint for a skill."""
        if skill in self.blueprints:
            return self.blueprints[skill]

        # Generic default blueprint for unlisted skills
        return {
            "prereqs": [],
            "base_hours": 12,
            "base_priority": "Medium",
            "reason": f"Valuable technical skill enhancing capability for modern software and data roles.",
            "objectives": [
                f"Master core syntax and fundamental conventions of {skill}",
                f"Build practical exercises demonstrating key capabilities",
                f"Understand best practices, security, and common pitfalls",
                f"Integrate {skill} with external libraries and tools"
            ],
            "mini_project": f"Demonstration Portfolio Project highlighting practical application of {skill}."
        }

    def generate_roadmap(
        self,
        missing_skills: List[str],
        target_role: str = "Python Developer",
        skill_level: str = "Beginner"
    ) -> RoadmapPlan:
        """
        Generate a sequenced, prioritized learning roadmap from missing skills.
        
        Args:
            missing_skills: List of skills identified as missing.
            target_role: Selected student career path.
            skill_level: 'Beginner', 'Intermediate', or 'Advanced'.
        """
        if not missing_skills:
            return RoadmapPlan(
                target_role=target_role,
                skill_level=skill_level,
                total_steps=0,
                total_estimated_hours=0,
                steps=[]
            )

        # Multiplier based on current skill level
        duration_multipliers = {
            "Beginner": 1.25,
            "Intermediate": 1.0,
            "Advanced": 0.75
        }
        multiplier = duration_multipliers.get(skill_level, 1.0)

        # Get role core skills to boost priority
        role_info = ROLE_REQUIREMENTS.get(target_role, {})
        core_role_skills = set(role_info.get("core", []))

        # Build dependency graph
        remaining_skills = set(missing_skills)
        ordered_skills: List[str] = []

        # Topological sort based on prerequisites
        # Repeatedly select skills whose prerequisites are already satisfied or not in missing_skills
        while remaining_skills:
            # Find candidate skills ready to be learned
            ready = []
            for s in remaining_skills:
                bp = self._get_skill_blueprint(s)
                prereqs = bp.get("prereqs", [])
                # Satisfied if all prereqs are either already scheduled or not in missing skills
                unsatisfied_prereqs = [p for p in prereqs if p in remaining_skills]
                if not unsatisfied_prereqs:
                    ready.append(s)

            if not ready:
                # Cycle or mutual dependency: break ties by picking any core skill or first
                ready = sorted(list(remaining_skills), key=lambda x: (x not in core_role_skills, x))

            # Within ready candidates, prioritize Core role skills first, then High priority blueprints
            def sort_key(skill_name: str):
                is_core = skill_name in core_role_skills
                bp = self._get_skill_blueprint(skill_name)
                priority_val = {"High": 0, "Medium": 1, "Low": 2}.get(bp.get("base_priority", "Medium"), 1)
                return (not is_core, priority_val, skill_name)

            ready.sort(key=sort_key)
            chosen = ready[0]
            ordered_skills.append(chosen)
            remaining_skills.remove(chosen)

        # Build detailed roadmap steps
        steps: List[RoadmapStep] = []
        total_hours = 0

        for idx, skill in enumerate(ordered_skills, start=1):
            bp = self._get_skill_blueprint(skill)
            
            # Determine priority: if core to role, always High
            if skill in core_role_skills:
                priority = "High"
            else:
                priority = bp.get("base_priority", "Medium")

            est_hours = max(4, int(bp.get("base_hours", 12) * multiplier))
            total_hours += est_hours

            step = RoadmapStep(
                step_number=idx,
                skill_name=skill,
                priority=priority,
                reason=bp.get("reason", f"Important requirement for {target_role}."),
                learning_objectives=bp.get("objectives", []),
                estimated_hours=est_hours,
                mini_project=bp.get("mini_project", f"Practical {skill} demo project."),
                prerequisites=bp.get("prereqs", [])
            )
            steps.append(step)

        return RoadmapPlan(
            target_role=target_role,
            skill_level=skill_level,
            total_steps=len(steps),
            total_estimated_hours=total_hours,
            steps=steps
        )
