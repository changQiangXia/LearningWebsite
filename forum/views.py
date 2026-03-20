from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import FavoriteItem, FavoriteTargetType, UserRole
from courses.models import CourseStatus, Lesson

from .forms import ForumCommentForm, ForumPostForm, NoteShareForm
from .models import ForumComment, ForumPost, ForumPostCategory, ForumPostLike, ForumPostStatus


def _is_moderator(user):
    if not user.is_authenticated:
        return False
    if user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role in {UserRole.TEACHER, UserRole.ADMIN})


def _lesson_queryset():
    return Lesson.objects.select_related("chapter", "chapter__course").filter(
        chapter__course__status=CourseStatus.PUBLISHED,
        chapter__is_active=True,
        is_active=True,
    ).order_by("chapter__course__title", "chapter__order_no", "order_no", "id")


def _topic_prompts():
    prompts = {}
    for lesson in _lesson_queryset():
        if lesson.order_no == 1:
            prompts[lesson.id] = "示例话题：分享一个身边的 AI 应用，描述它如何影响日常学习或生活。"
        elif lesson.order_no == 2:
            prompts[lesson.id] = "示例话题：AI 对话和人与人对话有什么不同？从数据、算法或体验角度谈看法。"
        elif lesson.order_no == 3:
            prompts[lesson.id] = "示例话题：AI 会取代哪些工作？哪些能力仍然需要人来完成？"
        else:
            prompts[lesson.id] = "示例话题：总结本单元最有启发的一个观点，并给出个人反思。"
    return prompts


def _visible_post_queryset(user):
    queryset = ForumPost.objects.select_related("author", "lesson", "lesson__chapter", "lesson__chapter__course").annotate(
        comment_total=Count("comments", filter=Q(comments__is_deleted=False), distinct=True),
        like_total=Count("likes", distinct=True),
    )
    if _is_moderator(user):
        return queryset.exclude(status=ForumPostStatus.DELETED)
    return queryset.filter(status=ForumPostStatus.PUBLISHED)


def _prepare_post_form(form):
    form.fields["lesson"].queryset = _lesson_queryset()
    form.fields["lesson"].required = False
    return form


def _list_context_base():
    return {
        "lesson_options": list(_lesson_queryset()),
    }


def post_list(request):
    keyword = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    lesson_id = request.GET.get("lesson", "").strip()
    order_by = request.GET.get("order", "latest").strip().lower() or "latest"

    posts = _visible_post_queryset(request.user)

    if keyword:
        posts = posts.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))
    if category:
        posts = posts.filter(category=category)
    if lesson_id.isdigit():
        posts = posts.filter(lesson_id=int(lesson_id))

    if order_by == "hot":
        posts = posts.order_by("-is_pinned", "-like_total", "-view_count", "-comment_total", "-last_activity_at", "-id")
    else:
        order_by = "latest"
        posts = posts.order_by("-is_pinned", "-created_at", "-id")

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "keyword": keyword,
        "category": category,
        "lesson_id": lesson_id,
        "order_by": order_by,
        "page_obj": page_obj,
        **_list_context_base(),
    }
    return render(request, "forum/post_list.html", context)


def note_list(request):
    keyword = request.GET.get("q", "").strip()
    lesson_id = request.GET.get("lesson", "").strip()
    order_by = request.GET.get("order", "latest").strip().lower() or "latest"
    notes = _visible_post_queryset(request.user).filter(category=ForumPostCategory.SHARE)
    if keyword:
        notes = notes.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))
    if lesson_id.isdigit():
        notes = notes.filter(lesson_id=int(lesson_id))

    if order_by == "hot":
        notes = notes.order_by("-is_pinned", "-like_total", "-view_count", "-comment_total", "-last_activity_at", "-id")
    else:
        order_by = "latest"
        notes = notes.order_by("-is_pinned", "-created_at", "-id")

    paginator = Paginator(notes, 10)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "forum/note_list.html",
        {
            "keyword": keyword,
            "lesson_id": lesson_id,
            "order_by": order_by,
            "page_obj": page_obj,
            **_list_context_base(),
        },
    )


def post_detail(request, post_id: int):
    post = get_object_or_404(_visible_post_queryset(request.user), id=post_id)

    ForumPost.objects.filter(id=post.id).update(view_count=F("view_count") + 1)
    post.view_count += 1

    comments = (
        ForumComment.objects.filter(post=post, is_deleted=False)
        .select_related("author", "parent")
        .order_by("created_at", "id")
    )

    form = ForumCommentForm()
    parent_from_query = request.GET.get("reply_to", "").strip()
    if parent_from_query.isdigit():
        form.fields["parent_id"].initial = int(parent_from_query)

    return render(
        request,
        "forum/post_detail.html",
        {
            "post": post,
            "comments": comments,
            "form": form,
            "can_moderate": _is_moderator(request.user),
            "can_toggle_solved": request.user.is_authenticated
            and (_is_moderator(request.user) or request.user.id == post.author_id),
            "is_liked": request.user.is_authenticated
            and ForumPostLike.objects.filter(post=post, user=request.user).exists(),
            "is_favorited": request.user.is_authenticated
            and FavoriteItem.objects.filter(
                user=request.user,
                target_type=FavoriteTargetType.POST,
                target_id=post.id,
            ).exists(),
        },
    )


@login_required
def post_create(request):
    if request.method == "POST":
        form = _prepare_post_form(ForumPostForm(request.POST))
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.status = ForumPostStatus.PUBLISHED
            post.save()
            messages.success(request, "帖子发布成功。")
            return redirect("forum:post_detail", post_id=post.id)
    else:
        form = _prepare_post_form(ForumPostForm(initial={"lesson": request.GET.get("lesson")}))

    return render(
        request,
        "forum/post_form.html",
        {"form": form, "topic_prompts": _topic_prompts(), "lessons": list(_lesson_queryset())},
    )


@login_required
def note_create(request):
    if request.method == "POST":
        form = _prepare_post_form(NoteShareForm(request.POST))
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.category = ForumPostCategory.SHARE
            post.status = ForumPostStatus.PUBLISHED
            post.save()
            messages.success(request, "笔记已发布。")
            return redirect("forum:post_detail", post_id=post.id)
    else:
        form = _prepare_post_form(NoteShareForm(initial={"lesson": request.GET.get("lesson")}))

    return render(
        request,
        "forum/note_form.html",
        {"form": form, "topic_prompts": _topic_prompts(), "lessons": list(_lesson_queryset())},
    )


@login_required
def comment_create(request, post_id: int):
    if request.method != "POST":
        raise Http404("方法不允许。")

    post = get_object_or_404(_visible_post_queryset(request.user), id=post_id)
    form = ForumCommentForm(request.POST)

    if not form.is_valid():
        comments = (
            ForumComment.objects.filter(post=post, is_deleted=False)
            .select_related("author", "parent")
            .order_by("created_at", "id")
        )
        return render(
            request,
            "forum/post_detail.html",
            {
                "post": post,
                "comments": comments,
                "form": form,
                "can_moderate": _is_moderator(request.user),
                "can_toggle_solved": _is_moderator(request.user) or request.user.id == post.author_id,
                "is_liked": ForumPostLike.objects.filter(post=post, user=request.user).exists(),
                "is_favorited": FavoriteItem.objects.filter(
                    user=request.user,
                    target_type=FavoriteTargetType.POST,
                    target_id=post.id,
                ).exists(),
            },
            status=400,
        )

    parent = None
    parent_id = form.cleaned_data.get("parent_id")
    if parent_id:
        parent = get_object_or_404(ForumComment, id=parent_id, post=post, is_deleted=False)

    comment = form.save(commit=False)
    comment.post = post
    comment.author = request.user
    comment.parent = parent
    comment.save()

    messages.success(request, "评论已发布。")
    return redirect("forum:post_detail", post_id=post.id)


@login_required
def toggle_solved(request, post_id: int):
    if request.method != "POST":
        raise Http404("方法不允许。")

    post = get_object_or_404(ForumPost, id=post_id)
    if not (_is_moderator(request.user) or post.author_id == request.user.id):
        raise Http404("帖子不存在。")

    post.is_solved = not post.is_solved
    post.save(update_fields=["is_solved", "updated_at"])
    if post.is_solved:
        messages.success(request, "帖子已标记为已解决。")
    else:
        messages.info(request, "帖子已标记为未解决。")
    return redirect("forum:post_detail", post_id=post.id)


@login_required
def toggle_pin(request, post_id: int):
    if request.method != "POST":
        raise Http404("方法不允许。")
    if not _is_moderator(request.user):
        raise Http404("帖子不存在。")

    post = get_object_or_404(ForumPost, id=post_id)
    post.is_pinned = not post.is_pinned
    post.save(update_fields=["is_pinned", "updated_at"])
    if post.is_pinned:
        messages.success(request, "帖子已置顶。")
    else:
        messages.info(request, "帖子已取消置顶。")
    return redirect("forum:post_detail", post_id=post.id)


@login_required
def change_status(request, post_id: int):
    if request.method != "POST":
        raise Http404("方法不允许。")
    if not _is_moderator(request.user):
        raise Http404("帖子不存在。")

    post = get_object_or_404(ForumPost, id=post_id)
    new_status = (request.POST.get("status") or "").strip().lower()
    valid_status = {choice for choice, _ in ForumPostStatus.choices}
    if new_status not in valid_status:
        messages.error(request, "状态值无效。")
        return redirect("forum:post_detail", post_id=post.id)

    post.status = new_status
    post.save(update_fields=["status", "updated_at"])
    messages.success(request, f"帖子状态已更新为：{post.get_status_display()}。")
    return redirect("forum:post_detail", post_id=post.id)


@login_required
def toggle_like(request, post_id: int):
    if request.method != "POST":
        raise Http404("方法不允许。")

    post = get_object_or_404(_visible_post_queryset(request.user), id=post_id)
    like, created = ForumPostLike.objects.get_or_create(post=post, user=request.user)
    if created:
        messages.success(request, "已点赞该帖子。")
    else:
        like.delete()
        messages.info(request, "已取消点赞。")
    return redirect("forum:post_detail", post_id=post.id)
