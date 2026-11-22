from django.urls import path

from apps.inquiries import views

app_name = "inquiries"

urlpatterns = [
    path("", views.contact, name="contact"),
]
