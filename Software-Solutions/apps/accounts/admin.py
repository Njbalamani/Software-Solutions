from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.accounts.models import Profile, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "updated_at")
    search_fields = ("user__username", "user__email", "phone")
