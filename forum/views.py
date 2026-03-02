from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ForumCommentForm, ForumPostForm
from .models import ForumComment, ForumPost, ForumPostStatus


def _visible_post_queryset(user):
    """Return posts visible to current user."""
    if user.is_authenticated and user.is_staff:
        return ForumPost.objects.exclude(status=ForumPostStatus.DELETED)
    return ForumPost.objects.filter(status=ForumPostStatus.PUBLISHED)


def post_list(request):
    keyword = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()

    posts = _visible_post_queryset(request.user).select_related("author")

    if keyword:
        posts = posts.filter(Q(title__icontains=keyword) | Q(content__icontains=keyword))
    if category:
        posts = posts.filter(category=category)

    paginator = Paginator(posts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "keyword": keyword,
        "category": category,
        "page_obj": page_obj,
    }
    return render(request, "forum/post_list.html", context)


def post_detail(request, post_id: int):
    post = get_object_or_404(
        _visible_post_queryset(request.user).select_related("author"),
        id=post_id,
    )

    ForumPost.objects.filter(id=post.id).update(view_count=F("view_count") + 1)
    post.refresh_from_db()

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
        },
    )


@login_required
def post_create(request):
    if request.method == "POST":
        form = ForumPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.status = ForumPostStatus.PUBLISHED
            post.save()
            messages.success(request, "帖子发布成功。")
            return redirect("forum:post_detail", post_id=post.id)
    else:
        form = ForumPostForm()

    return render(request, "forum/post_form.html", {"form": form})


@login_required
def comment_create(request, post_id: int):
    if request.method != "POST":
        raise Http404("方法不允许。")

    post = get_object_or_404(
        _visible_post_queryset(request.user),
        id=post_id,
    )
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
            {"post": post, "comments": comments, "form": form},
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
    if not (request.user.is_staff or post.author_id == request.user.id):
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
    if not request.user.is_staff:
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
    if not request.user.is_staff:
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
