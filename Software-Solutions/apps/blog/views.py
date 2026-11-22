from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.blog.forms import BlogCommentForm
from apps.blog.models import BlogCategory, BlogComment, BlogPost


def blog_list(request):
    posts = BlogPost.objects.filter(is_published=True).select_related("category", "author")
    query = request.GET.get("q", "").strip()
    if query:
        posts = posts.filter(Q(title__icontains=query) | Q(excerpt__icontains=query) | Q(content__icontains=query))
    category_slug = request.GET.get("category")
    category = None
    if category_slug:
        category = get_object_or_404(BlogCategory, slug=category_slug, is_active=True)
        posts = posts.filter(category=category)
    return render(
        request,
        "blog.html",
        {
            "posts": posts,
            "categories": BlogCategory.objects.filter(is_active=True),
            "active_category": category,
            "query": query,
            "featured": BlogPost.objects.filter(is_published=True, is_featured=True)
            .select_related("category", "author")
            .first(),
        },
    )


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug, is_published=True)
    form = BlogCommentForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            data = form.cleaned_data.copy()
            data.pop("website", None)
            BlogComment.objects.create(post=post, **data)
            messages.success(request, "Thank you. Your comment will appear after moderation.")
            return redirect("blog:detail", slug=slug)
    else:
        BlogPost.objects.filter(pk=post.pk).update(views=post.views + 1)
        post.views += 1
    related = BlogPost.objects.filter(is_published=True, category=post.category).exclude(pk=post.pk)[:3]
    return render(
        request,
        "blog_detail.html",
        {
            "post": post,
            "related_posts": related,
            "comments": post.comments.filter(is_approved=True),
            "comment_form": form,
        },
    )
