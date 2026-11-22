from django import forms

from apps.blog.models import BlogPost
from apps.portfolio.models import PortfolioProject
from apps.services.models import Service


class DashboardFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        if "description" in self.fields:
            self.fields["description"].widget.attrs["rows"] = 5
        if "features" in self.fields:
            self.fields["features"].widget.attrs["rows"] = 5
        if "technology_stack" in self.fields:
            self.fields["technology_stack"].widget.attrs["rows"] = 5
        if "benefits" in self.fields:
            self.fields["benefits"].widget.attrs["rows"] = 4
        if "content" in self.fields:
            self.fields["content"].widget.attrs["rows"] = 12


class ServiceForm(DashboardFormMixin, forms.ModelForm):
    class Meta:
        model = Service
        fields = (
            "category", "title", "icon", "short_description", "description",
            "features", "technology_stack", "benefits",
            "is_published", "is_featured", "order",
        )
        help_texts = {
            "features": "One feature per line.",
            "technology_stack": "One technology per line.",
            "benefits": "One benefit per line.",
        }


class PortfolioProjectForm(DashboardFormMixin, forms.ModelForm):
    class Meta:
        model = PortfolioProject
        fields = (
            "category", "title", "short_description", "description", "screenshot",
            "technology_stack", "github_url", "live_demo_url", "completed_date",
            "is_published", "is_featured", "order",
        )
        help_texts = {"technology_stack": "One technology per line."}
        widgets = {"completed_date": forms.DateInput(attrs={"type": "date"})}


class BlogPostForm(DashboardFormMixin, forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = (
            "category", "title", "excerpt", "content", "featured_image",
            "is_published", "is_featured",
        )
