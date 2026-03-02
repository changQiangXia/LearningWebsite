from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "school", "major", "grade", "updated_at")
    list_filter = ("role", "school")
    search_fields = ("user__username", "user__email", "school", "major", "grade")
    raw_id_fields = ("user",)
