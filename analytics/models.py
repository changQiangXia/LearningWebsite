from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from courses.models import Course


User = get_user_model()


class LearningFeedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="learning_feedback")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="learning_feedback")
    concept_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    mechanism_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    ethics_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    expression_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    exploration_score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    reflection = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "course"],
                name="uniq_learning_feedback_user_course",
            )
        ]

    def __str__(self):
        return f"{self.user} / {self.course} / feedback"
