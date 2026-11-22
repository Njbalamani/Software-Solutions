from django.contrib import admin

from apps.services.models import Service, ServiceCategory


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order", "is_active")
    list_editable = ("order", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "is_published", "is_featured", "views", "order")
    list_editable = ("is_published", "is_featured", "order")
    readonly_fields = ("views",)
    list_filter = ("category", "is_published", "is_featured")
    search_fields = ("title", "short_description", "description")
    prepopulated_fields = {"slug": ("title",)}
    fieldsets = (
        ("General", {"fields": ("category", "title", "slug", "icon", "short_description", "description")}),
        ("Details", {"fields": ("features", "technology_stack", "benefits")}),
        ("Display", {"fields": ("is_published", "is_featured", "order", "views")}),
    )
