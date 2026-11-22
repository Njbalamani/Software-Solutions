from django.urls import path

from apps.blog import views

app_name = "blog"

urlpatterns = [
    path("", views.blog_list, name="list"),
    path("<slug:slug>/", views.blog_detail, name="detail"),
]
