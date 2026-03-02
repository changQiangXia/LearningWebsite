from django.contrib import admin

from .models import Question, QuizAnswer, QuizSubmission, WrongQuestion


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "short_stem",
        "question_type",
        "difficulty",
        "lesson",
        "score",
        "is_active",
        "updated_at",
    )
    list_filter = ("question_type", "difficulty", "is_active")
    search_fields = ("stem", "explanation", "lesson__title", "lesson__chapter__course__title")
    raw_id_fields = ("lesson", "created_by")

    @admin.display(description="Stem")
    def short_stem(self, obj: Question) -> str:
        text = obj.stem.strip().replace("\n", " ")
        return f"{text[:45]}..." if len(text) > 45 else text


class QuizAnswerInline(admin.TabularInline):
    model = QuizAnswer
    extra = 0
    fields = ("question", "is_correct", "score_awarded", "user_answer", "expected_answer")
    readonly_fields = ("question", "is_correct", "score_awarded", "user_answer", "expected_answer")
    can_delete = False


@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "lesson",
        "earned_score",
        "total_score",
        "correct_count",
        "total_questions",
        "accuracy",
        "submitted_at",
    )
    list_filter = ("submitted_at", "lesson__chapter__course")
    search_fields = ("user__username", "lesson__title", "lesson__chapter__course__title")
    raw_id_fields = ("user", "lesson")
    inlines = [QuizAnswerInline]


@admin.register(QuizAnswer)
class QuizAnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "question", "is_correct", "score_awarded", "created_at")
    list_filter = ("is_correct", "created_at")
    search_fields = ("submission__user__username", "question__stem")
    raw_id_fields = ("submission", "question")


@admin.register(WrongQuestion)
class WrongQuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "question", "wrong_count", "resolved", "last_wrong_at")
    list_filter = ("resolved", "last_wrong_at")
    search_fields = ("user__username", "question__stem", "question__lesson__title")
    raw_id_fields = ("user", "question")
