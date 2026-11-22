from django.contrib import admin

from apps.blog.models import BlogCategory, BlogComment, BlogPost


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_editable = ("is_active",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "is_published", "is_featured", "published_at")
    list_editable = ("is_published", "is_featured")
    list_filter = ("category", "is_published", "is_featured")
    search_fields = ("title", "excerpt", "content")
    prepopulated_fields = {"slug": ("title",)}
    autocomplete_fields = ("author", "category")
    readonly_fields = ("views", "created_at", "updated_at", "published_at")
    fieldsets = (
        ("Content", {"fields": ("category", "author", "title", "slug", "excerpt", "content", "featured_image")}),
        ("Publishing", {"fields": ("is_published", "is_featured", "published_at", "views", "created_at", "updated_at")}),
    )


@admin.action(description="Approve selected comments")
def approve_comments(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.register(BlogComment)
class BlogCommentAdmin(admin.ModelAdmin):
    list_display = ("author_name", "post", "is_approved", "created_at")
    list_editable = ("is_approved",)
    list_filter = ("is_approved", "created_at")
    search_fields = ("author_name", "author_email", "content", "post__title")
    readonly_fields = ("created_at",)
    actions = [approve_comments]
