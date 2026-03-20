from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserRole
from courses.models import Course, Lesson

from .forms import ResourceForm
from .models import Resource, ResourceAudience


def _is_manager(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role in {UserRole.TEACHER, UserRole.ADMIN})


def _visible_resources(user):
    queryset = Resource.objects.select_related("course", "lesson", "lesson__chapter", "created_by")
    public_filter = Q(is_published=True, audience=ResourceAudience.ALL)
    teacher_filter = Q(is_published=True, audience=ResourceAudience.TEACHER)
    if not user.is_authenticated:
        return queryset.filter(public_filter)
    if user.is_staff:
        return queryset
    if _is_manager(user):
        return queryset.filter(public_filter | teacher_filter | Q(created_by=user))
    return queryset.filter(public_filter)


def _managed_resources(user):
    queryset = Resource.objects.select_related("course", "lesson", "lesson__chapter").all()
    if user.is_staff:
        return queryset
    return queryset.filter(created_by=user)


def _managed_courses(user):
    queryset = Course.objects.order_by("title", "id")
    if user.is_staff:
        return queryset
    return queryset.filter(created_by=user)


def _managed_lessons(user):
    queryset = Lesson.objects.select_related("chapter", "chapter__course").order_by(
        "chapter__course__title",
        "chapter__order_no",
        "order_no",
        "id",
    )
    if user.is_staff:
        return queryset
    return queryset.filter(chapter__course__created_by=user)


def _group_resources(resources):
    groups = OrderedDict()
    for resource in resources:
        lesson = resource.lesson
        if lesson:
            key = (
                lesson.chapter.course.title,
                lesson.chapter.order_no,
                lesson.order_no,
                lesson.id,
            )
            label = f"第 {lesson.order_no} 课时：{lesson.title}"
        else:
            course_title = resource.course.title if resource.course_id else "综合资源"
            course_order = resource.course_id or 999999
            key = (course_title, 9999, 9999, resource.course_id or 0)
            label = f"{course_title} · 综合资源"

        if key not in groups:
            groups[key] = {"label": label, "resources": []}
        groups[key]["resources"].append(resource)
    return list(groups.values())


def resource_list(request):
    base_resources = _visible_resources(request.user).distinct()
    resources = base_resources
    keyword = request.GET.get("q", "").strip()
    resource_type = request.GET.get("type", "").strip()
    course_id = request.GET.get("course", "").strip()
    lesson_id = request.GET.get("lesson", "").strip()

    if keyword:
        resources = resources.filter(
            Q(title__icontains=keyword) | Q(description__icontains=keyword) | Q(tags__icontains=keyword)
        )
    if resource_type:
        resources = resources.filter(resource_type=resource_type)
    if course_id.isdigit():
        resources = resources.filter(course_id=int(course_id))
    if lesson_id.isdigit():
        resources = resources.filter(lesson_id=int(lesson_id))

    ordered_resources = list(
        resources.order_by(
            "course__title",
            "lesson__chapter__order_no",
            "lesson__order_no",
            "sort_order",
            "-updated_at",
            "-id",
        )
    )
    lesson_options = list(
        Lesson.objects.filter(id__in=base_resources.exclude(lesson_id=None).values_list("lesson_id", flat=True))
        .select_related("chapter", "chapter__course")
        .order_by("chapter__course__title", "chapter__order_no", "order_no", "id")
    )
    course_options = list(
        Course.objects.filter(id__in=base_resources.exclude(course_id=None).values_list("course_id", flat=True))
        .order_by("title", "id")
    )

    return render(
        request,
        "resources/resource_list.html",
        {
            "resources": ordered_resources,
            "resource_groups": _group_resources(ordered_resources),
            "keyword": keyword,
            "resource_type": resource_type,
            "course_id": course_id,
            "lesson_id": lesson_id,
            "course_options": course_options,
            "lesson_options": lesson_options,
            "can_manage_resources": _is_manager(request.user),
        },
    )


def resource_detail(request, slug: str):
    resource = get_object_or_404(_visible_resources(request.user), slug=slug)
    return render(
        request,
        "resources/resource_detail.html",
        {
            "resource": resource,
            "can_manage_resource": _is_manager(request.user)
            and (request.user.is_staff or resource.created_by_id == request.user.id),
        },
    )


@login_required
def teacher_resource_list(request):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")
    resources = list(
        _visible_resources(request.user)
        .filter(audience=ResourceAudience.TEACHER, is_published=True)
        .order_by("course__title", "lesson__chapter__order_no", "lesson__order_no", "sort_order", "-updated_at", "-id")
    )
    return render(
        request,
        "resources/teacher_resource_list.html",
        {
            "resources": resources,
            "resource_groups": _group_resources(resources),
        },
    )


@login_required
def manage_resource_list(request):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")
    resources = _managed_resources(request.user).order_by(
        "course__title",
        "lesson__chapter__order_no",
        "lesson__order_no",
        "sort_order",
        "-updated_at",
        "-id",
    )
    return render(request, "resources/manage_resource_list.html", {"resources": resources})


@login_required
def manage_resource_create(request):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")
    course_queryset = _managed_courses(request.user)
    lesson_queryset = _managed_lessons(request.user)
    if request.method == "POST":
        form = ResourceForm(
            request.POST,
            request.FILES,
            course_queryset=course_queryset,
            lesson_queryset=lesson_queryset,
        )
        if form.is_valid():
            resource = form.save(commit=False)
            resource.created_by = request.user
            resource.save()
            messages.success(request, "资源创建成功。")
            return redirect("resources:resource_detail", slug=resource.slug)
    else:
        initial = {}
        course_id = request.GET.get("course", "").strip()
        lesson_id = request.GET.get("lesson", "").strip()
        if course_id.isdigit() and course_queryset.filter(id=int(course_id)).exists():
            initial["course"] = int(course_id)
        if lesson_id.isdigit() and lesson_queryset.filter(id=int(lesson_id)).exists():
            initial["lesson"] = int(lesson_id)
        form = ResourceForm(initial=initial, course_queryset=course_queryset, lesson_queryset=lesson_queryset)
    return render(
        request,
        "resources/manage_resource_form.html",
        {"form": form, "mode": "create"},
    )


@login_required
def manage_resource_edit(request, resource_id: int):
    if not _is_manager(request.user):
        raise Http404("页面不存在。")
    resource = get_object_or_404(_managed_resources(request.user), id=resource_id)
    course_queryset = _managed_courses(request.user)
    lesson_queryset = _managed_lessons(request.user)
    if request.method == "POST":
        form = ResourceForm(
            request.POST,
            request.FILES,
            instance=resource,
            course_queryset=course_queryset,
            lesson_queryset=lesson_queryset,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "资源更新成功。")
            return redirect("resources:resource_detail", slug=resource.slug)
    else:
        form = ResourceForm(instance=resource, course_queryset=course_queryset, lesson_queryset=lesson_queryset)
    return render(
        request,
        "resources/manage_resource_form.html",
        {"form": form, "resource": resource, "mode": "edit"},
    )


@login_required
def manage_resource_toggle_publish(request, resource_id: int):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    if not _is_manager(request.user):
        raise Http404("页面不存在。")
    resource = get_object_or_404(_managed_resources(request.user), id=resource_id)
    resource.is_published = not resource.is_published
    resource.save(update_fields=["is_published", "updated_at"])
    state_label = "公开" if resource.is_published else "隐藏"
    messages.success(request, f"资源当前状态：{state_label}。")
    return redirect("resources:manage_resource_list")

# Create your views here.
