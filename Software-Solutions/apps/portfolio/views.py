from django.shortcuts import get_object_or_404, render

from apps.portfolio.models import PortfolioProject, ProjectCategory


def project_list(request):
    projects = PortfolioProject.objects.filter(is_published=True).select_related("category")
    category_slug = request.GET.get("category")
    category = None
    if category_slug:
        category = get_object_or_404(ProjectCategory, slug=category_slug, is_active=True)
        projects = projects.filter(category=category)
    return render(
        request,
        "portfolio.html",
        {
            "projects": projects,
            "categories": ProjectCategory.objects.filter(is_active=True),
            "active_category": category,
        },
    )


def project_detail(request, slug):
    project = get_object_or_404(PortfolioProject, slug=slug, is_published=True)
    PortfolioProject.objects.filter(pk=project.pk).update(views=project.views + 1)
    project.views += 1
    related = PortfolioProject.objects.filter(is_published=True, category=project.category).exclude(pk=project.pk)[:3]
    return render(request, "project_detail.html", {"project": project, "related_projects": related})
