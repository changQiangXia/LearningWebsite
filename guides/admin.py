from django.contrib import admin

from .models import TeachingGuide


@admin.register(TeachingGuide)
class TeachingGuideAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order_no", "is_published", "updated_at")
    list_filter = ("is_published", "course")
    search_fields = ("title", "unit_name", "objectives", "key_points", "evaluation_suggestion")

# Register your models here.
