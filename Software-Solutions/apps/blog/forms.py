from django import forms
from django.core.exceptions import ValidationError

from apps.blog.models import BlogComment


class BlogCommentForm(forms.ModelForm):
    website = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = BlogComment
        fields = ("author_name", "author_email", "content")
        widgets = {
            "content": forms.Textarea(attrs={"rows": 4, "placeholder": "Share your thoughts..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["author_name"].widget.attrs["placeholder"] = "Your name"
        self.fields["author_email"].widget.attrs["placeholder"] = "you@example.com"

    def clean_website(self):
        if self.cleaned_data.get("website", "").strip():
            raise ValidationError("Submission rejected.")
        return ""

    def clean_content(self):
        content = self.cleaned_data["content"].strip()
        if len(content) < 10:
            raise ValidationError("Please write at least 10 characters.")
        return content