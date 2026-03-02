from search.models import SearchDocument


def upsert_document(
    source_type,
    source_id,
    title,
    body="",
    keywords="",
    metadata=None,
    is_active=True,
):
    """Create or update one search document."""
    defaults = {
        "title": title,
        "body": body,
        "keywords": keywords,
        "metadata": metadata or {},
        "is_active": is_active,
    }
    SearchDocument.objects.update_or_create(
        source_type=source_type,
        source_id=source_id,
        defaults=defaults,
    )


def remove_document(source_type, source_id):
    """Delete one search document if exists."""
    SearchDocument.objects.filter(source_type=source_type, source_id=source_id).delete()


def index_course(course):
    from courses.models import CourseStatus
    from search.models import SearchSourceType

    keywords = f"{course.slug} {course.created_by.username if course.created_by else ''}".strip()
    upsert_document(
        source_type=SearchSourceType.COURSE,
        source_id=course.id,
        title=course.title,
        body=course.description or "",
        keywords=keywords,
        metadata={"course_id": course.id},
        is_active=course.status == CourseStatus.PUBLISHED,
    )


def index_lesson(lesson):
    from courses.models import CourseStatus
    from search.models import SearchSourceType

    is_active = (
        lesson.is_active
        and lesson.chapter.is_active
        and lesson.chapter.course.status == CourseStatus.PUBLISHED
    )

    upsert_document(
        source_type=SearchSourceType.LESSON,
        source_id=lesson.id,
        title=lesson.title,
        body=lesson.content or "",
        keywords=f"{lesson.chapter.title} {lesson.chapter.course.title}",
        metadata={
            "lesson_id": lesson.id,
            "chapter_id": lesson.chapter_id,
            "course_id": lesson.chapter.course_id,
        },
        is_active=is_active,
    )


def index_forum_post(post):
    from forum.models import ForumPostStatus
    from search.models import SearchSourceType

    upsert_document(
        source_type=SearchSourceType.FORUM_POST,
        source_id=post.id,
        title=post.title,
        body=post.content,
        keywords=post.category,
        metadata={"post_id": post.id},
        is_active=post.status == ForumPostStatus.PUBLISHED,
    )


def index_question(question):
    from courses.models import CourseStatus
    from search.models import SearchSourceType

    is_active = (
        question.is_active
        and question.lesson.is_active
        and question.lesson.chapter.is_active
        and question.lesson.chapter.course.status == CourseStatus.PUBLISHED
    )
    upsert_document(
        source_type=SearchSourceType.QUESTION,
        source_id=question.id,
        title=question.stem[:255],
        body=question.explanation or "",
        keywords=f"{question.lesson.title} {question.lesson.chapter.course.title}",
        metadata={
            "question_id": question.id,
            "lesson_id": question.lesson_id,
            "course_id": question.lesson.chapter.course_id,
        },
        is_active=is_active,
    )
