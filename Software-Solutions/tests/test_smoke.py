import json
import xml.etree.ElementTree as ET
from datetime import timedelta

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.utils import timezone
from django.urls import reverse
from rest_framework.test import APIClient

from apps.blog.models import BlogCategory, BlogComment, BlogPost
from apps.core.models import FAQ, NewsletterSubscriber, SiteConfiguration, Statistic, Technology, Testimonial
from apps.inquiries.admin import mark_contacted
from apps.inquiries.models import InquiryNote, ProjectInquiry
from apps.portfolio.models import PortfolioProject, ProjectCategory
from apps.services.models import Service, ServiceCategory

User = get_user_model()


class BaseDataMixin:
    def setUp(self):
        cache.clear()

    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(
            username="admin", email="admin@example.com", password="StrongPass123!",
            is_staff=True, is_superuser=True,
        )
        cls.member = User.objects.create_user(
            username="member", email="member@example.com", password="StrongPass123!"
        )
        cls.service_category = ServiceCategory.objects.create(name="Cloud")
        cls.service = Service.objects.create(
            category=cls.service_category,
            title="Cloud Application Development",
            short_description="Scalable cloud applications.",
            description="Detailed description of cloud application development.",
            features="AWS EC2 deployment\nDocker containerization",
            technology_stack="Python\nDocker\nAWS",
            benefits="Scalability\nReliability",
        )
        cls.project_category = ProjectCategory.objects.create(name="Web Applications")
        cls.project = PortfolioProject.objects.create(
            category=cls.project_category,
            title="Sample Web App",
            short_description="A sample Django web application.",
            description="Full project description for the sample web application.",
            technology_stack="Django\nPostgreSQL",
            is_published=True,
            is_featured=True,
        )
        cls.blog_category = BlogCategory.objects.create(name="Django Development")
        cls.post = BlogPost.objects.create(
            category=cls.blog_category,
            author=cls.admin,
            title="Getting Started with Django",
            excerpt="A short introduction to Django.",
            content="Django is a high-level Python web framework.",
            is_published=True,
        )
        SiteConfiguration.get()
        Statistic.objects.create(label="Projects Completed", value=10)
        Technology.objects.create(name="Python", category=Technology.Category.LANGUAGE, icon="Py")
        Testimonial.objects.create(client_name="Genuine Client", message="Great work.")


class PublicPagesTests(BaseDataMixin, TestCase):
    def test_home_page_loads_with_hero_and_navigation(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "home.html")
        self.assertContains(response, "Building Powerful Digital Solutions")
        self.assertContains(response, "Explore Our Services")
        for name in ("core:about", "services:list", "portfolio:list", "blog:list", "inquiries:contact"):
            self.assertContains(response, reverse(name))

    def test_about_page_loads(self):
        response = self.client.get(reverse("core:about"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "backend and cloud application development services")

    def test_service_list_and_detail(self):
        self.assertEqual(self.client.get(reverse("services:list")).status_code, 200)
        detail = self.client.get(reverse("services:detail", args=[self.service.slug]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "AWS EC2 deployment")
        self.assertEqual(self.client.get("/services/missing-service/").status_code, 404)

    def test_service_category_filter(self):
        response = self.client.get(reverse("services:list") + "?category=" + self.service_category.slug)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.service.title)

    def test_portfolio_list_filter_and_detail(self):
        self.assertEqual(self.client.get(reverse("portfolio:list")).status_code, 200)
        filtered = self.client.get(reverse("portfolio:list") + "?category=" + self.project_category.slug)
        self.assertContains(filtered, self.project.title)
        detail = self.client.get(reverse("portfolio:detail", args=[self.project.slug]))
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "PostgreSQL")

    def test_blog_list_search_and_detail(self):
        self.assertEqual(self.client.get(reverse("blog:list")).status_code, 200)
        search = self.client.get(reverse("blog:list"), {"q": "Django"})
        self.assertContains(search, self.post.title)
        detail = self.client.get(reverse("blog:detail", args=[self.post.slug]))
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(BlogPost.objects.get(pk=self.post.pk).views, 1)

    def test_unknown_page_returns_404_template(self):
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "404", status_code=404)


class ContactTests(BaseDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.payload = {
            "full_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+1 555 123 4567",
            "company_name": "Acme Ltd",
            "service": self.service.pk,
            "budget": ProjectInquiry.Budget.FROM_5000_TO_10000,
            "description": "We need a scalable Django application with REST APIs and cloud deployment.",
        }

    def test_contact_form_get(self):
        response = self.client.get(reverse("inquiries:contact"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Project Description")

    def test_valid_submission_creates_inquiry(self):
        response = self.client.post(reverse("inquiries:contact"), self.payload)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["submitted"])
        self.assertEqual(ProjectInquiry.objects.count(), 1)
        inquiry = ProjectInquiry.objects.first()
        self.assertEqual(inquiry.email, "jane@example.com")
        self.assertEqual(inquiry.status, ProjectInquiry.Status.NEW)

    def test_invalid_submission_does_not_create_inquiry(self):
        payload = dict(self.payload, full_name="J", description="Too short")
        response = self.client.post(reverse("inquiries:contact"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["submitted"])
        self.assertEqual(ProjectInquiry.objects.count(), 0)
        self.assertContains(response, "at least 20 characters")

    def test_duplicate_submission_is_prevented(self):
        self.client.post(reverse("inquiries:contact"), self.payload)
        self.client.post(reverse("inquiries:contact"), self.payload)
        self.assertEqual(ProjectInquiry.objects.count(), 1)

    def test_csrf_protection_enforced_on_post(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("inquiries:contact"), self.payload)
        self.assertEqual(response.status_code, 403)


class AuthenticationTests(BaseDataMixin, TestCase):
    def test_registration_creates_user_and_logs_in(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "newuser",
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "SuperSafePass123!",
            "password2": "SuperSafePass123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertEqual(int(self.client.session["_auth_user_id"]), User.objects.get(username="newuser").pk)

    def test_registration_rejects_weak_or_mismatched_password(self):
        response = self.client.post(reverse("accounts:register"), {
            "username": "weakuser", "email": "weak@example.com",
            "password1": "12345678", "password2": "different",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="weakuser").exists() or
                         User.objects.filter(email="weak@example.com").exists())

    def test_login_and_logout(self):
        response = self.client.post(reverse("accounts:login"), {
            "username": "member", "password": "StrongPass123!"
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.member.pk)
        logout = self.client.post(reverse("accounts:logout"))
        self.assertEqual(logout.status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_reset_page_loads(self):
        self.assertEqual(self.client.get(reverse("accounts:password_reset")).status_code, 200)

    def test_member_account_page_and_staff_redirect(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("accounts:account"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Profile settings")
        self.client.force_login(self.admin)
        self.assertRedirects(
            self.client.get(reverse("accounts:account")),
            reverse("dashboard:index"),
            fetch_redirect_response=False,
        )

    def test_dashboard_requires_login_and_staff(self):
        self.assertRedirects(
            self.client.get(reverse("dashboard:index")),
            reverse("accounts:login") + "?next=" + reverse("dashboard:index"),
        )
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 302)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("dashboard:index")).status_code, 200)


class DashboardTests(BaseDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.inquiry = ProjectInquiry.objects.create(
            full_name="John Smith", email="john@example.com",
            service=self.service, description="A detailed project description for testing.",
        )

    def test_dashboard_statistics(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.context["total_inquiries"], 1)
        self.assertEqual(response.context["new_inquiries"], 1)
        self.assertEqual(response.context["published_services"], 1)
        self.assertContains(response, "Recent messages")

    def test_inquiry_note_status_and_delete(self):
        url = reverse("dashboard:inquiry_detail", args=[self.inquiry.pk])
        response = self.client.post(url, {"action": "add_note", "note": "Called the client."})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(InquiryNote.objects.count(), 1)
        self.client.post(url, {"action": "update_status", "status": ProjectInquiry.Status.CONTACTED})
        self.inquiry.refresh_from_db()
        self.assertEqual(self.inquiry.status, ProjectInquiry.Status.CONTACTED)
        self.client.post(url, {"action": "delete"})
        self.assertFalse(ProjectInquiry.objects.filter(pk=self.inquiry.pk).exists())

    def test_toggle_service_publish(self):
        self.assertTrue(Service.objects.get(pk=self.service.pk).is_published)
        self.client.post(reverse("dashboard:services"), {"pk": self.service.pk})
        self.assertFalse(Service.objects.get(pk=self.service.pk).is_published)

    def test_profile_update(self):
        response = self.client.post(reverse("dashboard:profile"), {
            "first_name": "Ada", "last_name": "Admin", "email": "admin@example.com",
            "phone": "555-1000", "bio": "Backend engineer", "github_url": "", "linkedin_url": "",
        })
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, "Ada")
        self.assertEqual(self.admin.profile.phone, "555-1000")


class APITests(BaseDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.api = APIClient()

    def test_public_list_endpoints(self):
        for name in ("api:service-list", "api:portfolio-list", "api:blog-list"):
            response = self.api.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)
            self.assertIn("results", response.json())
            self.assertEqual(len(response.json()["results"]), 1)

    def test_public_detail_endpoint(self):
        response = self.api.get(reverse("api:service-detail", args=[self.service.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["title"], self.service.title)

    def test_inquiry_create_endpoint(self):
        payload = {
            "full_name": "API User", "email": "api@example.com", "phone": "",
            "company_name": "API Co", "service": self.service.pk,
            "budget": ProjectInquiry.Budget.NOT_SURE,
            "description": "This is a sufficiently long project description for validation.",
        }
        response = self.api.post(reverse("api:inquiry-create"), payload, format="json")
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(ProjectInquiry.objects.count(), 1)

    def test_inquiry_create_rejects_invalid_data(self):
        response = self.api.post(reverse("api:inquiry-create"), {
            "full_name": "X", "email": "not-an-email", "service": self.service.pk,
            "budget": "bad", "description": "short",
        }, format="json")
        self.assertEqual(response.status_code, 400)

    def test_inquiry_list_requires_admin(self):
        response = self.api.get(reverse("api:inquiry-list"))
        self.assertIn(response.status_code, (401, 403))
        self.api.force_authenticate(user=self.member)
        self.assertEqual(self.api.get(reverse("api:inquiry-list")).status_code, 403)
        self.api.force_authenticate(user=self.admin)
        self.assertEqual(self.api.get(reverse("api:inquiry-list")).status_code, 200)

    def test_api_documentation(self):
        self.assertEqual(self.client.get(reverse("api-docs")).status_code, 200)
        response = self.client.get(reverse("api-schema") + "?format=json")
        self.assertEqual(response.status_code, 200)
        self.assertIn("paths", json.loads(response.content))
class ExtendedFeaturesTests(BaseDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)
        self.api = APIClient()

    def test_dashboard_service_crud(self):
        payload = {
            "category": self.service_category.pk,
            "title": "DevOps Automation",
            "icon": "⚙",
            "short_description": "Automated CI/CD pipelines and infrastructure.",
            "description": "Complete pipeline design, automation, and monitoring.",
            "features": "CI/CD pipelines\nInfrastructure as code",
            "technology_stack": "Docker\nGitHub Actions",
            "benefits": "Faster releases",
            "order": 20,
            "is_published": "on",
        }
        response = self.client.post(reverse("dashboard:service_create"), payload)
        self.assertEqual(response.status_code, 302)
        created = Service.objects.get(title="DevOps Automation")
        self.assertTrue(created.is_published)
        self.assertEqual(created.features_list, ["CI/CD pipelines", "Infrastructure as code"])

        response = self.client.post(reverse("dashboard:service_edit", args=[created.pk]), dict(payload, title="DevOps & Automation"))
        self.assertEqual(response.status_code, 302)
        created.refresh_from_db()
        self.assertEqual(created.title, "DevOps & Automation")

        response = self.client.post(reverse("dashboard:service_delete", args=[created.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Service.objects.filter(pk=created.pk).exists())

    def test_dashboard_blog_create_sets_author(self):
        response = self.client.post(reverse("dashboard:blog_create"), {
            "category": self.blog_category.pk,
            "title": "Testing Django Applications",
            "excerpt": "Why automated tests matter.",
            "content": "Tests protect against regressions.",
            "is_published": "on",
        })
        self.assertEqual(response.status_code, 302)
        post = BlogPost.objects.get(title="Testing Django Applications")
        self.assertEqual(post.author, self.admin)
        self.assertIsNotNone(post.published_at)

    def test_dashboard_portfolio_create(self):
        response = self.client.post(reverse("dashboard:portfolio_create"), {
            "category": self.project_category.pk,
            "title": "Internal Dashboard",
            "short_description": "Admin panel for operations.",
            "description": "A complete admin dashboard application.",
            "technology_stack": "Django\nPostgreSQL",
            "order": 5,
            "is_published": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PortfolioProject.objects.filter(title="Internal Dashboard").exists())

    def test_unauthorized_dashboard_crud_blocked(self):
        self.client.logout()
        response = self.client.get(reverse("dashboard:service_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("accounts:login"), response["Location"])
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("dashboard:service_create")).status_code, 302)

    def test_token_authentication_for_protected_api(self):
        self.assertEqual(self.api.get(reverse("api:inquiry-list")).status_code, 403)
        response = self.api.post(reverse("api-token"), {"username": "admin", "password": "StrongPass123!"})
        self.assertEqual(response.status_code, 200)
        token = response.json()["token"]
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {token}")
        self.assertEqual(self.api.get(reverse("api:inquiry-list")).status_code, 200)

    def test_robots_and_sitemap(self):
        robots = self.client.get(reverse("core:robots"))
        self.assertEqual(robots.status_code, 200)
        self.assertIn(b"Sitemap:", robots.content)
        sitemap = self.client.get(reverse("core:sitemap"))
        self.assertEqual(sitemap.status_code, 200)
        self.assertIn(self.service.slug.encode(), sitemap.content)
        root = ET.fromstring(sitemap.content)
        self.assertEqual(root.tag.endswith("urlset"), True)
        self.assertGreater(len(root), 5)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_HOST="smtp.example.com",
        CONTACT_EMAIL="hello@example.com",
    )
    def test_api_inquiry_sends_email_notification(self):
        mail.outbox = []
        payload = {
            "full_name": "Notify Me", "email": "notify@example.com", "phone": "",
            "company_name": "", "service": self.service.pk,
            "budget": ProjectInquiry.Budget.NOT_SURE,
            "description": "A detailed request used to verify email notification delivery.",
        }
        response = self.api.post(reverse("api:inquiry-create"), payload, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn("Notify Me", mail.outbox[0].subject)
        self.assertEqual(mail.outbox[1].to, ["notify@example.com"])

    def test_contact_rate_limit(self):
        for index in range(5):
            payload = dict(self._contact_payload(), email=f"user{index}@example.com")
            response = self.client.post(reverse("inquiries:contact"), payload)
            self.assertTrue(response.context["submitted"])
        self.assertEqual(ProjectInquiry.objects.count(), 5)
        response = self.client.post(reverse("inquiries:contact"), self._contact_payload())
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["submitted"])
        self.assertEqual(ProjectInquiry.objects.count(), 5)

    def _contact_payload(self):
        return {
            "full_name": "Rate Test", "email": "rate@example.com", "phone": "",
            "company_name": "", "service": self.service.pk,
            "budget": ProjectInquiry.Budget.NOT_SURE,
            "description": "This is a sufficiently detailed project description for the form.",
        }


class AdditionalFeaturesTests(BaseDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.faq = FAQ.objects.create(
            question="How does a project start?", answer="Send us your requirements.", order=1
        )

    def test_global_search_finds_published_content(self):
        response = self.client.get(reverse("core:search"), {"q": "cloud"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.service.title)
        self.assertContains(response, "result")
        response = self.client.get(reverse("core:search"), {"q": "zzzznotfound"})
        self.assertContains(response, "No results found")

    def test_faq_appears_on_home_page(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.faq.question)
        self.assertContains(response, "faq-item")

    def test_inquiry_csv_export(self):
        self.client.force_login(self.admin)
        ProjectInquiry.objects.create(
            full_name="CSV Client", email="csv@example.com", service=self.service,
            description="Exported inquiry", budget=ProjectInquiry.Budget.NOT_SURE,
        )
        response = self.client.get(reverse("dashboard:inquiries"), {"export": "csv"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("CSV Client", response.content.decode())

    def test_dashboard_trend_context(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["inquiry_trend"]), 7)
        self.assertEqual(response.context["inquiry_trend"][-1][1], 0)

    def test_contact_honeypot_rejects_bot(self):
        payload = {
            "full_name": "Bot", "email": "bot@example.com", "phone": "", "company_name": "",
            "service": self.service.pk, "budget": ProjectInquiry.Budget.NOT_SURE,
            "description": "This is a long enough description to pass normal validation checks.",
            "website": "https://spam.example.com",
        }
        response = self.client.post(reverse("inquiries:contact"), payload)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(ProjectInquiry.objects.exists())

    def test_custom_403_page(self):
        response = self.client.get(reverse("core:home"), follow=False)
        request = response.wsgi_request
        from apps.core.views import error_403
        rendered = error_403(request, None)
        self.assertEqual(rendered.status_code, 403)
        self.assertIn(b"Access denied", rendered.content)

    def test_admin_bulk_status_action(self):
        inquiry = ProjectInquiry.objects.create(
            full_name="Bulk Client", email="bulk@example.com", service=self.service,
            description="Bulk status update", budget=ProjectInquiry.Budget.NOT_SURE,
        )
        mark_contacted(None, None, ProjectInquiry.objects.filter(pk=inquiry.pk))
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.status, ProjectInquiry.Status.CONTACTED)


class EngagementFeaturesTests(BaseDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_newsletter_subscribe_duplicate_and_unsubscribe(self):
        response = self.client.post(reverse("core:newsletter_subscribe"), {"email": "News@Example.com"})
        self.assertEqual(response.status_code, 302)
        subscriber = NewsletterSubscriber.objects.get(email="news@example.com")
        self.assertTrue(subscriber.is_active)
        self.assertTrue(subscriber.unsubscribe_token)
        self.client.post(reverse("core:newsletter_subscribe"), {"email": "news@example.com"})
        self.assertEqual(NewsletterSubscriber.objects.count(), 1)
        response = self.client.get(reverse("core:newsletter_unsubscribe", args=[subscriber.unsubscribe_token]))
        self.assertEqual(response.status_code, 302)
        subscriber.refresh_from_db()
        self.assertFalse(subscriber.is_active)

    def test_newsletter_honeypot_rejects_bot(self):
        self.client.post(reverse("core:newsletter_subscribe"), {
            "email": "bot@example.com", "website": "https://spam.example.com"
        })
        self.assertFalse(NewsletterSubscriber.objects.exists())

    def test_newsletter_dashboard_csv(self):
        NewsletterSubscriber.objects.create(email="csv@example.com")
        response = self.client.get(reverse("dashboard:newsletters") + "?export=csv")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csv@example.com", response.content.decode())

    def test_blog_comment_submission_and_moderation(self):
        payload = {
            "author_name": "Reader", "author_email": "reader@example.com",
            "content": "This was a helpful article about Django.",
        }
        response = self.client.post(reverse("blog:detail", args=[self.post.slug]), payload)
        self.assertEqual(response.status_code, 302)
        comment = BlogComment.objects.get()
        self.assertFalse(comment.is_approved)
        detail = self.client.get(reverse("blog:detail", args=[self.post.slug]))
        self.assertNotContains(detail, comment.content)
        self.client.post(reverse("dashboard:comments"), {"pk": comment.pk, "approve": "1"})
        comment.refresh_from_db()
        self.assertTrue(comment.is_approved)
        detail = self.client.get(reverse("blog:detail", args=[self.post.slug]))
        self.assertContains(detail, comment.content)

    def test_blog_comment_honeypot_rejects_bot(self):
        self.client.post(reverse("blog:detail", args=[self.post.slug]), {
            "author_name": "Bot", "author_email": "bot@example.com",
            "content": "This is a sufficiently long spam comment.", "website": "https://spam.example.com",
        })
        self.assertFalse(BlogComment.objects.exists())

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        EMAIL_HOST="smtp.example.com",
        CONTACT_EMAIL="hello@example.com",
    )
    def test_auto_reply_sent_to_submitter(self):
        mail.outbox = []
        payload = {
            "full_name": "Reply Me", "email": "reply@example.com", "phone": "", "company_name": "",
            "service": self.service.pk, "budget": ProjectInquiry.Budget.NOT_SURE,
            "description": "A detailed inquiry that should generate both notification emails.",
        }
        response = self.client.post(reverse("inquiries:contact"), payload)
        self.assertTrue(response.context["submitted"])
        self.assertEqual(len(mail.outbox), 2)
        self.assertEqual(mail.outbox[1].to, ["reply@example.com"])
        self.assertIn("We received your inquiry", mail.outbox[1].subject)

    def test_json_ld_structured_data(self):
        self.assertIn('"@type":"Organization"', self.client.get(reverse("core:home")).content.decode())
        self.assertIn('"@type":"Service"', self.client.get(reverse("services:detail", args=[self.service.slug])).content.decode())
        self.assertIn('"@type":"BlogPosting"', self.client.get(reverse("blog:detail", args=[self.post.slug])).content.decode())

    def test_admin_is_branded(self):
        self.assertEqual(admin.site.site_header, "BALATECH Administration")
        self.assertEqual(admin.site.site_title, "BALATECH Admin")


class HardeningFeaturesTests(BaseDataMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.admin)

    def test_security_headers_on_responses(self):
        response = self.client.get(reverse("core:home"))
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")

    def test_health_endpoint(self):
        response = self.client.get(reverse("core:health"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "database": "ok"})

    def test_view_tracking_and_dashboard_panel(self):
        url = reverse("services:detail", args=[self.service.slug])
        self.client.get(url)
        self.client.get(url)
        self.service.refresh_from_db()
        self.assertEqual(self.service.views, 2)
        dashboard = self.client.get(reverse("dashboard:index"))
        self.assertContains(dashboard, "Most viewed content")
        self.assertTrue(any(title == self.service.title for title, _, _ in dashboard.context["most_viewed"]))

    def test_inquiry_assignment(self):
        inquiry = ProjectInquiry.objects.create(
            full_name="Assign Me", email="assign@example.com", service=self.service,
            description="Assign this inquiry for testing.", budget=ProjectInquiry.Budget.NOT_SURE,
        )
        url = reverse("dashboard:inquiry_detail", args=[inquiry.pk])
        response = self.client.post(url, {"action": "assign", "assigned_to": self.admin.pk})
        self.assertEqual(response.status_code, 302)
        inquiry.refresh_from_db()
        self.assertEqual(inquiry.assigned_to, self.admin)

    def test_sla_breached_filter_and_property(self):
        inquiry = ProjectInquiry.objects.create(
            full_name="Late Client", email="late@example.com", service=self.service,
            description="This inquiry has been waiting too long.", budget=ProjectInquiry.Budget.NOT_SURE,
        )
        ProjectInquiry.objects.filter(pk=inquiry.pk).update(created_at=timezone.now() - timedelta(days=3))
        inquiry.refresh_from_db()
        self.assertTrue(inquiry.sla_breached)
        response = self.client.get(reverse("dashboard:inquiries") + "?sla=breached")
        self.assertContains(response, "Late Client")
        self.assertNotContains(response, "SLA breaches (0)")

    def test_theme_toggle_present(self):
        self.assertContains(self.client.get(reverse("core:home")), 'id="themeToggle"')
