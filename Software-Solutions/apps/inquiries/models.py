from django.db import models
from django.utils import timezone


class ProjectInquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        IN_DISCUSSION = "in_discussion", "In Discussion"
        PROPOSAL_SENT = "proposal_sent", "Proposal Sent"
        COMPLETED = "completed", "Completed"
        REJECTED = "rejected", "Rejected"

    class Budget(models.TextChoices):
        UNDER_1000 = "under_1000", "Under $1,000"
        FROM_1000_TO_5000 = "1000_5000", "$1,000 - $5,000"
        FROM_5000_TO_10000 = "5000_10000", "$5,000 - $10,000"
        FROM_10000_TO_25000 = "10000_25000", "$10,000 - $25,000"
        OVER_25000 = "over_25000", "$25,000+"
        NOT_SURE = "not_sure", "Not sure yet"

    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=30, blank=True)
    company_name = models.CharField(max_length=150, blank=True)
    service = models.ForeignKey(
        "services.Service",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )
    budget = models.CharField(max_length=30, choices=Budget.choices, default=Budget.NOT_SURE)
    description = models.TextField()
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.NEW)
    assigned_to = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_inquiries",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Project Inquiry"
        verbose_name_plural = "Project Inquiries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["email", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.get_status_display()}"

    @property
    def note_count(self):
        return self.notes.count()

    @property
    def sla_breached(self):
        if self.status in (self.Status.COMPLETED, self.Status.REJECTED):
            return False
        return self.created_at < timezone.now() - timezone.timedelta(hours=48)


class InquiryNote(models.Model):
    inquiry = models.ForeignKey(ProjectInquiry, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiry_notes",
    )
    note = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inquiry Note"
        verbose_name_plural = "Inquiry Notes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note on {self.inquiry_id} at {self.created_at:%Y-%m-%d %H:%M}"
