from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import SignUpForm, UserProfileForm


@login_required
def index(request):
    """Account dashboard page."""
    return render(request, "accounts/index.html")


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
