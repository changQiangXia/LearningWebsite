from django.contrib import admin

from .models import Resource


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "resource_type", "course", "lesson", "audience", "is_published", "updated_at")
    list_filter = ("resource_type", "audience", "is_published", "course")
    search_fields = ("title", "description", "tags")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("course", "lesson", "created_by")

# Register your models here.
