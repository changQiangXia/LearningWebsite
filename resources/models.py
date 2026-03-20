from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

from courses.models import Course, Lesson


User = get_user_model()


class ResourceType(models.TextChoices):
    COURSEWARE = "courseware", "课件"
    VIDEO = "video", "视频"
    READING = "reading", "拓展阅读"
    TOOL = "tool", "工具资源"


class ResourceAudience(models.TextChoices):
    ALL = "all", "全体学习者"
    TEACHER = "teacher", "教师专用"


class Resource(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    resource_type = models.CharField(
        max_length=20,
        choices=ResourceType.choices,
        default=ResourceType.READING,
        db_index=True,
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources",
    )
    file = models.FileField(upload_to="resources/files/", blank=True, null=True)
    external_url = models.URLField(blank=True)
    cover_image = models.ImageField(upload_to="resources/covers/", blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True)
    audience = models.CharField(
        max_length=20,
        choices=ResourceAudience.choices,
        default=ResourceAudience.ALL,
        db_index=True,
    )
    sort_order = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resources_created",
    )
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course_id", "lesson_id", "sort_order", "-updated_at", "-id"]

    def __str__(self) -> str:
        return self.title

    def _build_unique_slug(self, seed: str | None = None) -> str:
        base = slugify(seed or self.title)[:200] or "resource"
        candidate = base
        suffix = 1
        while Resource.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    def clean(self):
        super().clean()
        if not self.file and not self.external_url:
            raise ValidationError("资源文件和外部链接至少填写一项。")
        if self.lesson_id:
            lesson_course_id = self.lesson.chapter.course_id
            if self.course_id and self.course_id != lesson_course_id:
                raise ValidationError({"lesson": "所选课时必须属于当前课程。"})
            self.course_id = lesson_course_id

    def save(self, *args, **kwargs):
        self.slug = self._build_unique_slug(seed=self.slug or self.title)
        self.full_clean()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("resources:resource_detail", kwargs={"slug": self.slug})

# Create your models here.
