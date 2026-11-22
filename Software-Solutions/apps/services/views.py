from django.shortcuts import get_object_or_404, render

from apps.services.models import Service, ServiceCategory


def service_list(request):
    services = Service.objects.filter(is_published=True).select_related("category")
    category_slug = request.GET.get("category")
    category = None
    if category_slug:
        category = get_object_or_404(ServiceCategory, slug=category_slug, is_active=True)
        services = services.filter(category=category)
    return render(
        request,
        "services.html",
        {
            "services": services,
            "categories": ServiceCategory.objects.filter(is_active=True),
            "active_category": category,
        },
    )


def service_detail(request, slug):
    service = get_object_or_404(Service, slug=slug, is_published=True)
    Service.objects.filter(pk=service.pk).update(views=service.views + 1)
    service.views += 1
    related = Service.objects.filter(is_published=True, category=service.category).exclude(pk=service.pk)[:3]
    return render(
        request,
        "service_detail.html",
        {"service": service, "related_services": related},
    )
