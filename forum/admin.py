from django.contrib import admin

from .models import ForumComment, ForumPost


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "category",
        "status",
        "author",
        "is_pinned",
        "is_solved",
        "view_count",
        "last_activity_at",
    )
    list_filter = ("category", "status", "is_pinned", "is_solved", "created_at")
    search_fields = ("title", "content", "author__username", "author__email")
    raw_id_fields = ("author",)


@admin.register(ForumComment)
class ForumCommentAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "author", "parent", "is_deleted", "created_at")
    list_filter = ("is_deleted", "created_at")
    search_fields = ("content", "author__username", "post__title")
    raw_id_fields = ("post", "author", "parent")
