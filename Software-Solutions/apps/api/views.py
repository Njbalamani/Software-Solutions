from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import exceptions, generics, permissions
from rest_framework.filters import OrderingFilter, SearchFilter

from apps.api.serializers import (
    BlogPostSerializer,
    InquiryCreateSerializer,
    InquirySerializer,
    PortfolioProjectSerializer,
    ServiceSerializer,
)
from apps.blog.models import BlogPost
from apps.inquiries.models import ProjectInquiry
from apps.inquiries.services import is_rate_limited, notify_admin, notify_submitter, record_submission
from apps.portfolio.models import PortfolioProject
from apps.services.models import Service


class PublicReadMixin:
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    ordering_fields = ("created_at", "updated_at", "title", "order")
    permission_classes = [permissions.AllowAny]


class ServiceListAPIView(PublicReadMixin, generics.ListAPIView):
    serializer_class = ServiceSerializer
    queryset = Service.objects.filter(is_published=True).select_related("category")
    filterset_fields = ("category__slug", "is_featured")


class ServiceDetailAPIView(PublicReadMixin, generics.RetrieveAPIView):
    serializer_class = ServiceSerializer
    lookup_field = "slug"
    queryset = Service.objects.filter(is_published=True).select_related("category")


class PortfolioListAPIView(PublicReadMixin, generics.ListAPIView):
    serializer_class = PortfolioProjectSerializer
    queryset = PortfolioProject.objects.filter(is_published=True).select_related("category")
    filterset_fields = ("category__slug", "is_featured")


class PortfolioDetailAPIView(PublicReadMixin, generics.RetrieveAPIView):
    serializer_class = PortfolioProjectSerializer
    lookup_field = "slug"
    queryset = PortfolioProject.objects.filter(is_published=True).select_related("category")


class BlogListAPIView(PublicReadMixin, generics.ListAPIView):
    serializer_class = BlogPostSerializer
    queryset = BlogPost.objects.filter(is_published=True).select_related("category", "author")
    filterset_fields = ("category__slug", "is_featured")
    search_fields = ("title", "excerpt", "content")
    ordering_fields = ("published_at", "views", "title")


class BlogDetailAPIView(PublicReadMixin, generics.RetrieveAPIView):
    serializer_class = BlogPostSerializer
    lookup_field = "slug"
    queryset = BlogPost.objects.filter(is_published=True).select_related("category", "author")


class InquiryCreateAPIView(generics.CreateAPIView):
    serializer_class = InquiryCreateSerializer
    permission_classes = [permissions.AllowAny]
    queryset = ProjectInquiry.objects.all()

    def perform_create(self, serializer):
        if is_rate_limited(self.request):
            raise exceptions.Throttled(detail="Too many submissions. Please try again later.")
        data = serializer.validated_data
        recent = timezone.now() - timezone.timedelta(minutes=10)
        duplicate = ProjectInquiry.objects.filter(
            email__iexact=data["email"],
            description=data["description"],
            created_at__gte=recent,
        ).exists()
        if duplicate:
            raise exceptions.ValidationError({"detail": "A duplicate inquiry was submitted recently."})
        record_submission(self.request)
        inquiry = serializer.save(ip_address=self.request.META.get("REMOTE_ADDR") or None)
        notify_admin(inquiry)
        notify_submitter(inquiry)


class InquiryListAPIView(generics.ListAPIView):
    serializer_class = InquirySerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ("status", "service", "budget")
    search_fields = ("full_name", "email", "company_name", "description")
    ordering_fields = ("created_at", "full_name")
    queryset = ProjectInquiry.objects.select_related("service")


class InquiryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InquirySerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = ProjectInquiry.objects.select_related("service")
