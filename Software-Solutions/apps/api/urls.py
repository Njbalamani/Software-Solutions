from django.urls import path

from apps.api import views

app_name = "api"

urlpatterns = [
    path("services/", views.ServiceListAPIView.as_view(), name="service-list"),
    path("services/<slug:slug>/", views.ServiceDetailAPIView.as_view(), name="service-detail"),
    path("portfolio/", views.PortfolioListAPIView.as_view(), name="portfolio-list"),
    path("portfolio/<slug:slug>/", views.PortfolioDetailAPIView.as_view(), name="portfolio-detail"),
    path("blog/", views.BlogListAPIView.as_view(), name="blog-list"),
    path("blog/<slug:slug>/", views.BlogDetailAPIView.as_view(), name="blog-detail"),
    path("inquiries/", views.InquiryCreateAPIView.as_view(), name="inquiry-create"),
    path("inquiries/list/", views.InquiryListAPIView.as_view(), name="inquiry-list"),
    path("inquiries/<int:pk>/", views.InquiryDetailAPIView.as_view(), name="inquiry-detail"),
]
