from django import forms

from .models import TeachingGuide


class TeachingGuideForm(forms.ModelForm):
    def __init__(self, *args, course_queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        if course_queryset is not None:
            self.fields["course"].queryset = course_queryset

    class Meta:
        model = TeachingGuide
        fields = (
            "course",
            "title",
            "unit_name",
            "objectives",
            "key_points",
            "difficult_points",
            "learning_methods",
            "assignment_suggestion",
            "evaluation_suggestion",
            "order_no",
            "is_published",
        )
        labels = {
            "course": "所属课程",
            "title": "指引标题",
            "unit_name": "单元名称",
            "objectives": "教学目标",
            "key_points": "重点内容",
            "difficult_points": "难点内容",
            "learning_methods": "学习建议",
            "assignment_suggestion": "作业与实践建议",
            "evaluation_suggestion": "评价建议",
            "order_no": "显示顺序",
            "is_published": "公开发布",
        }
        widgets = {
            "objectives": forms.Textarea(attrs={"rows": 4, "placeholder": "填写本单元教学目标"}),
            "key_points": forms.Textarea(attrs={"rows": 4, "placeholder": "填写需要重点掌握的知识点"}),
            "difficult_points": forms.Textarea(attrs={"rows": 4, "placeholder": "填写本单元难点"}),
            "learning_methods": forms.Textarea(attrs={"rows": 4, "placeholder": "填写学习方法建议"}),
            "assignment_suggestion": forms.Textarea(attrs={"rows": 4, "placeholder": "填写课后练习或实践建议"}),
            "evaluation_suggestion": forms.Textarea(attrs={"rows": 4, "placeholder": "填写学习成效评价建议"}),
        }
