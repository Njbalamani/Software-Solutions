from django.core.management.base import BaseCommand
from django.db import transaction

from apps.blog.models import BlogCategory
from apps.core.models import FAQ, SiteConfiguration, Statistic, Technology
from apps.portfolio.models import ProjectCategory
from apps.services.models import Service, ServiceCategory


SERVICE_CATEGORIES = [
    "Cloud Development",
    "Web Development",
    "Database Development",
    "Custom Software",
    "Backend & API",
]

PROJECT_CATEGORIES = [
    "Web Applications",
    "Cloud Applications",
    "Backend Systems",
    "Database Applications",
    "Custom Software",
]

BLOG_CATEGORIES = [
    "Python Development",
    "Django Development",
    "Backend Engineering",
    "Cloud Computing",
    "Cybersecurity",
    "Database Management",
    "API Development",
]

TECHNOLOGIES = [
    ("Python", Technology.Category.LANGUAGE, "Py", 1),
    ("Java", Technology.Category.LANGUAGE, "J", 2),
    ("Django", Technology.Category.FRAMEWORK, "Dj", 3),
    ("Spring Boot", Technology.Category.FRAMEWORK, "SB", 4),
    ("MySQL", Technology.Category.DATABASE, "My", 5),
    ("PostgreSQL", Technology.Category.DATABASE, "Pg", 6),
    ("REST APIs", Technology.Category.API, "{ }", 7),
    ("Docker", Technology.Category.CLOUD, "Dk", 8),
    ("AWS", Technology.Category.CLOUD, "AWS", 9),
    ("Git", Technology.Category.TOOL, "Git", 10),
    ("GitHub", Technology.Category.TOOL, "GH", 11),
]

STATISTICS = [
    ("Projects Completed", 0, "", "◇", 1),
    ("Technologies Used", 0, "+", "⌘", 2),
    ("Years of Experience", 0, "", "◷", 3),
    ("Client Satisfaction", 0, "%", "★", 4),
]

FAQS = [
    (FAQ.Category.GENERAL, "What kind of projects do you work on?", "We build web applications, cloud applications, databases, REST APIs, and custom business software. Every engagement is scoped around the specific problem you need solved.", 1),
    (FAQ.Category.PROCESS, "How does a project start?", "Share your requirements through the contact form. We review them, clarify scope and timelines, then agree on a plan before development begins.", 2),
    (FAQ.Category.SERVICES, "Do you work with existing codebases?", "Yes. We can extend, refactor, debug, and optimize existing Django, Python, and Java applications as well as build new systems.", 3),
    (FAQ.Category.TECHNICAL, "Which databases do you support?", "We work primarily with PostgreSQL and MySQL, including schema design, migrations, indexing, and query optimization.", 4),
    (FAQ.Category.TECHNICAL, "Can you deploy applications to the cloud?", "Yes. We handle containerization, server setup, deployment automation, and basic monitoring for cloud-hosted applications.", 5),
    (FAQ.Category.GENERAL, "How do I request a quote?", "Use the contact form with as much detail as possible about your goals, features, and timeline. We respond after reviewing your request.", 6),
]

SERVICES = [
    {
        "category": "Cloud Development",
        "title": "Cloud Application Development",
        "icon": "☁",
        "short_description": "Develop scalable cloud-based applications with secure architecture, deployment automation, and reliable infrastructure.",
        "description": "We design and build cloud-native applications that scale with demand. From architecture and containerization to deployment and monitoring, every layer is engineered for reliability, security, and performance.",
        "features": [
            "Cloud application development", "AWS EC2 deployment", "Docker containerization",
            "Application hosting", "Cloud integration", "Application monitoring", "Performance optimization",
        ],
        "stack": ["Python", "Django", "Docker", "AWS EC2", "Linux", "Git"],
        "benefits": ["Elastic scalability", "Reduced infrastructure overhead", "Automated deployments", "Improved availability"],
        "order": 1,
        "featured": True,
    },
    {
        "category": "Web Development",
        "title": "Web Development",
        "icon": "◇",
        "short_description": "Full-stack web applications built with Django, REST APIs, and modern responsive frontends.",
        "description": "End-to-end web development covering data modeling, backend logic, authentication, REST APIs, and polished responsive interfaces. Applications are built with maintainability and security in mind.",
        "features": [
            "Full-stack web application development", "Django development", "REST API development",
            "Frontend development", "Authentication systems", "Responsive web applications", "Third-party API integration",
        ],
        "stack": ["Python", "Django", "HTML/CSS", "JavaScript", "PostgreSQL", "Git"],
        "benefits": ["Secure by design", "Responsive user experience", "Maintainable codebase", "Fast delivery"],
        "order": 2,
        "featured": True,
    },
    {
        "category": "Database Development",
        "title": "Database Development",
        "icon": "▣",
        "short_description": "Reliable database architecture, data modeling, and performance tuning for MySQL and PostgreSQL.",
        "description": "Database systems designed for accuracy, speed, and growth. We handle schema design, migrations, indexing strategies, query optimization, and ongoing maintenance.",
        "features": [
            "MySQL database development", "PostgreSQL integration", "Database architecture",
            "Database optimization", "Query optimization", "Data modeling", "Database maintenance",
        ],
        "stack": ["MySQL", "PostgreSQL", "Django ORM", "SQL", "Database indexing"],
        "benefits": ["Faster queries", "Data integrity", "Scalable schemas", "Reduced downtime"],
        "order": 3,
        "featured": True,
    },
    {
        "category": "Custom Software",
        "title": "Custom Software Development",
        "icon": "◈",
        "short_description": "Tailored business applications, dashboards, automation, and enterprise software solutions.",
        "description": "Custom software built around real business workflows. We deliver internal tools, management systems, admin dashboards, automation, and integrations that fit the way your team works.",
        "features": [
            "Business management applications", "Custom web applications", "Workflow automation",
            "Admin dashboards", "Enterprise software solutions", "API integrations", "Software maintenance",
        ],
        "stack": ["Python", "Django", "React-ready REST APIs", "MySQL", "PostgreSQL", "Docker"],
        "benefits": ["Built for your workflow", "Improved efficiency", "Long-term maintainability", "Flexible integration"],
        "order": 4,
        "featured": True,
    },
    {
        "category": "Backend & API",
        "title": "Backend Development",
        "icon": "⌘",
        "short_description": "Secure, well-structured backend services and server-side business logic.",
        "description": "Backend systems with clear separation of concerns, strong validation, and comprehensive testing.",
        "features": [
            "Server-side application logic", "Authentication & authorization", "Background task processing",
            "Security hardening", "Error handling and logging", "Unit and integration testing",
        ],
        "stack": ["Python", "Django", "Java", "Spring Boot", "PostgreSQL"],
        "benefits": ["Robust architecture", "Secure operations", "Testable code"],
        "order": 5,
    },
    {
        "category": "Backend & API",
        "title": "REST API Development",
        "icon": "{ }",
        "short_description": "Clean, documented REST APIs for web, mobile, and third-party integrations.",
        "description": "API design and implementation with consistent conventions, validation, pagination, filtering, and documentation.",
        "features": ["RESTful endpoint design", "Request validation", "Pagination and filtering", "API documentation", "Versioning strategy"],
        "stack": ["Django REST Framework", "Swagger/OpenAPI", "Postman", "JSON"],
        "benefits": ["Easy integration", "Clear documentation", "Predictable responses"],
        "order": 6,
    },
    {
        "category": "Backend & API",
        "title": "Microservices Architecture",
        "icon": "◉",
        "short_description": "Decompose complex systems into focused, independently deployable services.",
        "description": "Service decomposition, API contracts, and containerized deployments for systems that need to scale by component.",
        "features": ["Service decomposition", "Inter-service communication", "Containerization", "API gateway patterns"],
        "stack": ["Docker", "REST APIs", "Python", "Django"],
        "benefits": ["Independent scaling", "Fault isolation", "Flexible technology choices"],
        "order": 7,
    },
    {
        "category": "Backend & API",
        "title": "JWT Authentication",
        "icon": "⚿",
        "short_description": "Stateless token-based authentication for modern applications and APIs.",
        "description": "Implementation of secure JWT-based login flows with token refresh, validation, and permission enforcement.",
        "features": ["Token issuance", "Token refresh", "Permission enforcement", "Secure password handling"],
        "stack": ["Django REST Framework", "JWT", "Python"],
        "benefits": ["Stateless sessions", "API-friendly security", "Scalable auth"],
        "order": 8,
    },
    {
        "category": "Backend & API",
        "title": "OAuth 2.0 Integration",
        "icon": "◍",
        "short_description": "Secure delegated authentication with third-party identity providers.",
        "description": "Integration of OAuth 2.0 flows for trusted third-party sign-in and authorized API access.",
        "features": ["Authorization code flow", "Provider integration", "Token handling", "Scope management"],
        "stack": ["OAuth 2.0", "REST APIs", "Python"],
        "benefits": ["Trusted sign-in", "Reduced password handling", "Standards-based security"],
        "order": 9,
    },
    {
        "category": "Backend & API",
        "title": "Bug Fixing",
        "icon": "✚",
        "short_description": "Diagnose and resolve defects, performance regressions, and production issues.",
        "description": "Systematic investigation of issues using logs, reproducible cases, and targeted fixes with regression coverage.",
        "features": ["Issue reproduction", "Root cause analysis", "Targeted fixes", "Regression tests"],
        "stack": ["Python", "Django", "SQL", "Git"],
        "benefits": ["Faster resolution", "Fewer repeat issues", "Improved stability"],
        "order": 10,
    },
    {
        "category": "Backend & API",
        "title": "Postman API Testing",
        "icon": "✓",
        "short_description": "Structured API test suites and automated collection runs.",
        "description": "API test collections covering success paths, validation errors, and authorization scenarios.",
        "features": ["Collection design", "Assertion scripting", "Environment variables", "Automated runs"],
        "stack": ["Postman", "REST APIs", "JSON"],
        "benefits": ["Confident releases", "Documented test cases", "Faster debugging"],
        "order": 11,
    },
    {
        "category": "Backend & API",
        "title": "Swagger Documentation",
        "icon": "▤",
        "short_description": "Interactive, machine-readable API documentation for developers.",
        "description": "OpenAPI/Swagger documentation generated from code, kept accurate as endpoints evolve.",
        "features": ["OpenAPI schema generation", "Interactive Swagger UI", "Request/response examples", "Authentication docs"],
        "stack": ["drf-spectacular", "OpenAPI", "Swagger UI"],
        "benefits": ["Faster onboarding", "Accurate reference", "Easy client generation"],
        "order": 12,
    },
]


class Command(BaseCommand):
    help = "Seed the database with initial site content. Safe to run multiple times."

    @transaction.atomic
    def handle(self, *args, **options):
        SiteConfiguration.get()
        self.stdout.write("Site configuration ready.")

        for name in SERVICE_CATEGORIES:
            ServiceCategory.objects.get_or_create(name=name)
        for name in PROJECT_CATEGORIES:
            ProjectCategory.objects.get_or_create(name=name)
        for name in BLOG_CATEGORIES:
            BlogCategory.objects.get_or_create(name=name)

        for name, category, icon, order in TECHNOLOGIES:
            Technology.objects.get_or_create(
                name=name, defaults={"category": category, "icon": icon, "order": order}
            )

        for label, value, suffix, icon, order in STATISTICS:
            Statistic.objects.get_or_create(
                label=label, defaults={"value": value, "suffix": suffix, "icon": icon, "order": order}
            )

        for category, question, answer, order in FAQS:
            FAQ.objects.get_or_create(
                question=question, defaults={"category": category, "answer": answer, "order": order}
            )

        for item in SERVICES:
            category = ServiceCategory.objects.get(name=item["category"])
            Service.objects.get_or_create(
                title=item["title"],
                defaults={
                    "category": category,
                    "icon": item["icon"],
                    "short_description": item["short_description"],
                    "description": item["description"],
                    "features": "\n".join(item["features"]),
                    "technology_stack": "\n".join(item["stack"]),
                    "benefits": "\n".join(item["benefits"]),
                    "order": item["order"],
                    "is_featured": item.get("featured", False),
                    "is_published": True,
                },
            )

        self.stdout.write(self.style.SUCCESS("Initial content seeded successfully."))
        self.stdout.write(
            "Note: statistic values are set to 0 and testimonials/projects are intentionally left empty. "
            "Update them in Django Admin with genuine data."
        )
