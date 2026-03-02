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


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Ensure each user always has a profile row."""
    if created:
        UserProfile.objects.create(user=instance)
        return
    UserProfile.objects.get_or_create(user=instance)
