from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserRole
from courses.audit import log_content_action
from courses.models import AuditTargetType, Course, CourseStatus, Lesson

from .forms import ManageQuestionForm
from .models import Question, QuestionType, QuizAnswer, QuizSubmission, WrongQuestion


def _is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role in {UserRole.TEACHER, UserRole.ADMIN})


def _visible_lessons(user):
    if user.is_authenticated and user.is_staff:
        return Lesson.objects.select_related("chapter", "chapter__course")
    return Lesson.objects.select_related("chapter", "chapter__course").filter(
        chapter__course__status=CourseStatus.PUBLISHED,
        chapter__is_active=True,
        is_active=True,
    )


def _visible_courses(user):
    queryset = Course.objects.all()
    if user.is_authenticated and user.is_staff:
        return queryset
    return queryset.filter(status=CourseStatus.PUBLISHED)


def _managed_lessons(user):
    qs = Lesson.objects.select_related("chapter", "chapter__course", "chapter__course__created_by")
    if user.is_staff:
        return qs
    if _is_manager(user):
        return qs.filter(chapter__course__created_by=user)
    return qs.none()


def _managed_questions(user):
    qs = Question.objects.select_related("lesson", "lesson__chapter", "lesson__chapter__course")
    if user.is_staff:
        return qs
    if _is_manager(user):
        return qs.filter(lesson__chapter__course__created_by=user)
    return qs.none()


def index(request):
    lessons = (
        _visible_lessons(request.user)
        .filter(questions__is_active=True)
        .distinct()
        .order_by("chapter__course_id", "chapter__order_no", "order_no")
    )
    courses = (
        _visible_courses(request.user)
        .filter(chapters__lessons__questions__is_active=True)
        .distinct()
        .order_by("title", "id")
    )
    course_quiz_rows = []
    for course in courses:
        question_total = Question.objects.filter(
            lesson__chapter__course=course,
            lesson__chapter__is_active=True,
            lesson__is_active=True,
            is_active=True,
        ).count()
        if not question_total:
            continue
        course_quiz_rows.append(
            {
                "course": course,
                "question_total": min(question_total, 10),
            }
        )
    return render(
        request,
        "quiz/index.html",
        {
            "lessons": lessons,
            "course_quiz_rows": course_quiz_rows,
        },
    )


def _normalize_answer_list(values):
    return sorted({str(item).strip().lower() for item in values if str(item).strip()})


def _extract_user_answer(question, post_data):
    key = f"q_{question.id}"
    if question.question_type == QuestionType.MULTIPLE_CHOICE:
        return post_data.getlist(key)
    if question.question_type == QuestionType.SHORT_ANSWER:
        return [post_data.get(f"{key}_text", "")]
    return [post_data.get(key, "")]


def _evaluate_submission(questions, post_data):
    """Evaluate question list against submitted form payload."""
    result_rows = []
    total_score = 0
    user_score = 0

    for question in questions:
        total_score += question.score
        expected = _normalize_answer_list(question.correct_answer)
        user_answer = _normalize_answer_list(_extract_user_answer(question, post_data))
        is_correct = user_answer == expected
        if is_correct:
            user_score += question.score

        result_rows.append(
            {
                "question": question,
                "user_answer": user_answer,
                "expected": expected,
                "is_correct": is_correct,
            }
        )

    correct_count = sum(1 for row in result_rows if row["is_correct"])
    accuracy = round((correct_count / len(result_rows)) * 100, 2)
    return result_rows, total_score, user_score, correct_count, accuracy


def _persist_submission(user, lesson, result_rows, total_score, user_score, correct_count, accuracy):
    """Persist one submission, per-question records, and wrong-question updates."""
    with transaction.atomic():
        submission = QuizSubmission.objects.create(
            user=user,
            lesson=lesson,
            total_questions=len(result_rows),
            correct_count=correct_count,
            total_score=total_score,
            earned_score=user_score,
            accuracy=accuracy,
        )

        for row in result_rows:
            question = row["question"]
            QuizAnswer.objects.create(
                submission=submission,
                question=question,
                user_answer=row["user_answer"],
                expected_answer=row["expected"],
                is_correct=row["is_correct"],
                score_awarded=question.score if row["is_correct"] else 0,
                explanation_snapshot=question.explanation,
            )

            if row["is_correct"]:
                WrongQuestion.objects.filter(user=user, question=question).update(resolved=True)
            else:
                wrong_item, created = WrongQuestion.objects.get_or_create(
                    user=user,
                    question=question,
                    defaults={"wrong_count": 1, "resolved": False},
                )
                if not created:
                    wrong_item.wrong_count += 1
                    wrong_item.resolved = False
                    wrong_item.save(update_fields=["wrong_count", "resolved", "last_wrong_at"])

    return submission


@login_required
def take_lesson_quiz(request, lesson_id: int):
    lesson = get_object_or_404(_visible_lessons(request.user), id=lesson_id)
    questions = list(
        Question.objects.filter(lesson=lesson, is_active=True)
        .order_by("id")
    )

    if not questions:
        raise Http404("该课时暂无可用题目。")

    if request.method == "POST":
        result_rows, total_score, user_score, correct_count, accuracy = _evaluate_submission(
            questions, request.POST
        )
        submission = _persist_submission(
            request.user,
            lesson,
            result_rows,
            total_score,
            user_score,
            correct_count,
            accuracy,
        )

        return render(
            request,
            "quiz/result.html",
            {
                "submission": submission,
                "quiz_mode": "lesson",
                "lesson": lesson,
                "result_rows": result_rows,
                "correct_count": correct_count,
                "question_count": len(result_rows),
                "user_score": user_score,
                "total_score": total_score,
                "accuracy": accuracy,
            },
        )

    return render(
        request,
        "quiz/take_quiz.html",
        {
            "page_title": f"课时测验：{lesson.title}",
            "page_hint": f"课程：{lesson.chapter.course.title} / 章节：{lesson.chapter.title}",
            "submit_text": "提交测验",
            "lesson": lesson,
            "questions": questions,
            "question_type": QuestionType,
        },
    )


@login_required
def take_course_quiz(request, course_slug: str):
    course = get_object_or_404(_visible_courses(request.user), slug=course_slug)
    questions = list(
        Question.objects.filter(
            lesson__chapter__course=course,
            lesson__chapter__is_active=True,
            lesson__is_active=True,
            lesson__order_no=4,
            is_active=True,
        )
        .select_related("lesson", "lesson__chapter")
        .order_by("id")[:10]
    )
    if not questions:
        questions = list(
            Question.objects.filter(
                lesson__chapter__course=course,
                lesson__chapter__is_active=True,
                lesson__is_active=True,
                is_active=True,
            )
            .select_related("lesson", "lesson__chapter")
            .order_by("lesson__chapter__order_no", "lesson__order_no", "id")[:10]
        )

    if not questions:
        raise Http404("当前课程暂无可用题目。")

    anchor_lesson = questions[-1].lesson

    if request.method == "POST":
        result_rows, total_score, user_score, correct_count, accuracy = _evaluate_submission(
            questions, request.POST
        )
        submission = _persist_submission(
            request.user,
            anchor_lesson,
            result_rows,
            total_score,
            user_score,
            correct_count,
            accuracy,
        )

        return render(
            request,
            "quiz/result.html",
            {
                "submission": submission,
                "quiz_mode": "course_unit",
                "lesson": anchor_lesson,
                "result_title": f"单元综合测验：{course.title}",
                "result_rows": result_rows,
                "correct_count": correct_count,
                "question_count": len(result_rows),
                "user_score": user_score,
                "total_score": total_score,
                "accuracy": accuracy,
            },
        )

    return render(
        request,
        "quiz/take_quiz.html",
        {
            "page_title": f"单元综合测验：{course.title}",
            "page_hint": f"共 {len(questions)} 题，覆盖课程概念、应用、伦理与总结内容。",
            "submit_text": "提交综合测验",
            "course": course,
            "questions": questions,
            "question_type": QuestionType,
        },
    )


@login_required
def retry_wrong_questions(request, lesson_id: int):
    lesson = get_object_or_404(_visible_lessons(request.user), id=lesson_id)
    wrong_items = list(
        WrongQuestion.objects.filter(
            user=request.user,
            question__lesson=lesson,
            question__is_active=True,
            resolved=False,
        )
        .select_related("question")
        .order_by("-last_wrong_at", "question_id")
    )
    questions = [item.question for item in wrong_items]

    if not questions:
        raise Http404("该课时暂无未解决错题。")

    if request.method == "POST":
        result_rows, total_score, user_score, correct_count, accuracy = _evaluate_submission(
            questions, request.POST
        )
        submission = _persist_submission(
            request.user,
            lesson,
            result_rows,
            total_score,
            user_score,
            correct_count,
            accuracy,
        )
        return render(
            request,
            "quiz/result.html",
            {
                "submission": submission,
                "quiz_mode": "wrong_retry",
                "lesson": lesson,
                "result_rows": result_rows,
                "correct_count": correct_count,
                "question_count": len(result_rows),
                "user_score": user_score,
                "total_score": total_score,
                "accuracy": accuracy,
            },
        )

    return render(
        request,
        "quiz/take_quiz.html",
        {
            "page_title": f"错题重练：{lesson.title}",
            "page_hint": "本次仅包含仍未解决的错题。",
            "submit_text": "提交重练",
            "lesson": lesson,
            "questions": questions,
            "question_type": QuestionType,
        },
    )


@login_required
def manage_question_list(request, lesson_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    lesson = get_object_or_404(_managed_lessons(request.user), id=lesson_id)
    questions = list(Question.objects.filter(lesson=lesson).order_by("id"))
    return render(
        request,
        "quiz/manage_question_list.html",
        {
            "lesson": lesson,
            "questions": questions,
        },
    )


@login_required
def manage_question_create(request, lesson_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    lesson = get_object_or_404(_managed_lessons(request.user), id=lesson_id)
    if request.method == "POST":
        form = ManageQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(user=request.user, lesson=lesson)
            log_content_action(
                actor=request.user,
                target_type=AuditTargetType.QUESTION,
                target_id=question.id,
                action="create",
                message=f"为课时《{lesson.title}》创建题目 #{question.id}。",
                course=lesson.chapter.course,
                chapter=lesson.chapter,
                lesson=lesson,
                payload={"question_type": question.question_type, "is_active": question.is_active},
            )
            messages.success(request, "题目创建成功。")
            return redirect("quiz:manage_question_edit", question_id=question.id)
    else:
        form = ManageQuestionForm()
    return render(
        request,
        "quiz/manage_question_form.html",
        {
            "form": form,
            "lesson": lesson,
            "mode": "create",
        },
    )


@login_required
def manage_question_edit(request, question_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    question = get_object_or_404(_managed_questions(request.user), id=question_id)
    lesson = question.lesson
    if request.method == "POST":
        form = ManageQuestionForm(request.POST, instance=question)
        if form.is_valid():
            question = form.save()
            log_content_action(
                actor=request.user,
                target_type=AuditTargetType.QUESTION,
                target_id=question.id,
                action="update",
                message=f"更新题目 #{question.id}。",
                course=lesson.chapter.course,
                chapter=lesson.chapter,
                lesson=lesson,
                payload={"question_type": question.question_type, "is_active": question.is_active},
            )
            messages.success(request, "题目更新成功。")
            return redirect("quiz:manage_question_edit", question_id=question.id)
    else:
        form = ManageQuestionForm(instance=question)
    return render(
        request,
        "quiz/manage_question_form.html",
        {
            "form": form,
            "lesson": lesson,
            "question": question,
            "mode": "edit",
        },
    )


@login_required
def manage_question_toggle_active(request, question_id: int):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _is_manager(request.user):
        raise Http404("页面不存在。")

    question = get_object_or_404(_managed_questions(request.user), id=question_id)
    question.is_active = not question.is_active
    question.save(update_fields=["is_active", "updated_at"])
    state_label = "启用" if question.is_active else "停用"
    log_content_action(
        actor=request.user,
        target_type=AuditTargetType.QUESTION,
        target_id=question.id,
        action="toggle_active",
        message=f"题目 #{question.id} 状态调整为“{state_label}”。",
        course=question.lesson.chapter.course,
        chapter=question.lesson.chapter,
        lesson=question.lesson,
        payload={"is_active": question.is_active},
    )
    messages.success(request, f"题目当前状态：{state_label}。")
    return redirect("quiz:manage_question_list", lesson_id=question.lesson_id)


@login_required
def submission_history(request):
    submissions = (
        QuizSubmission.objects.filter(user=request.user)
        .select_related("lesson", "lesson__chapter", "lesson__chapter__course")
        .order_by("-submitted_at")
    )
    paginator = Paginator(submissions, 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "quiz/history.html", {"page_obj": page_obj})


@login_required
def wrong_question_list(request):
    status = request.GET.get("status", "open").strip().lower()
    wrong_questions = WrongQuestion.objects.filter(user=request.user).select_related(
        "question", "question__lesson", "question__lesson__chapter", "question__lesson__chapter__course"
    )
    if status == "resolved":
        wrong_questions = wrong_questions.filter(resolved=True)
    elif status == "all":
        pass
    else:
        status = "open"
        wrong_questions = wrong_questions.filter(resolved=False)

    paginator = Paginator(wrong_questions.order_by("-last_wrong_at"), 20)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "quiz/wrong_questions.html",
        {
            "status": status,
            "page_obj": page_obj,
        },
    )
