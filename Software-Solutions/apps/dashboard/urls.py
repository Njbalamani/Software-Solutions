from django.urls import path

from apps.dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="index"),
    path("inquiries/", views.InquiryListView.as_view(), name="inquiries"),
    path("inquiries/<int:pk>/", views.InquiryDetailView.as_view(), name="inquiry_detail"),
    path("newsletters/", views.NewsletterListView.as_view(), name="newsletters"),
    path("comments/", views.CommentModerationView.as_view(), name="comments"),
    path("services/", views.ServiceListView.as_view(), name="services"),
    path("services/new/", views.ServiceCreateView.as_view(), name="service_create"),
    path("services/<int:pk>/edit/", views.ServiceUpdateView.as_view(), name="service_edit"),
    path("services/<int:pk>/delete/", views.ServiceDeleteView.as_view(), name="service_delete"),
    path("portfolio/", views.PortfolioListView.as_view(), name="portfolio"),
    path("portfolio/new/", views.PortfolioCreateView.as_view(), name="portfolio_create"),
    path("portfolio/<int:pk>/edit/", views.PortfolioUpdateView.as_view(), name="portfolio_edit"),
    path("portfolio/<int:pk>/delete/", views.PortfolioDeleteView.as_view(), name="portfolio_delete"),
    path("blog/", views.BlogListView.as_view(), name="blog"),
    path("blog/new/", views.BlogCreateView.as_view(), name="blog_create"),
    path("blog/<int:pk>/edit/", views.BlogUpdateView.as_view(), name="blog_edit"),
    path("blog/<int:pk>/delete/", views.BlogDeleteView.as_view(), name="blog_delete"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]
