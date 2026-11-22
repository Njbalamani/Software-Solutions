from django.contrib import messages
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from apps.blog.models import BlogPost
from apps.core.forms import NewsletterForm
from apps.core.models import FAQ, NewsletterSubscriber, SiteConfiguration, Statistic, Technology, Testimonial
from apps.portfolio.models import PortfolioProject
from apps.services.models import Service


def home(request):
    return render(
        request,
        "home.html",
        {
            "services": Service.objects.filter(is_published=True).select_related("category").order_by("order")[:4],
            "technologies": Technology.objects.filter(is_active=True),
            "statistics": Statistic.objects.filter(is_active=True),
            "testimonials": Testimonial.objects.filter(is_active=True),
            "faqs": FAQ.objects.filter(is_active=True),
            "featured_projects": PortfolioProject.objects.filter(is_published=True, is_featured=True)
            .select_related("category")
            .order_by("-created_at")[:3],
            "recent_posts": BlogPost.objects.filter(is_published=True)
            .select_related("category", "author")
            .order_by("-published_at")[:3],
        },
    )


def about(request):
    return render(
        request,
        "about.html",
        {
            "site": SiteConfiguration.get(),
            "statistics": Statistic.objects.filter(is_active=True),
            "technologies": Technology.objects.filter(is_active=True),
        },
    )


def search(request):
    query = request.GET.get("q", "").strip()
    services = Service.objects.none()
    projects = PortfolioProject.objects.none()
    posts = BlogPost.objects.none()
    if query:
        services = Service.objects.filter(is_published=True).filter(
            Q(title__icontains=query) | Q(short_description__icontains=query) | Q(description__icontains=query)
        ).select_related("category")
        projects = PortfolioProject.objects.filter(is_published=True).filter(
            Q(title__icontains=query) | Q(short_description__icontains=query) | Q(technology_stack__icontains=query)
        ).select_related("category")
        posts = BlogPost.objects.filter(is_published=True).filter(
            Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query)
        ).select_related("category")
    return render(
        request,
        "search.html",
        {
            "query": query,
            "services": services,
            "projects": projects,
            "posts": posts,
            "total": services.count() + projects.count() + posts.count(),
        },
    )


def newsletter_subscribe(request):
    if request.method != "POST":
        return redirect("core:home")
    form = NewsletterForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data["email"]
        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email, defaults={"is_active": True}
        )
        if not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save(update_fields=["is_active"])
            messages.success(request, "You're subscribed again. Welcome back!")
        elif created:
            messages.success(request, "You're subscribed. Thank you!")
        else:
            messages.info(request, "This email is already subscribed.")
    else:
        messages.error(request, "Please enter a valid email address.")
    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        next_url = ""
    return redirect(next_url or "core:home")


def newsletter_unsubscribe(request, token):
    subscriber = NewsletterSubscriber.objects.filter(unsubscribe_token=token, is_active=True).first()
    if subscriber:
        subscriber.is_active = False
        subscriber.save(update_fields=["is_active"])
        messages.success(request, "You have been unsubscribed from the newsletter.")
    else:
        messages.info(request, "This subscription is already inactive.")
    return redirect("core:home")


def health(request):
    try:
        connection.ensure_connection()
        database = "ok"
    except Exception:
        database = "unavailable"
    status = 200 if database == "ok" else 503
    return JsonResponse({"status": "ok" if database == "ok" else "degraded", "database": database}, status=status)


def error_403(request, exception):
    return render(request, "403.html", status=403)


def error_404(request, exception):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)
