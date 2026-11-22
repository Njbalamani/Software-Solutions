from django.contrib import admin

from apps.core.models import FAQ, NewsletterSubscriber, SiteConfiguration, Statistic, Technology, Testimonial


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Branding", {"fields": ("site_name", "tagline", "meta_description")}),
        ("Hero", {"fields": ("hero_heading", "hero_description")}),
        ("About", {"fields": ("about_intro", "about_experience", "about_approach", "career_experience")}),
        ("Contact & Social", {"fields": ("email", "phone", "location", "github_url", "linkedin_url", "twitter_url")}),
    )
    list_display = ("site_name", "email", "updated_at")

    def has_add_permission(self, request):
        return not SiteConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Statistic)
class StatisticAdmin(admin.ModelAdmin):
    list_display = ("label", "value", "suffix", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("label",)


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ("email", "is_active", "created_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "created_at")
    search_fields = ("email",)
    readonly_fields = ("unsubscribe_token", "created_at")


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "category", "order", "is_active")
    list_editable = ("order", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("question", "answer")


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("client_name", "company", "rating", "is_active", "created_at")
    list_editable = ("is_active",)
    list_filter = ("is_active", "rating")
    search_fields = ("client_name", "company", "message")
