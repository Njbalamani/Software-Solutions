from django.urls import path

from apps.core import seo, views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("search/", views.search, name="search"),
    path("health/", views.health, name="health"),
    path("newsletter/subscribe/", views.newsletter_subscribe, name="newsletter_subscribe"),
    path("newsletter/unsubscribe/<str:token>/", views.newsletter_unsubscribe, name="newsletter_unsubscribe"),
    path("robots.txt", seo.robots_txt, name="robots"),
    path("sitemap.xml", seo.sitemap_xml, name="sitemap"),
]
