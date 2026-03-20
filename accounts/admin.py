from django.contrib import admin

from .models import FavoriteItem, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "school", "major", "grade", "updated_at")
    list_filter = ("role", "school")
    search_fields = ("user__username", "user__email", "school", "major", "grade")
    raw_id_fields = ("user",)


@admin.register(FavoriteItem)
class FavoriteItemAdmin(admin.ModelAdmin):
    list_display = ("user", "target_type", "target_id", "title_snapshot", "created_at")
    list_filter = ("target_type", "created_at")
    search_fields = ("user__username", "title_snapshot", "url_snapshot")
    raw_id_fields = ("user",)
