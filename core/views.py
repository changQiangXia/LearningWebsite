from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import render

from courses.models import Chapter, Course, CourseStatus, Lesson
from forum.models import ForumPost, ForumPostCategory, ForumPostStatus
from guides.models import TeachingGuide
from resources.models import Resource


def home(request):
    """Homepage aligned with the final course portal structure."""
    published_courses = (
        Course.objects.filter(status=CourseStatus.PUBLISHED)
        .prefetch_related(
            Prefetch(
                "chapters",
                queryset=Chapter.objects.filter(is_active=True).prefetch_related(
                    Prefetch(
                        "lessons",
                        queryset=Lesson.objects.filter(is_active=True).order_by("order_no", "id"),
                    )
                ),
            )
        )
        .order_by("-published_at", "-updated_at")
    )
    latest_notes = ForumPost.objects.filter(
        status=ForumPostStatus.PUBLISHED,
        category=ForumPostCategory.SHARE,
    ).select_related("author", "lesson")[:5]
    latest_discussions = ForumPost.objects.filter(
        status=ForumPostStatus.PUBLISHED,
    ).exclude(
        category=ForumPostCategory.SHARE,
    ).select_related("author", "lesson")[:5]
    context = {
        "featured_course": published_courses.first(),
        "published_course_count": published_courses.count(),
        "lesson_count": Lesson.objects.filter(
            chapter__course__status=CourseStatus.PUBLISHED,
            chapter__is_active=True,
            is_active=True,
        ).count(),
        "resource_count": Resource.objects.filter(is_published=True).count(),
        "guide_count": TeachingGuide.objects.filter(is_published=True).count(),
        "latest_notes": latest_notes,
        "latest_discussions": latest_discussions,
    }
    return render(request, "core/home.html", context)


def health(request):
    """Lightweight health endpoint for quick sanity checks."""
    return HttpResponse("ok")
