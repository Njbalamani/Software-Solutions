from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
    PasswordResetCompleteView,
)
from django.shortcuts import redirect, render
from django.urls import reverse_lazy

from apps.accounts.forms import ProfileUpdateForm, UserRegistrationForm, UserUpdateForm
from apps.inquiries.models import ProjectInquiry


@login_required
def account_home(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect("dashboard:index")
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect("accounts:account")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    return render(
        request,
        "account.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "inquiries": ProjectInquiry.objects.filter(email__iexact=request.user.email)[:10],
        },
    )


def register(request):
    if request.user.is_authenticated:
        return redirect("accounts:account")
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("accounts:account")
    else:
        form = UserRegistrationForm()
    return render(request, "register.html", {"form": form})


class CustomLoginView(LoginView):
    authentication_form = None
    template_name = "login.html"
    redirect_authenticated_user = True

    def get_form_class(self):
        from apps.accounts.forms import LoginForm

        return LoginForm


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy("core:home")


class CustomPasswordResetView(PasswordResetView):
    template_name = "password_reset.html"
    email_template_name = "emails/password_reset_email.html"
    subject_template_name = "emails/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "password_reset_complete.html"
