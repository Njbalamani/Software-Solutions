from django.contrib import admin

from apps.portfolio.models import PortfolioProject, ProjectCategory


@admin.register(ProjectCategory)
class ProjectCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(PortfolioProject)
class PortfolioProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "is_featured", "views", "order")
    list_editable = ("is_published", "is_featured", "order")
    list_filter = ("category", "is_published", "is_featured")
    search_fields = ("title", "short_description", "description", "technology_stack")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("views", "created_at", "updated_at")
    fieldsets = (
        ("General", {"fields": ("category", "title", "slug", "short_description", "description", "screenshot")}),
        ("Links & Stack", {"fields": ("technology_stack", "github_url", "live_demo_url")}),
        ("Display", {"fields": ("is_published", "is_featured", "completed_date", "order", "views", "created_at", "updated_at")}),
    )
