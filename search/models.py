from django.db import models


class SearchSourceType(models.TextChoices):
    COURSE = "course", "Course"
    LESSON = "lesson", "Lesson"
    FORUM_POST = "forum_post", "Forum Post"
    QUESTION = "question", "Question"


class SearchDocument(models.Model):
    """Denormalized search index document."""

    source_type = models.CharField(max_length=30, choices=SearchSourceType.choices, db_index=True)
    source_id = models.PositiveBigIntegerField(db_index=True)
    title = models.CharField(max_length=255, db_index=True)
    body = models.TextField(blank=True)
    keywords = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["source_type", "source_id"],
                name="uniq_search_source",
            )
        ]
        indexes = [
            models.Index(fields=["source_type", "is_active"], name="idx_search_type_active"),
            models.Index(fields=["updated_at"], name="idx_search_updated"),
        ]

    def __str__(self) -> str:
        return f"{self.source_type}:{self.source_id} - {self.title}"
