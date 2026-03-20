from django.contrib import admin

from .models import PracticeRecord


@admin.register(PracticeRecord)
class PracticeRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "practice_type", "created_at")
    list_filter = ("practice_type",)
    search_fields = ("input_text", "output_text")

# Register your models here.
