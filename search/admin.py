from django.contrib import admin

from .models import SearchDocument


@admin.register(SearchDocument)
class SearchDocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "source_type", "source_id", "title", "is_active", "updated_at")
    list_filter = ("source_type", "is_active", "updated_at")
    search_fields = ("title", "body", "keywords")
