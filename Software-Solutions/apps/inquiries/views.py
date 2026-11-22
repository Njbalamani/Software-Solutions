from django.contrib import messages
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.inquiries.forms import ContactForm
from apps.inquiries.models import ProjectInquiry
from apps.inquiries.services import (
    client_ip,
    is_rate_limited,
    notify_admin,
    notify_submitter,
    record_submission,
)
from apps.services.models import Service


@require_http_methods(["GET", "POST"])
def contact(request):
    initial = {}
    service_slug = request.GET.get("service")
    if service_slug:
        initial["service"] = Service.objects.filter(slug=service_slug, is_published=True).values_list("pk", flat=True).first()

    if request.method == "POST":
        if is_rate_limited(request):
            messages.error(
                request,
                "Too many submissions in a short time. Please try again in a few minutes or email us directly.",
            )
            return render(request, "contact.html", {"form": ContactForm(), "submitted": False})

        form = ContactForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            description = form.cleaned_data["description"]
            recent = timezone.now() - timezone.timedelta(minutes=10)
            duplicate = ProjectInquiry.objects.filter(
                email__iexact=email,
                description=description,
                created_at__gte=recent,
            ).exists()
            if duplicate:
                messages.warning(
                    request,
                    "This inquiry was already submitted recently. We have your request and will be in touch.",
                )
                return render(request, "contact.html", {"form": ContactForm(), "submitted": True})

            record_submission(request)
            inquiry = form.save(commit=False)
            inquiry.ip_address = client_ip(request)
            inquiry.save()
            notify_admin(inquiry)
            notify_submitter(inquiry)
            messages.success(
                request,
                "Thank you! Your project inquiry has been received. We will contact you soon.",
            )
            return render(request, "contact.html", {"form": ContactForm(), "submitted": True})
    else:
        form = ContactForm(initial=initial)

    return render(request, "contact.html", {"form": form, "submitted": False})
