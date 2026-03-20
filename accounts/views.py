from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse

from courses.models import Course, CourseStatus, LearningProgress, Lesson
from forum.models import ForumPost, ForumPostCategory
from guides.models import TeachingGuide
from practice.models import PracticeRecord
from quiz.models import QuizSubmission, WrongQuestion
from resources.models import Resource

from .models import FavoriteItem, FavoriteTargetType
from .forms import SignUpForm, UserProfileForm


@login_required
def index(request):
    """Account dashboard page."""
    progress_qs = LearningProgress.objects.filter(user=request.user)
    completed_count = progress_qs.filter(completed=True).count()
    in_progress_count = progress_qs.filter(completed=False).count()
    favorite_items = _resolve_favorite_items(request.user)
    note_qs = ForumPost.objects.filter(
        author=request.user,
        category=ForumPostCategory.SHARE,
    ).select_related("lesson")
    submission_qs = QuizSubmission.objects.filter(user=request.user).select_related(
        "lesson",
        "lesson__chapter",
        "lesson__chapter__course",
    )
    wrong_questions = list(
        WrongQuestion.objects.filter(user=request.user, resolved=False)
        .select_related("question", "question__lesson", "question__lesson__chapter", "question__lesson__chapter__course")
        .order_by("-last_wrong_at", "-id")[:6]
    )
    total_available_lessons = Lesson.objects.filter(
        chapter__course__status=CourseStatus.PUBLISHED,
        chapter__is_active=True,
        is_active=True,
    ).count()
    activity_days = set(progress_qs.dates("last_viewed_at", "day"))
    activity_days.update(submission_qs.dates("submitted_at", "day"))
    activity_days.update(PracticeRecord.objects.filter(user=request.user).dates("created_at", "day"))
    activity_days.update(ForumPost.objects.filter(author=request.user).dates("created_at", "day"))
    context = {
        "registered_at": request.user.date_joined,
        "completed_count": completed_count,
        "in_progress_count": in_progress_count,
        "total_available_lessons": total_available_lessons,
        "wrong_question_count": WrongQuestion.objects.filter(user=request.user, resolved=False).count(),
        "favorite_count": FavoriteItem.objects.filter(user=request.user).count(),
        "favorite_items": favorite_items,
        "shared_note_count": note_qs.count(),
        "practice_record_count": PracticeRecord.objects.filter(user=request.user).count(),
        "recent_submissions": list(submission_qs.order_by("-submitted_at", "-id")[:5]),
        "my_notes": list(note_qs.order_by("-created_at", "-id")[:5]),
        "wrong_questions": wrong_questions,
        "activity_days": len(activity_days),
        "community_post_count": ForumPost.objects.filter(author=request.user).count(),
        "answer_count": submission_qs.count(),
    }
    return render(request, "accounts/index.html", context)


def signup(request):
    """User registration page."""
    if request.user.is_authenticated:
        return redirect("accounts:index")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "账户创建成功。")
            return redirect("accounts:index")
    else:
        form = SignUpForm()

    return render(request, "accounts/signup.html", {"form": form})


@login_required
def profile_edit(request):
    """Update profile fields for the current user."""
    profile = request.user.profile

    if request.method == "POST":
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "个人资料已更新。")
            return redirect("accounts:index")
    else:
        form = UserProfileForm(instance=profile)

    return render(request, "accounts/profile_edit.html", {"form": form})


def _resolve_favorite_items(user):
    favorite_items = list(FavoriteItem.objects.filter(user=user))
    if not favorite_items:
        return []

    grouped_ids = {
        FavoriteTargetType.COURSE: [],
        FavoriteTargetType.RESOURCE: [],
        FavoriteTargetType.GUIDE: [],
        FavoriteTargetType.POST: [],
    }
    for item in favorite_items:
        grouped_ids.setdefault(item.target_type, []).append(item.target_id)

    course_map = {obj.id: obj for obj in Course.objects.filter(id__in=grouped_ids[FavoriteTargetType.COURSE])}
    resource_map = {
        obj.id: obj for obj in Resource.objects.filter(id__in=grouped_ids[FavoriteTargetType.RESOURCE])
    }
    guide_map = {
        obj.id: obj for obj in TeachingGuide.objects.filter(id__in=grouped_ids[FavoriteTargetType.GUIDE])
    }
    post_map = {
        obj.id: obj for obj in ForumPost.objects.filter(id__in=grouped_ids[FavoriteTargetType.POST])
    }

    resolved = []
    for item in favorite_items:
        if item.target_type == FavoriteTargetType.COURSE:
            obj = course_map.get(item.target_id)
            url = reverse("courses:course_detail", kwargs={"slug": obj.slug}) if obj else item.url_snapshot
            title = obj.title if obj else item.title_snapshot
        elif item.target_type == FavoriteTargetType.RESOURCE:
            obj = resource_map.get(item.target_id)
            url = reverse("resources:resource_detail", kwargs={"slug": obj.slug}) if obj else item.url_snapshot
            title = obj.title if obj else item.title_snapshot
        elif item.target_type == FavoriteTargetType.POST:
            obj = post_map.get(item.target_id)
            url = reverse("forum:post_detail", kwargs={"post_id": obj.id}) if obj else item.url_snapshot
            title = obj.title if obj else item.title_snapshot
        else:
            obj = guide_map.get(item.target_id)
            url = reverse("guides:guide_detail", kwargs={"guide_id": obj.id}) if obj else item.url_snapshot
            title = obj.title if obj else item.title_snapshot
        resolved.append(
            {
                "target_type": item.get_target_type_display(),
                "title": title,
                "url": url,
                "created_at": item.created_at,
            }
        )
    return resolved


@login_required
def toggle_favorite(request, target_type: str, target_id: int):
    target_type = (target_type or "").strip().lower()
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("accounts:index")

    if target_type == FavoriteTargetType.COURSE:
        target = Course.objects.filter(id=target_id).first()
        url = reverse("courses:course_detail", kwargs={"slug": target.slug}) if target else ""
    elif target_type == FavoriteTargetType.RESOURCE:
        target = Resource.objects.filter(id=target_id).first()
        url = reverse("resources:resource_detail", kwargs={"slug": target.slug}) if target else ""
    elif target_type == FavoriteTargetType.POST:
        target = ForumPost.objects.filter(id=target_id).first()
        url = reverse("forum:post_detail", kwargs={"post_id": target.id}) if target else ""
    elif target_type == FavoriteTargetType.GUIDE:
        target = TeachingGuide.objects.filter(id=target_id).first()
        url = reverse("guides:guide_detail", kwargs={"guide_id": target.id}) if target else ""
    else:
        raise Http404("页面不存在。")

    if target is None:
        raise Http404("页面不存在。")

    favorite, created = FavoriteItem.objects.get_or_create(
        user=request.user,
        target_type=target_type,
        target_id=target_id,
        defaults={
            "title_snapshot": target.title,
            "url_snapshot": url,
        },
    )
    if created:
        messages.success(request, "已加入收藏。")
    else:
        favorite.delete()
        messages.info(request, "已取消收藏。")
    return redirect(next_url)
