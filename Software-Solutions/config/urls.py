from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.authtoken.views import obtain_auth_token

admin.site.site_header = "BALATECH Administration"
admin.site.site_title = "BALATECH Admin"
admin.site.index_title = "Site management"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/token/", obtain_auth_token, name="api-token"),
    path("api/", include("apps.api.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("services/", include("apps.services.urls")),
    path("portfolio/", include("apps.portfolio.urls")),
    path("contact/", include("apps.inquiries.urls")),
    path("inquiries/", RedirectView.as_view(pattern_name="inquiries:contact", permanent=True)),
    path("blog/", include("apps.blog.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"
