from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from courses.models import Lesson


User = get_user_model()


class QuestionType(models.TextChoices):
    SINGLE_CHOICE = "single", "单选题"
    MULTIPLE_CHOICE = "multiple", "多选题"
    TRUE_FALSE = "judge", "判断题"
    SHORT_ANSWER = "short", "简答题"


class QuestionDifficulty(models.TextChoices):
    EASY = "easy", "简单"
    MEDIUM = "medium", "中等"
    HARD = "hard", "困难"


class Question(models.Model):
    """Question bank item for a lesson."""

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="questions")
    question_type = models.CharField(
        max_length=20,
        choices=QuestionType.choices,
        default=QuestionType.SINGLE_CHOICE,
        db_index=True,
    )
    difficulty = models.CharField(
        max_length=20,
        choices=QuestionDifficulty.choices,
        default=QuestionDifficulty.MEDIUM,
        db_index=True,
    )
    stem = models.TextField()
    options = models.JSONField(default=list, blank=True)
    correct_answer = models.JSONField(default=list)
    explanation = models.TextField(blank=True)
    score = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questions_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["lesson_id", "id"]
        indexes = [
            models.Index(fields=["lesson", "question_type"], name="idx_q_lesson_type"),
            models.Index(fields=["difficulty"], name="idx_q_difficulty"),
            models.Index(fields=["is_active"], name="idx_q_active"),
        ]

    def __str__(self) -> str:
        return f"Q{self.pk or 'new'} - {self.get_question_type_display()}"

    def clean(self):
        super().clean()

        if not isinstance(self.correct_answer, list):
            raise ValidationError({"correct_answer": "correct_answer 必须是列表类型。"})

        if not self.correct_answer:
            raise ValidationError({"correct_answer": "至少需要一个正确答案。"})

        objective_types = {
            QuestionType.SINGLE_CHOICE,
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.TRUE_FALSE,
        }

        if self.question_type in objective_types:
            if not isinstance(self.options, list):
                raise ValidationError({"options": "客观题的 options 必须是列表类型。"})
            if len(self.options) < 2:
                raise ValidationError({"options": "客观题至少需要两个选项。"})

            option_keys = set()
            for item in self.options:
                if not isinstance(item, dict):
                    raise ValidationError({"options": "每个选项必须是包含 key/text 的对象。"})
                key = str(item.get("key", "")).strip()
                text = str(item.get("text", "")).strip()
                if not key or not text:
                    raise ValidationError({"options": "每个选项都必须包含非空 key 和 text。"})
                option_keys.add(key)

            if self.question_type in {QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE}:
                if len(self.correct_answer) != 1:
                    raise ValidationError(
                        {"correct_answer": "单选题和判断题必须且只能有一个答案键。"}
                    )

            missing_keys = [str(ans) for ans in self.correct_answer if str(ans) not in option_keys]
            if missing_keys:
                raise ValidationError({"correct_answer": f"以下答案键在选项中不存在：{missing_keys}"})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class QuizSubmission(models.Model):
    """A single quiz attempt for one lesson."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_submissions")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="quiz_submissions")
    total_questions = models.PositiveIntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    total_score = models.PositiveIntegerField(default=0)
    earned_score = models.PositiveIntegerField(default=0)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-submitted_at", "-id"]
        indexes = [
            models.Index(fields=["user", "submitted_at"], name="idx_submission_user_time"),
            models.Index(fields=["lesson", "submitted_at"], name="idx_submission_lesson_time"),
        ]

    def __str__(self) -> str:
        return f"Submission#{self.id} by {self.user_id} on lesson {self.lesson_id}"


class QuizAnswer(models.Model):
    """Per-question answer record inside one submission."""

    submission = models.ForeignKey(QuizSubmission, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    user_answer = models.JSONField(default=list, blank=True)
    expected_answer = models.JSONField(default=list, blank=True)
    is_correct = models.BooleanField(default=False)
    score_awarded = models.PositiveIntegerField(default=0)
    explanation_snapshot = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["submission_id", "question_id"]
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "question"],
                name="uniq_submission_question",
            )
        ]
        indexes = [
            models.Index(fields=["question", "is_correct"], name="idx_answer_q_correct"),
        ]

    def __str__(self) -> str:
        return f"Answer#{self.id} submission={self.submission_id} question={self.question_id}"


class WrongQuestion(models.Model):
    """Personal wrong-question tracker."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wrong_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="wrong_users")
    wrong_count = models.PositiveIntegerField(default=1)
    resolved = models.BooleanField(default=False)
    first_wrong_at = models.DateTimeField(auto_now_add=True)
    last_wrong_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-last_wrong_at", "-id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "question"],
                name="uniq_wrong_question_per_user",
            )
        ]
        indexes = [
            models.Index(fields=["user", "resolved"], name="idx_wrong_user_resolved"),
        ]

    def __str__(self) -> str:
        return f"WrongQuestion user={self.user_id} question={self.question_id}"
