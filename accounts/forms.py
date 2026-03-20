from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile, UserRole


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, max_length=254)
    role = forms.ChoiceField(
        choices=(
            (UserRole.STUDENT, "学生"),
            (UserRole.TEACHER, "教师"),
        ),
        initial=UserRole.STUDENT,
        label="注册角色",
        required=False,
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("该邮箱已被使用。")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            profile = user.profile
            profile.role = self.cleaned_data.get("role") or UserRole.STUDENT
            profile.save(update_fields=["role"])
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ("school", "major", "grade", "bio", "avatar")
        labels = {
            "school": "学校",
            "major": "专业",
            "grade": "年级",
            "bio": "个人简介",
            "avatar": "头像",
        }
        widgets = {
            "bio": forms.Textarea(attrs={"rows": 5, "placeholder": "简要介绍个人学习方向或背景"}),
        }
