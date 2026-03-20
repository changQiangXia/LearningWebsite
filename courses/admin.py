from django.contrib import admin

from .models import Chapter, ContentAuditLog, Course, CourseGlossaryTerm, LearningProgress, Lesson


class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 0
    fields = ("title", "order_no", "is_active")


class CourseGlossaryTermInline(admin.TabularInline):
    model = CourseGlossaryTerm
    extra = 0
    fields = ("term", "order_no")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "created_by", "published_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "description", "slug")
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ("created_by",)
    inlines = [ChapterInline, CourseGlossaryTermInline]


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = ("title", "order_no", "estimated_minutes", "is_free_preview", "is_active")


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order_no", "is_active", "updated_at")
    list_filter = ("course", "is_active")
    search_fields = ("title", "course__title")
    raw_id_fields = ("course",)
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "chapter", "order_no", "estimated_minutes", "is_free_preview", "is_active")
    list_filter = ("is_free_preview", "is_active", "chapter__course")
    search_fields = ("title", "chapter__title", "chapter__course__title")
    raw_id_fields = ("chapter",)


@admin.register(LearningProgress)
class LearningProgressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "lesson", "view_count", "completed", "completed_at", "last_viewed_at")
    list_filter = ("completed", "last_viewed_at")
    search_fields = ("user__username", "lesson__title", "lesson__chapter__course__title")
    raw_id_fields = ("user", "lesson")


@admin.register(ContentAuditLog)
class ContentAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "actor", "target_type", "target_id", "action", "course")
    list_filter = ("target_type", "action", "created_at")
    search_fields = ("message", "actor__username", "course__title")
    raw_id_fields = ("actor", "course", "chapter", "lesson")


@admin.register(CourseGlossaryTerm)
class CourseGlossaryTermAdmin(admin.ModelAdmin):
    list_display = ("term", "course", "order_no")
    list_filter = ("course",)
    search_fields = ("term", "definition", "course__title")
    raw_id_fields = ("course",)
