import csv

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from courses.models import Course, CourseStatus, LearningProgress, Lesson
from forum.models import ForumPost, ForumPostStatus
from quiz.models import QuizSubmission, WrongQuestion

from .forms import LearningFeedbackForm
from .models import LearningFeedback


User = get_user_model()


def _visible_courses(user):
    if user.is_staff:
        return Course.objects.all()
    return Course.objects.filter(status=CourseStatus.PUBLISHED)


def _build_student_context(user):
    courses_qs = _visible_courses(user)
    courses = list(courses_qs.order_by("title"))

    total_lessons = Lesson.objects.filter(chapter__course__in=courses_qs).count()
    completed_lessons = LearningProgress.objects.filter(
        user=user,
        completed=True,
        lesson__chapter__course__in=courses_qs,
    ).count()
    completion_rate = round((completed_lessons / total_lessons) * 100, 2) if total_lessons else 0

    submissions_qs = (
        QuizSubmission.objects.filter(user=user)
        .select_related("lesson", "lesson__chapter", "lesson__chapter__course")
        .order_by("-submitted_at")
    )
    submission_count = submissions_qs.count()
    submission_summary = submissions_qs.aggregate(avg_accuracy=Avg("accuracy"))
    avg_accuracy = round(float(submission_summary["avg_accuracy"] or 0), 2)
    recent_submissions = list(submissions_qs[:10])

    open_wrong_count = WrongQuestion.objects.filter(user=user, resolved=False).count()
    resolved_wrong_count = WrongQuestion.objects.filter(user=user, resolved=True).count()
    feedback_qs = LearningFeedback.objects.filter(user=user, course__in=courses_qs).select_related("course")
    feedback_count = feedback_qs.count()
    feedback_completion_rate = round((feedback_count / len(courses)) * 100, 2) if courses else 0
    feedback_summary = feedback_qs.aggregate(
        concept_avg=Avg("concept_score"),
        mechanism_avg=Avg("mechanism_score"),
        ethics_avg=Avg("ethics_score"),
        expression_avg=Avg("expression_score"),
        exploration_avg=Avg("exploration_score"),
    )
    feedback_course_ids = set(feedback_qs.values_list("course_id", flat=True))
    recent_feedback = list(feedback_qs.order_by("-updated_at", "-id")[:3])

    total_by_course = {
        row["chapter__course_id"]: row["total"]
        for row in Lesson.objects.filter(chapter__course__in=courses_qs)
        .values("chapter__course_id")
        .annotate(total=Count("id"))
    }
    completed_by_course = {
        row["lesson__chapter__course_id"]: row["total"]
        for row in LearningProgress.objects.filter(
            user=user,
            completed=True,
            lesson__chapter__course__in=courses_qs,
        )
        .values("lesson__chapter__course_id")
        .annotate(total=Count("id"))
    }

    course_progress_rows = []
    for course in courses:
        total = total_by_course.get(course.id, 0)
        completed = completed_by_course.get(course.id, 0)
        course_progress_rows.append(
            {
                "course": course,
                "total_lessons": total,
                "completed_lessons": completed,
                "completion_rate": round((completed / total) * 100, 2) if total else 0,
            }
        )

    return {
        "mode": "student",
        "total_lessons": total_lessons,
        "completed_lessons": completed_lessons,
        "completion_rate": completion_rate,
        "submission_count": submission_count,
        "avg_accuracy": avg_accuracy,
        "open_wrong_count": open_wrong_count,
        "resolved_wrong_count": resolved_wrong_count,
        "recent_submissions": recent_submissions,
        "course_progress_rows": course_progress_rows,
        "feedback_count": feedback_count,
        "feedback_completion_rate": feedback_completion_rate,
        "feedback_course_ids": feedback_course_ids,
        "feedback_summary": {
            key: round(float(value or 0), 2) for key, value in feedback_summary.items()
        },
        "recent_feedback": recent_feedback,
    }


def _build_staff_context():
    all_courses = Course.objects.all().order_by("title")
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_students = User.objects.filter(is_staff=False).count()

    total_courses = all_courses.count()
    published_courses = all_courses.filter(status=CourseStatus.PUBLISHED).count()
    draft_courses = all_courses.filter(status=CourseStatus.DRAFT).count()
    archived_courses = all_courses.filter(status=CourseStatus.ARCHIVED).count()
    total_lessons = Lesson.objects.count()

    forum_total = ForumPost.objects.count()
    forum_published = ForumPost.objects.filter(status=ForumPostStatus.PUBLISHED).count()
    forum_hidden = ForumPost.objects.filter(status=ForumPostStatus.HIDDEN).count()
    forum_deleted = ForumPost.objects.filter(status=ForumPostStatus.DELETED).count()

    submission_count = QuizSubmission.objects.count()
    avg_accuracy_raw = QuizSubmission.objects.aggregate(avg=Avg("accuracy"))["avg"] or 0
    avg_accuracy = round(float(avg_accuracy_raw), 2)

    open_wrong_count = WrongQuestion.objects.filter(resolved=False).count()
    resolved_wrong_count = WrongQuestion.objects.filter(resolved=True).count()
    feedback_count = LearningFeedback.objects.count()
    feedback_summary = LearningFeedback.objects.aggregate(
        concept_avg=Avg("concept_score"),
        mechanism_avg=Avg("mechanism_score"),
        ethics_avg=Avg("ethics_score"),
        expression_avg=Avg("expression_score"),
        exploration_avg=Avg("exploration_score"),
    )

    completed_lessons_by_user = {
        row["user_id"]: row["completed_lessons"]
        for row in LearningProgress.objects.filter(completed=True)
        .values("user_id")
        .annotate(completed_lessons=Count("id"))
    }
    quiz_stats_by_user = {
        row["user_id"]: row
        for row in QuizSubmission.objects.values("user_id")
        .annotate(submission_count=Count("id"), avg_accuracy=Avg("accuracy"))
    }

    user_ids = set(completed_lessons_by_user.keys()) | set(quiz_stats_by_user.keys())
    user_map = {u.id: u for u in User.objects.filter(id__in=user_ids)}

    learner_rows = []
    for user_id in user_ids:
        user = user_map.get(user_id)
        if not user:
            continue
        quiz_stats = quiz_stats_by_user.get(user_id, {})
        learner_rows.append(
            {
                "user": user,
                "completed_lessons": completed_lessons_by_user.get(user_id, 0),
                "submission_count": quiz_stats.get("submission_count", 0),
                "avg_accuracy": round(float(quiz_stats.get("avg_accuracy") or 0), 2),
            }
        )
    learner_rows.sort(
        key=lambda item: (item["completed_lessons"], item["submission_count"], item["avg_accuracy"]),
        reverse=True,
    )
    learner_rows = learner_rows[:10]

    lesson_total_by_course = {
        row["chapter__course_id"]: row["total"]
        for row in Lesson.objects.values("chapter__course_id").annotate(total=Count("id"))
    }
    completion_total_by_course = {
        row["lesson__chapter__course_id"]: row["total"]
        for row in LearningProgress.objects.filter(completed=True)
        .values("lesson__chapter__course_id")
        .annotate(total=Count("id"))
    }
    learners_by_course = {
        row["lesson__chapter__course_id"]: row["total"]
        for row in LearningProgress.objects.values("lesson__chapter__course_id")
        .annotate(total=Count("user_id", distinct=True))
    }
    course_rows = []
    for course in all_courses:
        total = lesson_total_by_course.get(course.id, 0)
        completed = completion_total_by_course.get(course.id, 0)
        learner_count = learners_by_course.get(course.id, 0)
        course_rows.append(
            {
                "course": course,
                "total_lessons": total,
                "completed_records": completed,
                "learner_count": learner_count,
                "completion_rate": round((completed / total) * 100, 2) if total else 0,
            }
        )

    return {
        "mode": "staff",
        "total_users": total_users,
        "active_users": active_users,
        "total_students": total_students,
        "total_courses": total_courses,
        "published_courses": published_courses,
        "draft_courses": draft_courses,
        "archived_courses": archived_courses,
        "total_lessons": total_lessons,
        "forum_total": forum_total,
        "forum_published": forum_published,
        "forum_hidden": forum_hidden,
        "forum_deleted": forum_deleted,
        "submission_count": submission_count,
        "avg_accuracy": avg_accuracy,
        "open_wrong_count": open_wrong_count,
        "resolved_wrong_count": resolved_wrong_count,
        "feedback_count": feedback_count,
        "feedback_summary": {
            key: round(float(value or 0), 2) for key, value in feedback_summary.items()
        },
        "learner_rows": learner_rows,
        "course_rows": course_rows,
    }


def _write_student_csv(writer, context):
    writer.writerow(["Section", "Metric", "Value"])
    writer.writerow(["Summary", "Total Lessons", context["total_lessons"]])
    writer.writerow(["Summary", "Completed Lessons", context["completed_lessons"]])
    writer.writerow(["Summary", "Completion Rate", f'{context["completion_rate"]}%'])
    writer.writerow(["Summary", "Quiz Submissions", context["submission_count"]])
    writer.writerow(["Summary", "Average Accuracy", f'{context["avg_accuracy"]}%'])
    writer.writerow(["Summary", "Open Wrong Questions", context["open_wrong_count"]])
    writer.writerow(["Summary", "Resolved Wrong Questions", context["resolved_wrong_count"]])
    writer.writerow(["Summary", "Feedback Count", context["feedback_count"]])
    writer.writerow(["Summary", "Feedback Completion Rate", f'{context["feedback_completion_rate"]}%'])
    writer.writerow([])
    writer.writerow(["Course", "Completed", "Total", "Completion Rate"])
    for row in context["course_progress_rows"]:
        writer.writerow(
            [
                row["course"].title,
                row["completed_lessons"],
                row["total_lessons"],
                f'{row["completion_rate"]}%',
            ]
        )


def _write_staff_csv(writer, context):
    writer.writerow(["Section", "Metric", "Value"])
    writer.writerow(["Users", "Total Users", context["total_users"]])
    writer.writerow(["Users", "Active Users", context["active_users"]])
    writer.writerow(["Users", "Total Students", context["total_students"]])
    writer.writerow(["Courses", "Total Courses", context["total_courses"]])
    writer.writerow(["Courses", "Published Courses", context["published_courses"]])
    writer.writerow(["Courses", "Draft Courses", context["draft_courses"]])
    writer.writerow(["Courses", "Archived Courses", context["archived_courses"]])
    writer.writerow(["Courses", "Total Lessons", context["total_lessons"]])
    writer.writerow(["Forum", "Total Posts", context["forum_total"]])
    writer.writerow(["Forum", "Published Posts", context["forum_published"]])
    writer.writerow(["Forum", "Hidden Posts", context["forum_hidden"]])
    writer.writerow(["Forum", "Deleted Posts", context["forum_deleted"]])
    writer.writerow(["Quiz", "Submission Count", context["submission_count"]])
    writer.writerow(["Quiz", "Average Accuracy", f'{context["avg_accuracy"]}%'])
    writer.writerow(["Quiz", "Open Wrong Questions", context["open_wrong_count"]])
    writer.writerow(["Quiz", "Resolved Wrong Questions", context["resolved_wrong_count"]])
    writer.writerow(["Feedback", "Submitted Forms", context["feedback_count"]])
    writer.writerow([])
    writer.writerow(["Top Learners"])
    writer.writerow(["Username", "Completed Lessons", "Quiz Submissions", "Average Accuracy"])
    for row in context["learner_rows"]:
        writer.writerow(
            [
                row["user"].username,
                row["completed_lessons"],
                row["submission_count"],
                f'{row["avg_accuracy"]}%',
            ]
        )
    writer.writerow([])
    writer.writerow(["Course Breakdown"])
    writer.writerow(["Course", "Learners", "Completed Records", "Total Lessons", "Completion Rate"])
    for row in context["course_rows"]:
        writer.writerow(
            [
                row["course"].title,
                row["learner_count"],
                row["completed_records"],
                row["total_lessons"],
                f'{row["completion_rate"]}%',
            ]
        )


@login_required
def index(request):
    if request.user.is_staff:
        context = _build_staff_context()
    else:
        context = _build_student_context(request.user)
    return render(request, "analytics/dashboard.html", context)


@login_required
def export_csv(request):
    filename = "analytics_staff.csv" if request.user.is_staff else "analytics_student.csv"
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)

    if request.user.is_staff:
        context = _build_staff_context()
        _write_staff_csv(writer, context)
    else:
        context = _build_student_context(request.user)
        _write_student_csv(writer, context)

    return response


@login_required
def feedback_form(request, course_slug: str):
    course_qs = _visible_courses(request.user)
    course = get_object_or_404(course_qs, slug=course_slug)
    feedback = LearningFeedback.objects.filter(user=request.user, course=course).first()

    if request.method == "POST":
        form = LearningFeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.course = course
            feedback.save()
            messages.success(request, "????????")
            next_url = request.POST.get("next") or request.GET.get("next") or ""
            if next_url and url_has_allowed_host_and_scheme(
                url=next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)
            return redirect("analytics:index")
    else:
        form = LearningFeedbackForm(instance=feedback)

    return render(
        request,
        "analytics/feedback_form.html",
        {
            "form": form,
            "course": course,
            "feedback": feedback,
            "next": request.GET.get("next", ""),
        },
    )

