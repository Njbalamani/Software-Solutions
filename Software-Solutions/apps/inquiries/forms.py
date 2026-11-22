from django import forms
from django.core.exceptions import ValidationError

from apps.inquiries.models import ProjectInquiry


class ContactForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ProjectInquiry
        fields = ("full_name", "email", "phone", "company_name", "service", "budget", "description")
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6, "placeholder": "Tell us about your project..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["service"].required = True
        self.fields["full_name"].widget.attrs["placeholder"] = "Your full name"
        self.fields["email"].widget.attrs["placeholder"] = "you@example.com"
        self.fields["phone"].widget.attrs["placeholder"] = "+1 555 000 0000"
        self.fields["company_name"].widget.attrs["placeholder"] = "Company (optional)"

    def clean_full_name(self):
        name = self.cleaned_data["full_name"].strip()
        if len(name) < 2:
            raise ValidationError("Please enter your full name.")
        return name

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()
        if phone and not any(ch.isdigit() for ch in phone):
            raise ValidationError("Enter a valid phone number.")
        return phone

    def clean_description(self):
        description = self.cleaned_data["description"].strip()
        if len(description) < 20:
            raise ValidationError("Please provide at least 20 characters about your project.")
        return description

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_website(self):
        value = self.cleaned_data.get("website", "").strip()
        if value:
            raise ValidationError("Submission rejected.")
        return value
