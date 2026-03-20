from django.db.models import Q
from django.shortcuts import render

from accounts.models import UserRole
from courses.models import Course, CourseStatus, Lesson
from forum.models import ForumPost
from quiz.models import Question
from resources.models import Resource, ResourceAudience
from search.models import SearchDocument, SearchSourceType


FUZZY_KEYWORD_MAP = {
    "人工智障": "人工智能",
    "机气学习": "机器学习",
    "神经网咯": "神经网络",
    "豆包ai": "豆包 AI",
}


def _is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role in {UserRole.TEACHER, UserRole.ADMIN})


def _keyword_variants(keyword):
    keyword = (keyword or "").strip()
    if not keyword:
        return []

    variants = [keyword]
    lower_keyword = keyword.lower()
    if lower_keyword in FUZZY_KEYWORD_MAP:
        variants.append(FUZZY_KEYWORD_MAP[lower_keyword])

    for typo, canonical in FUZZY_KEYWORD_MAP.items():
        if typo in lower_keyword:
            variants.append(keyword.replace(typo, canonical))

    if "ai" in lower_keyword and "人工智能" not in keyword:
        variants.append(keyword.replace("AI", "人工智能").replace("ai", "人工智能"))
    if "人工智能" in keyword and "AI" not in variants:
        variants.append(keyword.replace("人工智能", "AI"))

    deduped = []
    seen = set()
    for item in variants:
        normalized = item.strip()
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


def _doc_matches_lesson(doc, lesson_id):
    metadata = doc.metadata or {}
    return str(metadata.get("lesson_id") or "") == str(lesson_id)


def _visible_resources_for_search(user):
    queryset = Resource.objects.select_related("course", "lesson", "lesson__chapter")
    if user.is_staff:
        return queryset
    if _is_manager(user):
        return queryset.filter(Q(audience=ResourceAudience.ALL) | Q(audience=ResourceAudience.TEACHER))
    return queryset.filter(audience=ResourceAudience.ALL)


def _make_snippet(doc, terms):
    content = " ".join(part for part in [doc.title, doc.body] if part).strip()
    if not content:
        return ""

    lowered = content.lower()
    terms = [term for term in terms if term]
    start = 0
    for term in terms:
        idx = lowered.find(term.lower())
        if idx >= 0:
            start = max(0, idx - 28)
            break

    snippet = content[start : start + 140].strip()
    if start > 0:
        snippet = f"...{snippet}"
    if len(content) > start + 140:
        snippet = f"{snippet}..."
    return snippet


def _attach_search_meta(objects, doc_map, source_type, terms):
    for obj in objects:
        doc = doc_map.get((source_type, obj.id))
        obj.search_snippet = _make_snippet(doc, terms) if doc else ""
    return objects


def index(request):
    keyword = request.GET.get("q", "").strip()
    type_filter = request.GET.get("type", "").strip().lower()
    lesson_filter = request.GET.get("lesson", "").strip()
    highlight_terms = _keyword_variants(keyword)

    courses = []
    lessons = []
    posts = []
    questions = []
    resources = []

    if keyword:
        query = Q()
        for term in highlight_terms:
            query |= Q(title__icontains=term) | Q(body__icontains=term) | Q(keywords__icontains=term)

        docs = list(
            SearchDocument.objects.filter(is_active=True)
            .filter(query)
            .order_by("-updated_at", "-id")[:200]
        )

        if type_filter:
            allowed_map = {
                "course": {SearchSourceType.COURSE},
                "lesson": {SearchSourceType.LESSON},
                "post": {SearchSourceType.FORUM_POST},
                "resource": {SearchSourceType.RESOURCE},
                "question": {SearchSourceType.QUESTION},
            }
            allowed_types = allowed_map.get(type_filter, set())
            if allowed_types:
                docs = [doc for doc in docs if doc.source_type in allowed_types]

        if lesson_filter.isdigit():
            docs = [doc for doc in docs if _doc_matches_lesson(doc, int(lesson_filter))]

        doc_map = {(doc.source_type, doc.source_id): doc for doc in docs}
        grouped_ids = {
            SearchSourceType.COURSE: [],
            SearchSourceType.LESSON: [],
            SearchSourceType.FORUM_POST: [],
            SearchSourceType.QUESTION: [],
            SearchSourceType.RESOURCE: [],
        }
        for doc in docs:
            grouped_ids.setdefault(doc.source_type, []).append(doc.source_id)

        course_ids = grouped_ids.get(SearchSourceType.COURSE, [])
        lesson_ids = grouped_ids.get(SearchSourceType.LESSON, [])
        post_ids = grouped_ids.get(SearchSourceType.FORUM_POST, [])
        question_ids = grouped_ids.get(SearchSourceType.QUESTION, [])
        resource_ids = grouped_ids.get(SearchSourceType.RESOURCE, [])

        course_map = {obj.id: obj for obj in Course.objects.filter(id__in=course_ids)}
        lesson_map = {
            obj.id: obj
            for obj in Lesson.objects.select_related("chapter", "chapter__course").filter(id__in=lesson_ids)
        }
        post_map = {
            obj.id: obj
            for obj in ForumPost.objects.select_related("author", "lesson", "lesson__chapter", "lesson__chapter__course")
            .filter(id__in=post_ids)
        }
        question_map = {
            obj.id: obj
            for obj in Question.objects.select_related("lesson", "lesson__chapter", "lesson__chapter__course").filter(
                id__in=question_ids
            )
        }
        resource_map = {
            obj.id: obj
            for obj in _visible_resources_for_search(request.user).filter(id__in=resource_ids)
        }

        courses = _attach_search_meta(
            [course_map[item_id] for item_id in course_ids if item_id in course_map][:20],
            doc_map,
            SearchSourceType.COURSE,
            highlight_terms,
        )
        lessons = _attach_search_meta(
            [lesson_map[item_id] for item_id in lesson_ids if item_id in lesson_map][:20],
            doc_map,
            SearchSourceType.LESSON,
            highlight_terms,
        )
        posts = _attach_search_meta(
            [post_map[item_id] for item_id in post_ids if item_id in post_map][:20],
            doc_map,
            SearchSourceType.FORUM_POST,
            highlight_terms,
        )
        questions = _attach_search_meta(
            [question_map[item_id] for item_id in question_ids if item_id in question_map][:20],
            doc_map,
            SearchSourceType.QUESTION,
            highlight_terms,
        )
        resources = _attach_search_meta(
            [resource_map[item_id] for item_id in resource_ids if item_id in resource_map][:20],
            doc_map,
            SearchSourceType.RESOURCE,
            highlight_terms,
        )

    total = len(courses) + len(lessons) + len(posts) + len(questions) + len(resources)
    return render(
        request,
        "search/results.html",
        {
            "keyword": keyword,
            "highlight_terms": highlight_terms,
            "courses": courses,
            "lessons": lessons,
            "posts": posts,
            "questions": questions,
            "resources": resources,
            "total": total,
            "type_filter": type_filter,
            "lesson_filter": lesson_filter,
            "lesson_options": list(
                Lesson.objects.select_related("chapter", "chapter__course")
                .filter(chapter__course__status=CourseStatus.PUBLISHED, chapter__is_active=True, is_active=True)
                .order_by("chapter__course__title", "chapter__order_no", "order_no", "id")
            ),
            "normalized_keyword": highlight_terms[1] if len(highlight_terms) > 1 else "",
        },
    )
