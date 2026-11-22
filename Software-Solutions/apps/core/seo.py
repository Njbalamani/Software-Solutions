from xml.sax.saxutils import escape

from django.http import HttpResponse
from django.urls import reverse

from apps.blog.models import BlogPost
from apps.portfolio.models import PortfolioProject
from apps.services.models import Service


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /accounts/",
        f"Sitemap: {request.build_absolute_uri(reverse('core:sitemap'))}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def sitemap_xml(request):
    base = request.build_absolute_uri("/").rstrip("/")
    entries = []

    def add(path, lastmod=None, priority="0.5", changefreq="monthly"):
        entries.append(
            "  <url><loc>{loc}</loc>{lastmod}<changefreq>{freq}</changefreq>"
            "<priority>{priority}</priority></url>".format(
                loc=escape(base + path),
                lastmod=f"<lastmod>{lastmod:%Y-%m-%d}</lastmod>" if lastmod else "",
                freq=changefreq,
                priority=priority,
            )
        )

    add(reverse("core:home"), priority="1.0", changefreq="weekly")
    for name, priority in (
        ("core:about", "0.7"),
        ("services:list", "0.9"),
        ("portfolio:list", "0.8"),
        ("blog:list", "0.8"),
        ("inquiries:contact", "0.9"),
    ):
        add(reverse(name), priority=priority)

    for service in Service.objects.filter(is_published=True):
        add(reverse("services:detail", args=[service.slug]), service.updated_at, "0.8")
    for project in PortfolioProject.objects.filter(is_published=True):
        add(reverse("portfolio:detail", args=[project.slug]), project.updated_at, "0.7")
    for post in BlogPost.objects.filter(is_published=True):
        add(reverse("blog:detail", args=[post.slug]), post.updated_at, "0.7", "weekly")

    xml = '<?xml version="1.0" encoding="UTF-8"?>\n' \
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' \
          + "\n".join(entries) + "\n</urlset>\n"
    return HttpResponse(xml, content_type="application/xml")
