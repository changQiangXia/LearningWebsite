from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Prefetch, Q
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from accounts.models import UserRole
from analytics.models import LearningFeedback
from forum.models import ForumPost, ForumPostCategory, ForumPostStatus
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
            "title": "互动节点：我身边的 AI",
            "body": "观察生活中的一个人工智能场景，例如语音助手、拍照搜题或刷脸支付，并尝试说明它为生活带来了什么便利。",
        },
        2: {
            "title": "互动节点：行业应用发现",
            "body": "从医疗、交通、教育、家居中任选一个领域，说明人工智能是如何提升效率和便利度的。",
        },
        3: {
            "title": "互动节点：伦理判断",
            "body": "阅读一个人工智能伦理案例后，思考隐私安全、算法公平性和责任边界分别体现在哪里。",
        },
        4: {
            "title": "互动节点：未来与总结",
            "body": "用几句话概括本单元最重要的收获，并说出一个最想继续探索的人工智能方向。",
        },
    }
    return prompt_map.get(
        lesson.order_no,
        {
            "title": "互动节点：开放反思",
            "body": "结合本课时内容，提出一个值得继续追问的问题。",
        },
    )


def _lesson_activity_blocks(lesson):
    activity_map = {
        1: [
            {
                "title": "课堂练习 1：AI 场景辨认",
                "type": "single_choice",
                "prompt": "下面哪一项最符合“基于数据做感知与判断”的 AI 应用特征？",
                "options": [
                    "普通机械闹钟按固定时间响铃",
                    "导航软件根据实时路况动态调整路线",
                    "纸质课本按页码顺序排版",
                    "黑板擦只能靠人工移动",
                ],
                "answer": 1,
                "explanation": "导航会结合地图、定位和交通流量数据动态给出判断，因此更符合 AI 应用场景。",
            },
            {
                "title": "课堂练习 2：生活观察",
                "type": "reflection",
                "prompt": "写出一个身边见过的 AI 场景，并尝试说明它的输入数据和输出结果。",
                "tips": [
                    "优先选择熟悉的真实场景，例如推荐系统、刷脸解锁、语音助手。",
                    "可按“输入了什么数据”“给出了什么结果”两个维度组织表达。",
                ],
            },
        ],
        2: [
            {
                "title": "课堂练习 1：应用场景辨认",
                "type": "single_choice",
                "prompt": "下面哪一项最符合人工智能在交通领域的应用？",
                "options": [
                    "自动驾驶",
                    "普通铅笔",
                    "纸质作业本",
                    "黑板擦",
                ],
                "answer": 0,
                "explanation": "自动驾驶是人工智能在交通领域中的代表性应用，其核心是感知、识别与决策。",
            },
            {
                "title": "课堂练习 2：应用案例观察",
                "type": "reflection",
                "prompt": "从医疗、交通、教育、家居四个方向中任选一个，说明人工智能带来了什么便利。",
                "tips": [
                    "可以围绕“它帮人完成了什么任务”“比传统方式方便在哪里”两个问题组织答案。",
                    "尽量使用真实案例，例如智能导航、医疗辅助诊断、个性化学习推荐或智能音箱。",
                ],
            },
        ],
        3: [
            {
                "title": "课堂练习 1：伦理判断",
                "type": "single_choice",
                "prompt": "当 AI 招聘系统因训练数据偏差而长期忽视某类候选人时，更合理的做法是什么？",
                "options": [
                    "继续直接使用结果，不做人工复核",
                    "停止关注公平性，只追求处理速度",
                    "检查训练数据和规则，并加入人工监督",
                    "把问题完全归咎于用户不会使用系统",
                ],
                "answer": 2,
                "explanation": "AI 伦理问题通常需要从数据、算法和人工监督三个层面共同修正，而不是放任偏差继续扩大。",
            },
            {
                "title": "课堂练习 2：责任讨论",
                "type": "reflection",
                "prompt": "如果 AI 结果影响了个人权益，开发者、平台和使用者分别应承担哪些责任？",
                "tips": [
                    "可从“设计是否合理”“是否及时告知”“是否有人类复核”三个角度回答。",
                    "尽量结合具体案例，不只停留在抽象观点。",
                ],
            },
        ],
        4: [
            {
                "title": "课堂练习 1：未来趋势判断",
                "type": "single_choice",
                "prompt": "下面哪一项更符合人工智能未来发展的方向？",
                "options": [
                    "多模态融合与人机协同",
                    "只依赖纸质记录，不再使用数据",
                    "完全停止所有算法更新",
                    "不再需要任何人类判断",
                ],
                "answer": 0,
                "explanation": "人工智能未来通常会朝着多模态融合、自主学习和人机协同等方向继续发展。",
            },
            {
                "title": "课堂练习 2：成果展示准备",
                "type": "reflection",
                "prompt": "用 2 到 3 句话概括本单元最重要的收获，并准备一个适合展示的案例或观点。",
                "tips": [
                    "可以从“我理解了什么”“我最认同什么观点”“我还想继续探究什么”三个问题切入。",
                    "整理完成后，可继续填写自评问卷或发布成果展示帖子。",
                ],
            },
        ],
    }
    return activity_map.get(lesson.order_no, [])


def _application_cards_for_lesson(lesson):
    if lesson.order_no != 2:
        return []
    return [
        {
            "title": "医疗辅助诊断",
            "scenario": "通过医学影像、病例数据和模型分析，辅助医生发现潜在风险。",
            "mapping": "典型价值：提升初筛效率，帮助医生更快定位异常区域。",
        },
        {
            "title": "智能交通",
            "scenario": "通过自动驾驶、智能导航和路况分析优化交通调度与出行体验。",
            "mapping": "典型价值：减少拥堵，提高路线规划效率，增强驾驶辅助能力。",
        },
        {
            "title": "教育与家居",
            "scenario": "在教育中提供个性化学习推荐，在家居中实现语音控制和智能联动。",
            "mapping": "典型价值：让学习更有针对性，让家庭生活更加便捷和智能。",
        },
    ]


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
    lesson_activities = _lesson_activity_blocks(lesson)
    application_cards = _application_cards_for_lesson(lesson)

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
    feedback_url = ""
    feedback_exists = False
    showcase_list_url = ""
    showcase_create_url = ""
    showcase_posts = []
    unit_quiz_url = ""

    if lesson.order_no == 4:
        feedback_url = reverse("analytics:feedback_form", kwargs={"course_slug": course.slug})
        unit_quiz_url = reverse("quiz:take_course_quiz", kwargs={"course_slug": course.slug})
        feedback_exists = request.user.is_authenticated and LearningFeedback.objects.filter(
            user=request.user,
            course=course,
        ).exists()
        showcase_list_url = reverse("forum:showcase_list")
        showcase_create_url = f'{reverse("forum:showcase_create")}?lesson={lesson.id}'
        showcase_posts = list(
            ForumPost.objects.filter(
                category=ForumPostCategory.SHOWCASE,
                status=ForumPostStatus.PUBLISHED,
                lesson__chapter__course=course,
            )
            .select_related("author", "lesson")
            .order_by("-is_pinned", "-created_at", "-id")[:3]
        )

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
            "lesson_activities": lesson_activities,
            "application_cards": application_cards,
            "embedded_video_url": _embed_video_url(lesson.video_url),
            "related_resources": related_resources,
            "teaching_guides": list(guide_qs.order_by("order_no", "id")[:4]),
            "glossary_terms": glossary_terms,
            "feedback_url": feedback_url,
            "feedback_exists": feedback_exists,
            "showcase_list_url": showcase_list_url,
            "showcase_create_url": showcase_create_url,
            "showcase_posts": showcase_posts,
            "unit_quiz_url": unit_quiz_url,
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
