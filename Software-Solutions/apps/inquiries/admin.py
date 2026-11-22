from django.contrib import admin

from apps.inquiries.models import InquiryNote, ProjectInquiry


class InquiryNoteInline(admin.TabularInline):
    model = InquiryNote
    extra = 0
    fields = ("author", "note", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)


@admin.action(description="Mark selected inquiries as contacted")
def mark_contacted(modeladmin, request, queryset):
    queryset.update(status=ProjectInquiry.Status.CONTACTED)


@admin.action(description="Mark selected inquiries as completed")
def mark_completed(modeladmin, request, queryset):
    queryset.update(status=ProjectInquiry.Status.COMPLETED)


@admin.action(description="Mark selected inquiries as rejected")
def mark_rejected(modeladmin, request, queryset):
    queryset.update(status=ProjectInquiry.Status.REJECTED)


@admin.register(ProjectInquiry)
class ProjectInquiryAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "service", "budget", "status", "created_at")
    list_editable = ("status",)
    list_filter = ("status", "budget", "service", "assigned_to", "created_at")
    search_fields = ("full_name", "email", "company_name", "description")
    readonly_fields = ("created_at", "updated_at", "ip_address")
    inlines = [InquiryNoteInline]
    actions = [mark_contacted, mark_completed, mark_rejected]
    fieldsets = (
        ("Client", {"fields": ("full_name", "email", "phone", "company_name", "ip_address")}),
        ("Project", {"fields": ("service", "budget", "description")}),
        ("Management", {"fields": ("status", "assigned_to", "created_at", "updated_at")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("service")


@admin.register(InquiryNote)
class InquiryNoteAdmin(admin.ModelAdmin):
    list_display = ("inquiry", "author", "created_at")
    search_fields = ("note", "inquiry__full_name")
    readonly_fields = ("created_at",)
