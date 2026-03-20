from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


User = get_user_model()


class UserRole(models.TextChoices):
    STUDENT = "student", "学生"
    TEACHER = "teacher", "教师"
    ADMIN = "admin", "管理员"


class UserProfile(models.Model):
    """Project-level user extension fields and role assignment."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.STUDENT,
        db_index=True,
    )
    school = models.CharField(max_length=120, blank=True)
    major = models.CharField(max_length=120, blank=True)
    grade = models.CharField(max_length=50, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__username"]

    def __str__(self) -> str:
        return f"{self.user.username} ({self.role})"


class FavoriteTargetType(models.TextChoices):
    COURSE = "course", "课程"
    RESOURCE = "resource", "资源"
    GUIDE = "guide", "教学指引"
    POST = "post", "帖子"


class FavoriteItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorite_items")
    target_type = models.CharField(max_length=20, choices=FavoriteTargetType.choices, db_index=True)
    target_id = models.PositiveBigIntegerField(db_index=True)
    title_snapshot = models.CharField(max_length=200)
    url_snapshot = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "target_type", "target_id"],
                name="uniq_favorite_user_target",
            )
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.target_type}:{self.target_id}"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Ensure each user always has a profile row."""
    if created:
        UserProfile.objects.create(user=instance)
        return
    UserProfile.objects.get_or_create(user=instance)
