import secrets

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify


class SiteConfiguration(models.Model):
    site_name = models.CharField(max_length=100, default="BALATECH")
    tagline = models.CharField(max_length=200, default="Cloud & Software Development Solutions")
    hero_heading = models.CharField(
        max_length=250,
        default="Building Powerful Digital Solutions for Modern Businesses",
    )
    hero_description = models.TextField(
        default=(
            "We design, develop, and deploy scalable software solutions that help "
            "businesses transform ideas into powerful digital products."
        )
    )
    about_intro = models.TextField(
        default=(
            "I provide backend and cloud application development services, specializing "
            "in scalable application architecture, REST API development, database "
            "management, application security, and cloud deployment."
        )
    )
    about_experience = models.TextField(
        default=(
            "With nearly two years of professional backend development experience, I help "
            "businesses build reliable digital solutions, diagnose technical issues, "
            "resolve database problems, and develop secure applications."
        )
    )
    about_approach = models.TextField(
        default=(
            "My development approach focuses on clean architecture, readable code, "
            "thorough testing, and pragmatic engineering decisions that keep solutions "
            "maintainable and ready to scale."
        )
    )
    career_experience = models.TextField(
        default="Nearly two years of professional backend development experience."
    )
    email = models.EmailField(default="hello@balatech.local")
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=120, blank=True)
    github_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    meta_description = models.TextField(
        default=(
            "BALATECH delivers cloud application development, web development, database "
            "development, and custom software solutions."
        )
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Statistic(models.Model):
    label = models.CharField(max_length=100)
    value = models.PositiveIntegerField()
    suffix = models.CharField(max_length=10, blank=True, help_text="For example: +, %, k")
    icon = models.CharField(max_length=60, blank=True, help_text="Optional emoji or short symbol")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "label"]
        indexes = [models.Index(fields=["is_active", "order"])]

    def __str__(self):
        return f"{self.label}: {self.value}{self.suffix}"


class Technology(models.Model):
    class Category(models.TextChoices):
        LANGUAGE = "language", "Language"
        FRAMEWORK = "framework", "Framework"
        DATABASE = "database", "Database"
        CLOUD = "cloud", "Cloud & DevOps"
        TOOL = "tool", "Tools & Practices"
        API = "api", "API"

    name = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.TOOL)
    icon = models.CharField(max_length=60, blank=True, help_text="Optional short symbol or emoji")
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]
        indexes = [models.Index(fields=["is_active", "order"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    unsubscribe_token = models.CharField(max_length=64, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Newsletter subscriber"
        verbose_name_plural = "Newsletter subscribers"

    def save(self, *args, **kwargs):
        if not self.unsubscribe_token:
            self.unsubscribe_token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class FAQ(models.Model):
    class Category(models.TextChoices):
        GENERAL = "general", "General"
        SERVICES = "services", "Services"
        PROCESS = "process", "Process"
        TECHNICAL = "technical", "Technical"

    question = models.CharField(max_length=250)
    answer = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.GENERAL)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
        ordering = ["order", "question"]
        indexes = [models.Index(fields=["is_active", "order"])]

    def __str__(self):
        return self.question


class Testimonial(models.Model):
    client_name = models.CharField(max_length=120)
    client_role = models.CharField(max_length=120, blank=True)
    company = models.CharField(max_length=120, blank=True)
    message = models.TextField()
    rating = models.PositiveSmallIntegerField(
        default=5, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_active"])]

    def __str__(self):
        return f"{self.client_name} - {self.company}".strip(" -")
