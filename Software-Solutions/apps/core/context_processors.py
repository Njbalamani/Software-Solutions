from apps.core.models import SiteConfiguration


def site_context(request):
    return {"site": SiteConfiguration.get()}
