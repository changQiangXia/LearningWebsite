from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


User = get_user_model()


class CourseStatus(models.TextChoices):
    DRAFT = "draft", "草稿"
    PUBLISHED = "published", "已发布"
    ARCHIVED = "archived", "已归档"


class Course(models.Model):
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to="course_covers/", blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=CourseStatus.choices,
        default=CourseStatus.DRAFT,
        db_index=True,
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses_created",
    )
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    def _build_unique_slug(self, seed: str | None = None) -> str:
        base = slugify(seed or self.title)[:200] or "course"
        candidate = base
        suffix = 1
        while Course.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    def save(self, *args, **kwargs):
        self.slug = self._build_unique_slug(seed=self.slug or self.title)
        if self.status == CourseStatus.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class Chapter(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="chapters")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order_no = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course_id", "order_no", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order_no"],
                name="uniq_chapter_order_per_course",
            )
        ]

    def __str__(self) -> str:
        return f"{self.course.title} / {self.title}"


class Lesson(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    video_url = models.URLField(blank=True)
    attachment_url = models.URLField(blank=True)
    order_no = models.PositiveIntegerField(default=1)
    estimated_minutes = models.PositiveIntegerField(default=10)
    is_free_preview = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["chapter_id", "order_no", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["chapter", "order_no"],
                name="uniq_lesson_order_per_chapter",
            )
        ]

    def __str__(self) -> str:
        return f"{self.chapter.title} / {self.title}"


class CourseGlossaryTerm(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="glossary_terms")
    term = models.CharField(max_length=100)
    definition = models.TextField()
    order_no = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["course_id", "order_no", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order_no"],
                name="uniq_glossary_order_per_course",
            )
        ]

    def __str__(self) -> str:
        return f"{self.course.title} / {self.term}"


class LearningProgress(models.Model):
    """Per-user learning state for a lesson."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="learning_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="learning_progress")
    view_count = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(blank=True, null=True)
    last_viewed_at = models.DateTimeField(auto_now=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_viewed_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "lesson"],
                name="uniq_learning_progress_user_lesson",
            )
        ]
        indexes = [
            models.Index(fields=["user", "completed"], name="idx_learning_user_completed"),
            models.Index(fields=["lesson", "completed"], name="idx_learning_lesson_completed"),
        ]

    def __str__(self) -> str:
        return f"Progress user={self.user_id} lesson={self.lesson_id} completed={self.completed}"


class AuditTargetType(models.TextChoices):
    COURSE = "course", "课程"
    CHAPTER = "chapter", "章节"
    LESSON = "lesson", "课时"
    QUESTION = "question", "题目"


class ContentAuditLog(models.Model):
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_audit_logs",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    target_type = models.CharField(max_length=20, choices=AuditTargetType.choices, db_index=True)
    target_id = models.PositiveIntegerField(db_index=True)
    action = models.CharField(max_length=50, db_index=True)
    message = models.CharField(max_length=255)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["course", "created_at"], name="idx_audit_course_time"),
            models.Index(fields=["target_type", "target_id"], name="idx_audit_target"),
        ]

    def __str__(self) -> str:
        return f"{self.target_type}:{self.target_id} {self.action}"
