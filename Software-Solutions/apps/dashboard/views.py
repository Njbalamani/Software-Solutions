import csv
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from apps.accounts.forms import ProfileUpdateForm, UserUpdateForm
from apps.blog.models import BlogComment, BlogPost
from apps.core.models import NewsletterSubscriber
from apps.dashboard.forms import BlogPostForm, PortfolioProjectForm, ServiceForm
from apps.inquiries.models import InquiryNote, ProjectInquiry
from apps.portfolio.models import PortfolioProject
from apps.services.models import Service


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        messages.error(self.request, "You do not have permission to access the admin dashboard.")
        return redirect("core:home")


class ContentContextMixin:
    title = ""
    url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = self.title
        context["url_name"] = self.url_name
        context["model_label"] = self.model._meta.verbose_name.title()
        return context

    def get_success_url(self):
        return reverse(self.url_name)


class DashboardHomeView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_inquiries"] = ProjectInquiry.objects.count()
        context["new_inquiries"] = ProjectInquiry.objects.filter(status=ProjectInquiry.Status.NEW).count()
        context["active_projects"] = PortfolioProject.objects.filter(is_published=True).count()
        context["published_services"] = Service.objects.filter(is_published=True).count()
        context["portfolio_projects"] = PortfolioProject.objects.count()
        context["recent_inquiries"] = ProjectInquiry.objects.select_related("service")[:8]
        context["status_counts"] = [
            (label, ProjectInquiry.objects.filter(status=value).count())
            for value, label in ProjectInquiry.Status.choices
        ]
        days = [timezone.localdate() - timedelta(days=offset) for offset in range(6, -1, -1)]
        counts = dict(
            ProjectInquiry.objects.filter(created_at__date__in=days)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(count=Count("id"))
            .values_list("day", "count")
        )
        peak = max(counts.values(), default=1) or 1
        context["inquiry_trend"] = [
            (day, counts.get(day, 0), int(counts.get(day, 0) / peak * 100)) for day in days
        ]
        popular = []
        popular.extend(
            (item.title, item.views, "Service")
            for item in Service.objects.filter(is_published=True).only("title", "views")
        )
        popular.extend(
            (item.title, item.views, "Project")
            for item in PortfolioProject.objects.filter(is_published=True).only("title", "views")
        )
        popular.extend(
            (item.title, item.views, "Article")
            for item in BlogPost.objects.filter(is_published=True).only("title", "views")
        )
        context["most_viewed"] = sorted(popular, key=lambda item: item[1], reverse=True)[:5]
        return context


class InquiryListView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/inquiries.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "csv":
            return self._export_csv()
        return super().get(request, *args, **kwargs)

    def _filtered_inquiries(self):
        inquiries = ProjectInquiry.objects.select_related("service")
        status = self.request.GET.get("status")
        query = self.request.GET.get("q", "").strip()
        if status in ProjectInquiry.Status.values:
            inquiries = inquiries.filter(status=status)
        if query:
            inquiries = inquiries.filter(full_name__icontains=query) | inquiries.filter(email__icontains=query)
        if self.request.GET.get("sla") == "breached":
            cutoff = timezone.now() - timezone.timedelta(hours=48)
            inquiries = inquiries.filter(
                created_at__lt=cutoff
            ).exclude(status__in=[ProjectInquiry.Status.COMPLETED, ProjectInquiry.Status.REJECTED])
        return inquiries

    def _export_csv(self):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="balatech-inquiries.csv"'
        writer = csv.writer(response)
        writer.writerow(["Submitted", "Name", "Email", "Phone", "Company", "Service", "Budget", "Status", "Description"])
        for inquiry in self._filtered_inquiries():
            writer.writerow([
                inquiry.created_at.strftime("%Y-%m-%d %H:%M"),
                inquiry.full_name,
                inquiry.email,
                inquiry.phone,
                inquiry.company_name,
                inquiry.service.title if inquiry.service_id else "",
                inquiry.get_budget_display(),
                inquiry.get_status_display(),
                inquiry.description.replace("\n", " "),
            ])
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["inquiries"] = self._filtered_inquiries()
        context["statuses"] = ProjectInquiry.Status.choices
        context["active_status"] = self.request.GET.get("status")
        context["query"] = self.request.GET.get("q", "").strip()
        cutoff = timezone.now() - timezone.timedelta(hours=48)
        context["breached_count"] = ProjectInquiry.objects.filter(created_at__lt=cutoff).exclude(
            status__in=[ProjectInquiry.Status.COMPLETED, ProjectInquiry.Status.REJECTED]
        ).count()
        return context


class NewsletterListView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/newsletters.html"

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "csv":
            response = HttpResponse(content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = 'attachment; filename="balatech-subscribers.csv"'
            writer = csv.writer(response)
            writer.writerow(["Email", "Status", "Subscribed"])
            for subscriber in NewsletterSubscriber.objects.all():
                writer.writerow([
                    subscriber.email,
                    "Active" if subscriber.is_active else "Unsubscribed",
                    subscriber.created_at.strftime("%Y-%m-%d %H:%M"),
                ])
            return response
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        subscriber = get_object_or_404(NewsletterSubscriber, pk=request.POST.get("pk"))
        subscriber.is_active = not subscriber.is_active
        subscriber.save(update_fields=["is_active"])
        messages.success(request, f"{subscriber.email} updated.")
        return redirect("dashboard:newsletters")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subscribers"] = NewsletterSubscriber.objects.all()
        return context


class CommentModerationView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/comments.html"

    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(BlogComment, pk=request.POST.get("pk"))
        if "approve" in request.POST:
            comment.is_approved = True
            comment.save(update_fields=["is_approved"])
            messages.success(request, "Comment approved.")
        elif "delete" in request.POST:
            comment.delete()
            messages.success(request, "Comment deleted.")
        return redirect("dashboard:comments")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pending_comments"] = BlogComment.objects.filter(is_approved=False).select_related("post")
        context["approved_comments"] = BlogComment.objects.filter(is_approved=True).select_related("post")[:20]
        return context


class InquiryDetailView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/inquiry_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inquiry = get_object_or_404(ProjectInquiry.objects.select_related("service"), pk=kwargs["pk"])
        context["inquiry"] = inquiry
        context["notes"] = inquiry.notes.select_related("author")
        context["statuses"] = ProjectInquiry.Status.choices
        context["staff_users"] = get_user_model().objects.filter(is_staff=True, is_active=True)
        return context

    def post(self, request, *args, **kwargs):
        inquiry = get_object_or_404(ProjectInquiry, pk=kwargs["pk"])
        action = request.POST.get("action")
        if action == "add_note":
            note = request.POST.get("note", "").strip()
            if note:
                InquiryNote.objects.create(inquiry=inquiry, author=request.user, note=note)
                messages.success(request, "Internal note added.")
        elif action == "update_status":
            status = request.POST.get("status")
            if status in ProjectInquiry.Status.values:
                inquiry.status = status
                inquiry.save(update_fields=["status", "updated_at"])
                messages.success(request, "Inquiry status updated.")
        elif action == "assign":
            assigned_id = request.POST.get("assigned_to")
            assigned = get_user_model().objects.filter(pk=assigned_id, is_staff=True, is_active=True).first() if assigned_id else None
            inquiry.assigned_to = assigned
            inquiry.save(update_fields=["assigned_to", "updated_at"])
            messages.success(request, "Inquiry assignment updated.")
        elif action == "delete":
            inquiry.delete()
            messages.success(request, "Inquiry deleted.")
            return redirect("dashboard:inquiries")
        return redirect("dashboard:inquiry_detail", pk=kwargs["pk"])


class ContentListView(StaffRequiredMixin, ContentContextMixin, TemplateView):
    template_name = "dashboard/content_list.html"
    model = None
    create_url_name = ""
    edit_url_name = ""
    delete_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["items"] = self.model.objects.all()
        context["create_url_name"] = self.create_url_name
        context["edit_url_name"] = self.edit_url_name
        context["delete_url_name"] = self.delete_url_name
        return context

    def post(self, request, *args, **kwargs):
        item = get_object_or_404(self.model, pk=request.POST.get("pk"))
        if "toggle_featured" in request.POST and hasattr(item, "is_featured"):
            item.is_featured = not item.is_featured
            item.save(update_fields=["is_featured"])
        elif hasattr(item, "is_published"):
            item.is_published = not item.is_published
            item.save(update_fields=["is_published"])
        messages.success(request, f"{item} updated.")
        return redirect(self.url_name)


class ContentCreateView(StaffRequiredMixin, ContentContextMixin, CreateView):
    template_name = "dashboard/content_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} created.")
        return super().form_valid(form)


class ContentUpdateView(StaffRequiredMixin, ContentContextMixin, UpdateView):
    template_name = "dashboard/content_form.html"

    def form_valid(self, form):
        messages.success(self.request, f"{self.model._meta.verbose_name.title()} updated.")
        return super().form_valid(form)


class ContentDeleteView(StaffRequiredMixin, ContentContextMixin, DeleteView):
    template_name = "dashboard/content_confirm_delete.html"

    def delete(self, request, *args, **kwargs):
        messages.success(request, f"{self.model._meta.verbose_name.title()} deleted.")
        return super().delete(request, *args, **kwargs)


class ServiceListView(ContentListView):
    model = Service
    title = "Services"
    url_name = "dashboard:services"
    create_url_name = "dashboard:service_create"
    edit_url_name = "dashboard:service_edit"
    delete_url_name = "dashboard:service_delete"


class ServiceCreateView(ContentCreateView):
    model = Service
    form_class = ServiceForm
    title = "Add Service"
    url_name = "dashboard:services"


class ServiceUpdateView(ContentUpdateView):
    model = Service
    form_class = ServiceForm
    title = "Edit Service"
    url_name = "dashboard:services"


class ServiceDeleteView(ContentDeleteView):
    model = Service
    title = "Delete Service"
    url_name = "dashboard:services"


class PortfolioListView(ContentListView):
    model = PortfolioProject
    title = "Portfolio Projects"
    url_name = "dashboard:portfolio"
    create_url_name = "dashboard:portfolio_create"
    edit_url_name = "dashboard:portfolio_edit"
    delete_url_name = "dashboard:portfolio_delete"


class PortfolioCreateView(ContentCreateView):
    model = PortfolioProject
    form_class = PortfolioProjectForm
    title = "Add Project"
    url_name = "dashboard:portfolio"


class PortfolioUpdateView(ContentUpdateView):
    model = PortfolioProject
    form_class = PortfolioProjectForm
    title = "Edit Project"
    url_name = "dashboard:portfolio"


class PortfolioDeleteView(ContentDeleteView):
    model = PortfolioProject
    title = "Delete Project"
    url_name = "dashboard:portfolio"


class BlogListView(ContentListView):
    model = BlogPost
    title = "Blog Posts"
    url_name = "dashboard:blog"
    create_url_name = "dashboard:blog_create"
    edit_url_name = "dashboard:blog_edit"
    delete_url_name = "dashboard:blog_delete"


class BlogCreateView(ContentCreateView):
    model = BlogPost
    form_class = BlogPostForm
    title = "Add Blog Post"
    url_name = "dashboard:blog"

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class BlogUpdateView(ContentUpdateView):
    model = BlogPost
    form_class = BlogPostForm
    title = "Edit Blog Post"
    url_name = "dashboard:blog"


class BlogDeleteView(ContentDeleteView):
    model = BlogPost
    title = "Delete Blog Post"
    url_name = "dashboard:blog"


class ProfileView(StaffRequiredMixin, TemplateView):
    template_name = "dashboard/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_form"] = kwargs.get("user_form") or UserUpdateForm(instance=self.request.user)
        context["profile_form"] = kwargs.get("profile_form") or ProfileUpdateForm(instance=self.request.user.profile)
        return context

    def post(self, request, *args, **kwargs):
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("dashboard:profile")
        return self.render_to_response(self.get_context_data(user_form=user_form, profile_form=profile_form))
