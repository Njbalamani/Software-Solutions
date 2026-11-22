import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = 600
RATE_LIMIT_MAX_SUBMISSIONS = 5


def client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or "unknown"


def _rate_limit_key(request):
    return f"inquiry-rate:{client_ip(request)}"


def is_rate_limited(request):
    attempts = cache.get(_rate_limit_key(request), [])
    cutoff = timezone.now().timestamp() - RATE_LIMIT_WINDOW_SECONDS
    recent = [timestamp for timestamp in attempts if timestamp > cutoff]
    return len(recent) >= RATE_LIMIT_MAX_SUBMISSIONS


def record_submission(request):
    key = _rate_limit_key(request)
    attempts = cache.get(key, [])
    now = timezone.now().timestamp()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    recent = [timestamp for timestamp in attempts if timestamp > cutoff]
    recent.append(now)
    cache.set(key, recent, RATE_LIMIT_WINDOW_SECONDS)


def _email_enabled():
    backend = settings.EMAIL_BACKEND.lower()
    disabled_backends = ("console", "dummy", "filebased")
    return bool(settings.EMAIL_HOST) and not any(name in backend for name in disabled_backends)


def notify_admin(inquiry):
    if not _email_enabled():
        return
    subject = f"New project inquiry from {inquiry.full_name}"
    body = (
        f"Name: {inquiry.full_name}\n"
        f"Email: {inquiry.email}\n"
        f"Phone: {inquiry.phone or '-'}\n"
        f"Company: {inquiry.company_name or '-'}\n"
        f"Service: {inquiry.service.title if inquiry.service else '-'}\n"
        f"Budget: {inquiry.get_budget_display()}\n\n"
        f"Description:\n{inquiry.description}\n"
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [settings.CONTACT_EMAIL], fail_silently=False)
    except Exception:
        logger.exception("Failed to send inquiry notification email")


def notify_submitter(inquiry):
    if not _email_enabled():
        return
    subject = "We received your inquiry — BALATECH"
    body = (
        f"Hi {inquiry.full_name},\n\n"
        "Thank you for contacting us. We have received your project inquiry and will review it shortly.\n\n"
        f"Service: {inquiry.service.title if inquiry.service else '-'}\n"
        f"Submitted: {inquiry.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        "We'll get back to you soon.\n\n"
        "— BALATECH"
    )
    try:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [inquiry.email], fail_silently=False)
    except Exception:
        logger.exception("Failed to send inquiry confirmation email")
