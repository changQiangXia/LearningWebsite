from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserRole
from courses.models import Course

from .forms import TeachingGuideForm
from .models import TeachingGuide


def _is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role in {UserRole.TEACHER, UserRole.ADMIN})


def _visible_guides(user):
    if not user.is_authenticated:
        return TeachingGuide.objects.filter(is_published=True)
    if user.is_staff:
        return TeachingGuide.objects.all()
    if _is_manager(user):
        return TeachingGuide.objects.filter(Q(is_published=True) | Q(created_by=user))
    return TeachingGuide.objects.filter(is_published=True)


def _managed_guides(user):
    if user.is_staff:
        return TeachingGuide.objects.all()
    return TeachingGuide.objects.filter(created_by=user)


def _managed_courses(user):
    queryset = Course.objects.order_by("title", "id")
    if user.is_staff:
        return queryset
    return queryset.filter(created_by=user)


def guide_list(request):
    guides = _visible_guides(request.user).select_related("course", "created_by").distinct()
    keyword = request.GET.get("q", "").strip()
    if keyword:
        guides = guides.filter(
            Q(title__icontains=keyword)
            | Q(unit_name__icontains=keyword)
            | Q(objectives__icontains=keyword)
            | Q(key_points__icontains=keyword)
        )
    return render(
        request,
        "guides/guide_list.html",
        {
            "guides": guides.order_by("course_id", "order_no", "id"),
            "keyword": keyword,
            "can_manage_guides": _is_manager(request.user),
        },
    )


def guide_detail(request, guide_id: int):
    guide = get_object_or_404(_visible_guides(request.user).select_related("course", "created_by"), id=guide_id)
    return render(
        request,
        "guides/guide_detail.html",
        {
            "guide": guide,
            "can_manage_guide": _is_manager(request.user)
            and (request.user.is_staff or guide.created_by_id == request.user.id),
        },
    )


@login_required
def manage_guide_list(request):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")
    guides = _managed_guides(request.user).select_related("course").order_by("course_id", "order_no", "id")
    return render(request, "guides/manage_guide_list.html", {"guides": guides})


@login_required
def manage_guide_create(request):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")
    course_queryset = _managed_courses(request.user)
    if request.method == "POST":
        form = TeachingGuideForm(request.POST, course_queryset=course_queryset)
        if form.is_valid():
            guide = form.save(commit=False)
            guide.created_by = request.user
            guide.save()
            messages.success(request, "教学指引创建成功。")
            return redirect("guides:guide_detail", guide_id=guide.id)
    else:
        initial = {}
        course_id = request.GET.get("course", "").strip()
        if course_id.isdigit() and course_queryset.filter(id=int(course_id)).exists():
            initial["course"] = int(course_id)
        form = TeachingGuideForm(initial=initial, course_queryset=course_queryset)
    return render(request, "guides/manage_guide_form.html", {"form": form, "mode": "create"})


@login_required
def manage_guide_edit(request, guide_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")
    guide = get_object_or_404(_managed_guides(request.user), id=guide_id)
    course_queryset = _managed_courses(request.user)
    if request.method == "POST":
        form = TeachingGuideForm(request.POST, instance=guide, course_queryset=course_queryset)
        if form.is_valid():
            form.save()
            messages.success(request, "教学指引更新成功。")
            return redirect("guides:guide_detail", guide_id=guide.id)
    else:
        form = TeachingGuideForm(instance=guide, course_queryset=course_queryset)
    return render(
        request,
        "guides/manage_guide_form.html",
        {"form": form, "guide": guide, "mode": "edit"},
    )


@login_required
def manage_guide_toggle_publish(request, guide_id: int):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _is_manager(request.user):
        raise Http404("页面不存在。")
    guide = get_object_or_404(_managed_guides(request.user), id=guide_id)
    guide.is_published = not guide.is_published
    guide.save(update_fields=["is_published", "updated_at"])
    state_label = "公开" if guide.is_published else "隐藏"
    messages.success(request, f"教学指引当前状态：{state_label}。")
    return redirect("guides:manage_guide_list")

# Create your views here.
