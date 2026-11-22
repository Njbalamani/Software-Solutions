from django import forms
from django.core.exceptions import ValidationError


class NewsletterForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Your email address"}))
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    def clean_website(self):
        if self.cleaned_data.get("website", "").strip():
            raise ValidationError("Submission rejected.")
        return ""

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()
