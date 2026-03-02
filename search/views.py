from django.db.models import Q
from django.shortcuts import render

from courses.models import Course, Lesson
from forum.models import ForumPost
from quiz.models import Question
from search.models import SearchDocument, SearchSourceType


def index(request):
    keyword = request.GET.get("q", "").strip()

    courses = []
    lessons = []
    posts = []
    questions = []

    if keyword:
        docs = (
            SearchDocument.objects.filter(is_active=True)
            .filter(Q(title__icontains=keyword) | Q(body__icontains=keyword) | Q(keywords__icontains=keyword))
            .order_by("-updated_at", "-id")[:120]
        )
        grouped_ids = {
            SearchSourceType.COURSE: [],
            SearchSourceType.LESSON: [],
            SearchSourceType.FORUM_POST: [],
            SearchSourceType.QUESTION: [],
        }
        for doc in docs:
            grouped_ids.setdefault(doc.source_type, []).append(doc.source_id)

        course_ids = grouped_ids.get(SearchSourceType.COURSE, [])
        lesson_ids = grouped_ids.get(SearchSourceType.LESSON, [])
        post_ids = grouped_ids.get(SearchSourceType.FORUM_POST, [])
        question_ids = grouped_ids.get(SearchSourceType.QUESTION, [])

        course_map = {obj.id: obj for obj in Course.objects.filter(id__in=course_ids)}
        lesson_map = {
            obj.id: obj
            for obj in Lesson.objects.select_related("chapter", "chapter__course").filter(id__in=lesson_ids)
        }
        post_map = {obj.id: obj for obj in ForumPost.objects.select_related("author").filter(id__in=post_ids)}
        question_map = {
            obj.id: obj
            for obj in Question.objects.select_related("lesson", "lesson__chapter", "lesson__chapter__course").filter(
                id__in=question_ids
            )
        }

        courses = [course_map[item_id] for item_id in course_ids if item_id in course_map][:20]
        lessons = [lesson_map[item_id] for item_id in lesson_ids if item_id in lesson_map][:20]
        posts = [post_map[item_id] for item_id in post_ids if item_id in post_map][:20]
        questions = [question_map[item_id] for item_id in question_ids if item_id in question_map][:20]

    total = len(courses) + len(lessons) + len(posts) + len(questions)
    return render(
        request,
        "search/results.html",
        {
            "keyword": keyword,
            "courses": courses,
            "lessons": lessons,
            "posts": posts,
            "questions": questions,
            "total": total,
        },
    )
