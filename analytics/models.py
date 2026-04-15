from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from courses.models import Course


User = get_user_model()


class LearningFeedback(models.Model):
    SCALE_CHOICES = [
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
    ]
    LEVEL_CHOICES = [
        ("excellent", "优秀"),
        ("good", "良好"),
        ("pass", "合格"),
        ("improve", "待提高"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="learning_feedback")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="learning_feedback")
    student_name = models.CharField(max_length=80, blank=True, default="")
    class_name = models.CharField(max_length=80, blank=True, default="")
    knowledge_q1 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    knowledge_q2 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    knowledge_q3 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    knowledge_q4 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    practice_q5 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    practice_q6 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    practice_q7 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    attitude_q8 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    attitude_q9 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    attitude_q10 = models.CharField(max_length=1, choices=SCALE_CHOICES, blank=True, default="")
    reflection_gain = models.TextField(blank=True, default="")
    reflection_gap = models.TextField(blank=True, default="")
    reflection_advice = models.TextField(blank=True, default="")
    overall_level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True, default="")
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

    @staticmethod
    def _choice_to_score(value: str) -> int:
        mapping = {"A": 5, "B": 4, "C": 3, "D": 2}
        return mapping.get((value or "").strip().upper(), 0)

    def _has_structured_answers(self) -> bool:
        fields = [
            self.knowledge_q1,
            self.knowledge_q2,
            self.knowledge_q3,
            self.knowledge_q4,
            self.practice_q5,
            self.practice_q6,
            self.practice_q7,
            self.attitude_q8,
            self.attitude_q9,
            self.attitude_q10,
        ]
        return all(fields)

    @staticmethod
    def _avg_score(*values: int) -> int:
        filtered = [value for value in values if value]
        if not filtered:
            return 1
        return round(sum(filtered) / len(filtered))

    def save(self, *args, **kwargs):
        if self._has_structured_answers():
            q1 = self._choice_to_score(self.knowledge_q1)
            q2 = self._choice_to_score(self.knowledge_q2)
            q3 = self._choice_to_score(self.knowledge_q3)
            q4 = self._choice_to_score(self.knowledge_q4)
            q5 = self._choice_to_score(self.practice_q5)
            q6 = self._choice_to_score(self.practice_q6)
            q7 = self._choice_to_score(self.practice_q7)
            q8 = self._choice_to_score(self.attitude_q8)
            q9 = self._choice_to_score(self.attitude_q9)
            q10 = self._choice_to_score(self.attitude_q10)

            self.concept_score = self._avg_score(q1, q3, q7)
            self.mechanism_score = self._avg_score(q2, q5, q6)
            self.ethics_score = self._avg_score(q4)
            self.expression_score = self._avg_score(q8, q9)
            self.exploration_score = self._avg_score(q10)

            reflection_parts = []
            if self.reflection_gain:
                reflection_parts.append(f"本单元最大收获：{self.reflection_gain}")
            if self.reflection_gap:
                reflection_parts.append(f"仍需加强内容：{self.reflection_gap}")
            if self.reflection_advice:
                reflection_parts.append(f"对 AI 学习的建议：{self.reflection_advice}")
            self.reflection = "\n".join(reflection_parts)

        if not self.student_name:
            self.student_name = self.user.get_full_name() or self.user.username

        super().save(*args, **kwargs)
