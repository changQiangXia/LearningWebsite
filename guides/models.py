from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse

from courses.models import Course


User = get_user_model()


class TeachingGuide(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="teaching_guides")
    title = models.CharField(max_length=200)
    unit_name = models.CharField(max_length=200, blank=True)
    objectives = models.TextField()
    key_points = models.TextField()
    difficult_points = models.TextField(blank=True)
    learning_methods = models.TextField(blank=True)
    assignment_suggestion = models.TextField(blank=True)
    evaluation_suggestion = models.TextField(blank=True)
    order_no = models.PositiveIntegerField(default=1)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teaching_guides_created",
    )
    is_published = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["course_id", "order_no", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "order_no"],
                name="uniq_guide_order_per_course",
            )
        ]

    def __str__(self) -> str:
        return f"{self.course.title} / {self.title}"

    def get_absolute_url(self):
        return reverse("guides:guide_detail", kwargs={"guide_id": self.id})

# Create your models here.
