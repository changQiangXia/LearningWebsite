from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Prefetch, Q
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from accounts.models import UserRole
from guides.models import TeachingGuide
from quiz.models import Question
from resources.models import Resource, ResourceAudience

from .audit import log_content_action
from .forms import ManageChapterForm, ManageCourseForm, ManageLessonForm
from .models import AuditTargetType, Chapter, ContentAuditLog, Course, CourseGlossaryTerm, CourseStatus, LearningProgress, Lesson


def _is_manager(user):
    """Teacher/admin/staff users are considered content managers."""
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role in {UserRole.TEACHER, UserRole.ADMIN})


def _visible_courses(user):
    """Courses visible to current user."""
    if not user.is_authenticated:
        return Course.objects.filter(status=CourseStatus.PUBLISHED)
    if user.is_staff:
        return Course.objects.all()
    if _is_manager(user):
        return Course.objects.filter(Q(status=CourseStatus.PUBLISHED) | Q(created_by=user))
    return Course.objects.filter(status=CourseStatus.PUBLISHED)


def _visible_lessons(user):
    qs = Lesson.objects.select_related("chapter", "chapter__course")
    public_filter = Q(
        chapter__course__status=CourseStatus.PUBLISHED,
        chapter__is_active=True,
        is_active=True,
    )
    if not user.is_authenticated:
        return qs.filter(public_filter)
    if user.is_staff:
        return qs
    if _is_manager(user):
        return qs.filter(public_filter | Q(chapter__course__created_by=user))
    return qs.filter(public_filter)


def _managed_courses(user):
    qs = Course.objects.select_related("created_by")
    if user.is_staff:
        return qs
    return qs.filter(created_by=user)


def _managed_chapters(user):
    qs = Chapter.objects.select_related("course", "course__created_by")
    if user.is_staff:
        return qs
    return qs.filter(course__created_by=user)


def _managed_lessons(user):
    qs = Lesson.objects.select_related("chapter", "chapter__course", "chapter__course__created_by")
    if user.is_staff:
        return qs
    return qs.filter(chapter__course__created_by=user)


def _can_manage_course(user, course):
    return user.is_staff or course.created_by_id == user.id


def _add_form_validation_error(form, exc):
    if getattr(exc, "message_dict", None):
        for field, messages in exc.message_dict.items():
            target = None if field == "__all__" else field
            for message in messages:
                form.add_error(target, message)
        return
    form.add_error(None, str(exc))


def _embed_video_url(url):
    if not url:
        return ""
    if "youtube.com/watch?v=" in url:
        video_id = url.split("watch?v=", 1)[1].split("&", 1)[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "youtu.be/" in url:
        video_id = url.split("youtu.be/", 1)[1].split("?", 1)[0]
        return f"https://www.youtube.com/embed/{video_id}"
    if "bilibili.com/video/" in url:
        video_id = url.split("bilibili.com/video/", 1)[1].split("?", 1)[0].strip("/")
        if video_id:
            return f"https://player.bilibili.com/player.html?bvid={video_id}&page=1"
    return url


def _interactive_prompt_for_lesson(lesson):
    prompt_map = {
        1: {
            "title": "互动节点：身边的 AI 观察",
            "body": "试着说出一个生活中的 AI 场景，例如推荐系统、地图导航或人脸解锁，并思考它依赖了什么数据。",
        },
        2: {
            "title": "互动节点：技术基石配对",
            "body": "把“数据、算法、算力”分别和一个真实案例联系起来，例如语音识别为什么既需要大量语音数据，也需要算力支持。",
        },
        3: {
            "title": "互动节点：AI 伦理判断",
            "body": "阅读案例后思考：如果算法偏见影响了招聘结果，责任应该由谁承担？",
        },
        4: {
            "title": "互动节点：单元总结反思",
            "body": "用一句话总结本单元最重要的一个观点，并写下未来最想继续探索的 AI 方向。",
        },
    }
    return prompt_map.get(
        lesson.order_no,
        {
            "title": "互动节点：开放反思",
            "body": "结合本课时内容，提出一个值得继续追问的问题。",
        },
    )


def course_list(request):
    courses = list(
        _visible_courses(request.user)
        .select_related("created_by")
        .prefetch_related(
            Prefetch("chapters", queryset=Chapter.objects.filter(is_active=True).order_by("order_no", "id")),
        )
        .order_by("-updated_at", "-created_at")
    )

    if request.user.is_authenticated and courses:
        course_ids = [course.id for course in courses]
        total_by_course = {
            row["chapter__course_id"]: row["total"]
            for row in Lesson.objects.filter(
                chapter__course_id__in=course_ids,
                chapter__is_active=True,
                is_active=True,
            )
            .values("chapter__course_id")
            .annotate(total=Count("id"))
        }
        completed_by_course = {
            row["lesson__chapter__course_id"]: row["total"]
            for row in LearningProgress.objects.filter(
                user=request.user,
                completed=True,
                lesson__chapter__course_id__in=course_ids,
                lesson__chapter__is_active=True,
                lesson__is_active=True,
            )
            .values("lesson__chapter__course_id")
            .annotate(total=Count("id"))
        }
        for course in courses:
            total = total_by_course.get(course.id, 0)
            completed = completed_by_course.get(course.id, 0)
            course.progress_total = total
            course.progress_completed = completed
            course.progress_rate = round((completed / total) * 100, 2) if total else 0

    return render(request, "courses/course_list.html", {"courses": courses})


def course_detail(request, slug: str):
    course = get_object_or_404(_visible_courses(request.user), slug=slug)
    can_manage_course = _is_manager(request.user) and _can_manage_course(request.user, course)

    if can_manage_course:
        chapter_qs = course.chapters.prefetch_related("lessons").all()
    else:
        chapter_qs = course.chapters.filter(is_active=True).prefetch_related(
            Prefetch("lessons", queryset=Lesson.objects.filter(is_active=True).order_by("order_no", "id"))
        )
    chapters = list(chapter_qs)

    completed_lesson_ids = set()
    if request.user.is_authenticated:
        completed_lesson_ids = set(
            LearningProgress.objects.filter(
                user=request.user,
                completed=True,
                lesson__chapter__course=course,
                lesson__chapter__is_active=True,
                lesson__is_active=True,
            ).values_list("lesson_id", flat=True)
        )

    total_lessons = sum(len(chapter.lessons.all()) for chapter in chapters)
    completed_count = len(completed_lesson_ids)
    completion_rate = round((completed_count / total_lessons) * 100, 2) if total_lessons else 0
    if can_manage_course:
        related_resources = list(
            Resource.objects.filter(course=course).order_by("-updated_at", "-id")[:6]
        )
        related_guides = list(
            TeachingGuide.objects.filter(course=course).order_by("order_no", "id")[:6]
        )
    else:
        related_resources = list(
            Resource.objects.filter(course=course, is_published=True, audience=ResourceAudience.ALL).order_by(
                "lesson__order_no",
                "sort_order",
                "-updated_at",
                "-id",
            )[:8]
        )
        related_guides = list(
            TeachingGuide.objects.filter(course=course, is_published=True).order_by("order_no", "id")[:6]
        )
    glossary_terms = list(CourseGlossaryTerm.objects.filter(course=course).order_by("order_no", "id")[:20])
    featured_videos = [lesson for chapter in chapters for lesson in chapter.lessons.all() if lesson.video_url][:4]

    return render(
        request,
        "courses/course_detail.html",
        {
            "course": course,
            "chapters": chapters,
            "completed_lesson_ids": completed_lesson_ids,
            "total_lessons": total_lessons,
            "completed_count": completed_count,
            "completion_rate": completion_rate,
            "can_manage_course": can_manage_course,
            "related_resources": related_resources,
            "related_guides": related_guides,
            "glossary_terms": glossary_terms,
            "featured_videos": featured_videos,
        },
    )


def lesson_detail(request, lesson_id: int):
    lesson = get_object_or_404(_visible_lessons(request.user), id=lesson_id)
    course = lesson.chapter.course
    can_manage_lesson = _is_manager(request.user) and _can_manage_course(request.user, course)

    lesson_nav_qs = Lesson.objects.filter(chapter__course=course).select_related("chapter")
    if not can_manage_lesson:
        lesson_nav_qs = lesson_nav_qs.filter(chapter__is_active=True, is_active=True)
    all_lessons = list(lesson_nav_qs.order_by("chapter__order_no", "order_no", "id"))
    current_index = next((idx for idx, item in enumerate(all_lessons) if item.id == lesson.id), -1)
    previous_lesson = all_lessons[current_index - 1] if current_index > 0 else None
    next_lesson = all_lessons[current_index + 1] if 0 <= current_index < len(all_lessons) - 1 else None

    question_count = Question.objects.filter(lesson=lesson, is_active=True).count()
    progress = None
    if request.user.is_authenticated and lesson.is_active and lesson.chapter.is_active:
        progress, created = LearningProgress.objects.get_or_create(
            user=request.user,
            lesson=lesson,
            defaults={"view_count": 1},
        )
        if not created:
            progress.view_count += 1
            progress.save(update_fields=["view_count", "last_viewed_at"])

    if can_manage_lesson:
        related_resources = list(
            Resource.objects.filter(Q(lesson=lesson) | Q(course=course, lesson__isnull=True))
            .order_by("sort_order", "-updated_at", "-id")[:10]
        )
    elif _is_manager(request.user):
        related_resources = list(
            Resource.objects.filter(
                Q(lesson=lesson) | Q(course=course, lesson__isnull=True),
                is_published=True,
            )
            .filter(Q(audience=ResourceAudience.ALL) | Q(audience=ResourceAudience.TEACHER))
            .order_by("sort_order", "-updated_at", "-id")[:10]
        )
    else:
        related_resources = list(
            Resource.objects.filter(
                Q(lesson=lesson) | Q(course=course, lesson__isnull=True),
                is_published=True,
                audience=ResourceAudience.ALL,
            ).order_by("sort_order", "-updated_at", "-id")[:10]
        )
    guide_qs = TeachingGuide.objects.filter(course=course)
    if not can_manage_lesson:
        guide_qs = guide_qs.filter(is_published=True)
    glossary_terms = list(CourseGlossaryTerm.objects.filter(course=course).order_by("order_no", "id")[:15])

    return render(
        request,
        "courses/lesson_detail.html",
        {
            "lesson": lesson,
            "course": course,
            "previous_lesson": previous_lesson,
            "next_lesson": next_lesson,
            "all_lessons": all_lessons,
            "question_count": question_count,
            "progress": progress,
            "can_manage_lesson": can_manage_lesson,
            "interactive_prompt": _interactive_prompt_for_lesson(lesson),
            "embedded_video_url": _embed_video_url(lesson.video_url),
            "related_resources": related_resources,
            "teaching_guides": list(guide_qs.order_by("order_no", "id")[:4]),
            "glossary_terms": glossary_terms,
        },
    )


@login_required
def mark_lesson_complete(request, lesson_id: int):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    lesson_obj = get_object_or_404(_visible_lessons(request.user).filter(chapter__is_active=True, is_active=True), id=lesson_id)

    progress, _ = LearningProgress.objects.get_or_create(user=request.user, lesson=lesson_obj)
    if not progress.completed:
        progress.completed = True
        progress.completed_at = timezone.now()
        progress.save(update_fields=["completed", "completed_at", "last_viewed_at"])
        messages.success(request, "课时已标记为完成。")
    else:
        messages.info(request, "该课时已是完成状态。")

    return redirect("courses:lesson_detail", lesson_id=lesson_obj.id)


@login_required
def manage_dashboard(request):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    courses = list(_managed_courses(request.user).order_by("-updated_at", "-created_at"))
    course_ids = [item.id for item in courses]

    lessons_qs = Lesson.objects.filter(chapter__course_id__in=course_ids)
    recent_lessons = list(
        lessons_qs.select_related("chapter", "chapter__course")
        .order_by("-updated_at", "-id")[:10]
    )
    recent_questions = list(
        Question.objects.filter(lesson__chapter__course_id__in=course_ids)
        .select_related("lesson", "lesson__chapter", "lesson__chapter__course")
        .order_by("-updated_at", "-id")[:10]
    )
    recent_logs_qs = ContentAuditLog.objects.select_related("actor", "course").order_by("-created_at", "-id")
    if not request.user.is_staff:
        recent_logs_qs = recent_logs_qs.filter(course__created_by=request.user)
    recent_logs = list(recent_logs_qs[:12])

    context = {
        "courses": courses[:12],
        "recent_lessons": recent_lessons,
        "recent_questions": recent_questions,
        "recent_resources": list(
            Resource.objects.filter(course_id__in=course_ids).select_related("course").order_by("-updated_at", "-id")[:8]
        ),
        "recent_guides": list(
            TeachingGuide.objects.filter(course_id__in=course_ids).select_related("course").order_by("-updated_at", "-id")[:8]
        ),
        "recent_logs": recent_logs,
        "total_courses": len(courses),
        "published_courses": sum(1 for c in courses if c.status == CourseStatus.PUBLISHED),
        "draft_courses": sum(1 for c in courses if c.status == CourseStatus.DRAFT),
        "archived_courses": sum(1 for c in courses if c.status == CourseStatus.ARCHIVED),
        "total_lessons": lessons_qs.filter(chapter__is_active=True, is_active=True).count(),
        "inactive_chapters": Chapter.objects.filter(course_id__in=course_ids, is_active=False).count(),
        "inactive_lessons": lessons_qs.filter(Q(is_active=False) | Q(chapter__is_active=False)).count(),
        "total_questions": Question.objects.filter(lesson__chapter__course_id__in=course_ids).count(),
        "total_resources": Resource.objects.filter(course_id__in=course_ids).count(),
        "total_guides": TeachingGuide.objects.filter(course_id__in=course_ids).count(),
    }
    return render(request, "courses/manage_dashboard.html", context)


@login_required
def manage_course_create(request):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    if request.method == "POST":
        form = ManageCourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save(commit=False)
            if not course.created_by_id:
                course.created_by = request.user
            if not request.user.is_staff:
                course.created_by = request.user
            course.save()
            log_content_action(
                actor=request.user,
                target_type=AuditTargetType.COURSE,
                target_id=course.id,
                action="create",
                message=f"创建课程《{course.title}》。",
                course=course,
            )
            messages.success(request, "课程创建成功。")
            return redirect("courses:manage_dashboard")
    else:
        form = ManageCourseForm()

    return render(request, "courses/manage_course_form.html", {"form": form, "mode": "create"})


@login_required
def manage_course_edit(request, course_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    course = get_object_or_404(_managed_courses(request.user), id=course_id)
    if request.method == "POST":
        form = ManageCourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            previous_status = course.status
            course = form.save(commit=False)
            if not request.user.is_staff:
                course.created_by = request.user
            course.save()
            log_content_action(
                actor=request.user,
                target_type=AuditTargetType.COURSE,
                target_id=course.id,
                action="update",
                message=f"更新课程《{course.title}》。",
                course=course,
                payload={"status_from": previous_status, "status_to": course.status},
            )
            messages.success(request, "课程更新成功。")
            return redirect("courses:manage_dashboard")
    else:
        form = ManageCourseForm(instance=course)

    return render(
        request,
        "courses/manage_course_form.html",
        {"form": form, "mode": "edit", "course": course},
    )


@login_required
def manage_course_toggle_status(request, course_id: int):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    course = get_object_or_404(_managed_courses(request.user), id=course_id)
    previous_status = course.status
    if course.status == CourseStatus.PUBLISHED:
        course.status = CourseStatus.DRAFT
    elif course.status == CourseStatus.DRAFT:
        course.status = CourseStatus.PUBLISHED
    else:
        messages.info(request, "已归档课程不可直接发布，请先恢复为草稿。")
        return redirect("courses:manage_dashboard")

    course.save()
    log_content_action(
        actor=request.user,
        target_type=AuditTargetType.COURSE,
        target_id=course.id,
        action="toggle_status",
        message=f"课程状态调整为“{course.get_status_display()}”。",
        course=course,
        payload={"status_from": previous_status, "status_to": course.status},
    )
    messages.success(request, f"课程状态已更新为：{course.get_status_display()}。")
    return redirect("courses:manage_dashboard")


@login_required
def manage_course_toggle_archive(request, course_id: int):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    course = get_object_or_404(_managed_courses(request.user), id=course_id)
    if course.status == CourseStatus.ARCHIVED:
        course.status = CourseStatus.DRAFT
        action = "restore"
        message_text = "课程已恢复为草稿状态。"
    else:
        course.status = CourseStatus.ARCHIVED
        action = "archive"
        message_text = "课程已归档。"
    course.save()
    log_content_action(
        actor=request.user,
        target_type=AuditTargetType.COURSE,
        target_id=course.id,
        action=action,
        message=message_text,
        course=course,
    )
    messages.success(request, message_text)
    return redirect("courses:manage_dashboard")


@login_required
def manage_chapter_create(request, course_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    course = get_object_or_404(_managed_courses(request.user), id=course_id)
    if request.method == "POST":
        form = ManageChapterForm(request.POST)
        if form.is_valid():
            chapter = form.save(commit=False)
            chapter.course = course
            try:
                chapter.full_clean()
            except ValidationError as exc:
                _add_form_validation_error(form, exc)
            else:
                chapter.save()
                log_content_action(
                    actor=request.user,
                    target_type=AuditTargetType.CHAPTER,
                    target_id=chapter.id,
                    action="create",
                    message=f"创建章节《{chapter.title}》。",
                    course=course,
                    chapter=chapter,
                )
                messages.success(request, "章节创建成功。")
                return redirect("courses:course_detail", slug=course.slug)
    else:
        form = ManageChapterForm()

    return render(
        request,
        "courses/manage_chapter_form.html",
        {"form": form, "course": course, "mode": "create"},
    )


@login_required
def manage_chapter_edit(request, chapter_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    chapter = get_object_or_404(_managed_chapters(request.user), id=chapter_id)
    if request.method == "POST":
        form = ManageChapterForm(request.POST, instance=chapter)
        if form.is_valid():
            chapter = form.save(commit=False)
            try:
                chapter.full_clean()
            except ValidationError as exc:
                _add_form_validation_error(form, exc)
            else:
                chapter.save()
                log_content_action(
                    actor=request.user,
                    target_type=AuditTargetType.CHAPTER,
                    target_id=chapter.id,
                    action="update",
                    message=f"更新章节《{chapter.title}》。",
                    course=chapter.course,
                    chapter=chapter,
                )
                messages.success(request, "章节更新成功。")
                return redirect("courses:course_detail", slug=chapter.course.slug)
    else:
        form = ManageChapterForm(instance=chapter)

    return render(
        request,
        "courses/manage_chapter_form.html",
        {"form": form, "course": chapter.course, "chapter": chapter, "mode": "edit"},
    )


@login_required
def manage_chapter_toggle_active(request, chapter_id: int):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    chapter = get_object_or_404(_managed_chapters(request.user), id=chapter_id)
    chapter.is_active = not chapter.is_active
    chapter.save(update_fields=["is_active", "updated_at"])
    state_label = "启用" if chapter.is_active else "停用"
    log_content_action(
        actor=request.user,
        target_type=AuditTargetType.CHAPTER,
        target_id=chapter.id,
        action="toggle_active",
        message=f"章节《{chapter.title}》状态调整为“{state_label}”。",
        course=chapter.course,
        chapter=chapter,
        payload={"is_active": chapter.is_active},
    )
    messages.success(request, f"章节当前状态：{state_label}。")
    return redirect("courses:course_detail", slug=chapter.course.slug)


@login_required
def manage_lesson_create(request, chapter_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    chapter = get_object_or_404(_managed_chapters(request.user), id=chapter_id)

    if request.method == "POST":
        form = ManageLessonForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.chapter = chapter
            try:
                lesson.full_clean()
            except ValidationError as exc:
                _add_form_validation_error(form, exc)
            else:
                lesson.save()
                log_content_action(
                    actor=request.user,
                    target_type=AuditTargetType.LESSON,
                    target_id=lesson.id,
                    action="create",
                    message=f"创建课时《{lesson.title}》。",
                    course=chapter.course,
                    chapter=chapter,
                    lesson=lesson,
                )
                messages.success(request, "课时创建成功。")
                return redirect("courses:lesson_detail", lesson_id=lesson.id)
    else:
        form = ManageLessonForm()

    return render(
        request,
        "courses/manage_lesson_form.html",
        {"form": form, "chapter": chapter, "mode": "create"},
    )


@login_required
def manage_lesson_edit(request, lesson_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    lesson = get_object_or_404(_managed_lessons(request.user), id=lesson_id)
    if request.method == "POST":
        form = ManageLessonForm(request.POST, instance=lesson)
        if form.is_valid():
            lesson = form.save(commit=False)
            try:
                lesson.full_clean()
            except ValidationError as exc:
                _add_form_validation_error(form, exc)
            else:
                lesson.save()
                log_content_action(
                    actor=request.user,
                    target_type=AuditTargetType.LESSON,
                    target_id=lesson.id,
                    action="update",
                    message=f"更新课时《{lesson.title}》。",
                    course=lesson.chapter.course,
                    chapter=lesson.chapter,
                    lesson=lesson,
                )
                messages.success(request, "课时更新成功。")
                return redirect("courses:lesson_detail", lesson_id=lesson.id)
    else:
        form = ManageLessonForm(instance=lesson)

    return render(
        request,
        "courses/manage_lesson_form.html",
        {"form": form, "chapter": lesson.chapter, "lesson": lesson, "mode": "edit"},
    )


@login_required
def manage_lesson_toggle_active(request, lesson_id: int):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    lesson = get_object_or_404(_managed_lessons(request.user), id=lesson_id)
    lesson.is_active = not lesson.is_active
    lesson.save(update_fields=["is_active", "updated_at"])
    state_label = "启用" if lesson.is_active else "停用"
    log_content_action(
        actor=request.user,
        target_type=AuditTargetType.LESSON,
        target_id=lesson.id,
        action="toggle_active",
        message=f"课时《{lesson.title}》状态调整为“{state_label}”。",
        course=lesson.chapter.course,
        chapter=lesson.chapter,
        lesson=lesson,
        payload={"is_active": lesson.is_active},
    )
    messages.success(request, f"课时当前状态：{state_label}。")
    return redirect("courses:lesson_detail", lesson_id=lesson.id)
