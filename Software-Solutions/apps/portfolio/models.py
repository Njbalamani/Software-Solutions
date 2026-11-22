from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class ProjectCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Project Category"
        verbose_name_plural = "Project Categories"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class PortfolioProject(models.Model):
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    title = models.CharField(max_length=150)
    slug = models.SlugField(max_length=150, unique=True, blank=True)
    short_description = models.TextField(max_length=400)
    description = models.TextField()
    screenshot = models.ImageField(upload_to="projects/", blank=True, null=True)
    technology_stack = models.TextField(help_text="One technology per line")
    github_url = models.URLField(blank=True)
    live_demo_url = models.URLField(blank=True)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    completed_date = models.DateField(blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Portfolio Project"
        verbose_name_plural = "Portfolio Projects"
        ordering = ["order", "-created_at"]
        indexes = [models.Index(fields=["is_published", "category"])]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def clean(self):
        if self.screenshot:
            if self.screenshot.size > 5 * 1024 * 1024:
                raise ValidationError({"screenshot": "Image file too large (maximum 5MB)."})
            valid = (".jpg", ".jpeg", ".png", ".webp", ".gif")
            if not self.screenshot.name.lower().endswith(valid):
                raise ValidationError({"screenshot": "Unsupported image format. Use JPG, PNG, WEBP or GIF."})

    @property
    def technologies_list(self):
        return [line.strip() for line in (self.technology_stack or "").splitlines() if line.strip()]
