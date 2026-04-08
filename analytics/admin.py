from django.contrib import admin

from .models import LearningFeedback


@admin.register(LearningFeedback)
class LearningFeedbackAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "concept_score", "mechanism_score", "ethics_score", "updated_at")
    list_filter = ("course",)
    search_fields = ("user__username", "course__title", "reflection")
