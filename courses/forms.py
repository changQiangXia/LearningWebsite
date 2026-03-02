from django import forms

from .models import Chapter, Course, Lesson


class ManageCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ("title", "description", "status", "cover_image")
        labels = {
            "title": "课程标题",
            "description": "课程简介",
            "status": "课程状态",
            "cover_image": "封面图片",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "填写课程简介"}),
        }


class ManageChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ("title", "description", "order_no")
        labels = {
            "title": "章节标题",
            "description": "章节简介",
            "order_no": "章节序号",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "填写章节简介"}),
        }


class ManageLessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = (
            "title",
            "content",
            "video_url",
            "attachment_url",
            "order_no",
            "estimated_minutes",
            "is_free_preview",
        )
        labels = {
            "title": "课时标题",
            "content": "课时内容",
            "video_url": "视频链接",
            "attachment_url": "附件链接",
            "order_no": "课时序号",
            "estimated_minutes": "预计学习时长（分钟）",
            "is_free_preview": "允许免费试看",
        }
        widgets = {
            "content": forms.Textarea(attrs={"rows": 8, "placeholder": "填写课时内容"}),
        }
