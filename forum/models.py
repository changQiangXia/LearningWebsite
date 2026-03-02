from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


User = get_user_model()


class ForumPostCategory(models.TextChoices):
    DISCUSSION = "discussion", "讨论"
    HELP = "help", "求助"
    SHARE = "share", "分享"


class ForumPostStatus(models.TextChoices):
    PUBLISHED = "published", "已发布"
    HIDDEN = "hidden", "已隐藏"
    DELETED = "deleted", "已删除"


class ForumPost(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="forum_posts",
    )
    title = models.CharField(max_length=200, db_index=True)
    content = models.TextField()
    category = models.CharField(
        max_length=20,
        choices=ForumPostCategory.choices,
        default=ForumPostCategory.DISCUSSION,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=ForumPostStatus.choices,
        default=ForumPostStatus.PUBLISHED,
        db_index=True,
    )
    is_pinned = models.BooleanField(default=False)
    is_solved = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField(default=timezone.now, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-last_activity_at", "-created_at"]
        indexes = [
            models.Index(fields=["category", "status"], name="idx_forum_cate_stat"),
            models.Index(fields=["status", "created_at"], name="idx_forum_stat_ctime"),
        ]

    def __str__(self) -> str:
        return self.title


class ForumComment(models.Model):
    post = models.ForeignKey(ForumPost, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="forum_comments",
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at", "id"]
        indexes = [
            models.Index(fields=["post", "created_at"], name="idx_forum_comment_post_ctime"),
        ]

    def __str__(self) -> str:
        return f"Comment#{self.pk or 'new'} on {self.post_id}"

    def clean(self):
        super().clean()
        if self.parent_id and self.parent_id == self.pk:
            raise ValidationError({"parent": "评论不能回复自身。"})
        if self.parent_id and self.parent.post_id != self.post_id:
            raise ValidationError({"parent": "父评论必须属于同一帖子。"})

    def save(self, *args, **kwargs):
        self.full_clean()
        if self.post_id:
            self.post.last_activity_at = timezone.now()
            self.post.save(update_fields=["last_activity_at"])
        return super().save(*args, **kwargs)
