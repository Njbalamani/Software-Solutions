from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.blog.models import BlogCategory, BlogPost
from apps.inquiries.models import ProjectInquiry
from apps.portfolio.models import PortfolioProject, ProjectCategory
from apps.services.models import Service, ServiceCategory


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = ("id", "name", "slug", "description")


class ServiceSerializer(serializers.ModelSerializer):
    category = ServiceCategorySerializer(read_only=True)
    features = serializers.ListField(source="features_list", read_only=True)
    technologies = serializers.ListField(source="technologies_list", read_only=True)
    benefits = serializers.ListField(source="benefits_list", read_only=True)

    class Meta:
        model = Service
        fields = (
            "id", "title", "slug", "short_description", "description", "icon",
            "category", "features", "technologies", "benefits", "order", "updated_at",
        )


class ProjectCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectCategory
        fields = ("id", "name", "slug", "description")


class PortfolioProjectSerializer(serializers.ModelSerializer):
    category = ProjectCategorySerializer(read_only=True)
    technologies = serializers.ListField(source="technologies_list", read_only=True)
    screenshot_url = serializers.SerializerMethodField()

    class Meta:
        model = PortfolioProject
        fields = (
            "id", "title", "slug", "short_description", "description", "category",
            "technologies", "screenshot_url", "github_url", "live_demo_url",
            "completed_date", "created_at",
        )

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_screenshot_url(self, obj):
        request = self.context.get("request")
        if obj.screenshot and request:
            return request.build_absolute_uri(obj.screenshot.url)
        return None


class BlogCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BlogCategory
        fields = ("id", "name", "slug", "description")


class BlogPostSerializer(serializers.ModelSerializer):
    category = BlogCategorySerializer(read_only=True)
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)
    featured_image_url = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = (
            "id", "title", "slug", "excerpt", "content", "category", "author_name",
            "featured_image_url", "views", "published_at",
        )

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_featured_image_url(self, obj):
        request = self.context.get("request")
        if obj.featured_image and request:
            return request.build_absolute_uri(obj.featured_image.url)
        return None


class InquiryCreateSerializer(serializers.ModelSerializer):
    service = serializers.PrimaryKeyRelatedField(
        queryset=Service.objects.filter(is_published=True), required=True
    )

    class Meta:
        model = ProjectInquiry
        fields = ("id", "full_name", "email", "phone", "company_name", "service", "budget", "description", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_full_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Please enter your full name.")
        return value.strip()

    def validate_description(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Please provide at least 20 characters about your project.")
        return value.strip()

    def validate_email(self, value):
        return value.strip().lower()


class InquirySerializer(serializers.ModelSerializer):
    service_title = serializers.CharField(source="service.title", read_only=True, default=None)

    class Meta:
        model = ProjectInquiry
        fields = (
            "id", "full_name", "email", "phone", "company_name", "service_title",
            "budget", "description", "status", "ip_address", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "ip_address")
