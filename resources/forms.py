from django import forms

from .models import Resource, ResourceAudience


class ResourceForm(forms.ModelForm):
    def __init__(self, *args, course_queryset=None, lesson_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course_queryset is not None:
            self.fields["course"].queryset = course_queryset
        if lesson_queryset is not None:
            self.fields["lesson"].queryset = lesson_queryset
        self.fields["audience"].initial = self.instance.audience or ResourceAudience.ALL
        self.fields["sort_order"].initial = self.instance.sort_order or 1
        self.fields["audience"].required = False
        self.fields["sort_order"].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("audience"):
            cleaned_data["audience"] = ResourceAudience.ALL
        if not cleaned_data.get("sort_order"):
            cleaned_data["sort_order"] = 1
        return cleaned_data

    class Meta:
        model = Resource
        fields = (
            "title",
            "description",
            "resource_type",
            "course",
            "lesson",
            "file",
            "external_url",
            "cover_image",
            "tags",
            "audience",
            "sort_order",
            "is_published",
        )
        labels = {
            "title": "资源标题",
            "description": "资源简介",
            "resource_type": "资源类型",
            "course": "关联课程",
            "lesson": "对应课时",
            "file": "上传文件",
            "external_url": "外部链接",
            "cover_image": "封面图片",
            "tags": "关键词标签",
            "audience": "资源受众",
            "sort_order": "排序序号",
            "is_published": "公开发布",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "填写资源用途、内容简介与适用场景"}),
            "tags": forms.TextInput(attrs={"placeholder": "例如：AI 入门, 机器学习, 提示词"}),
        }
