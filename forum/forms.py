from django import forms

from .models import ForumComment, ForumPost


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ["title", "lesson", "category", "content"]
        labels = {
            "title": "标题",
            "lesson": "关联课时",
            "category": "分类",
            "content": "正文",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "请输入帖子标题"}),
            "content": forms.Textarea(attrs={"placeholder": "请描述问题或观点"}),
        }


class ForumCommentForm(forms.ModelForm):
    parent_id = forms.IntegerField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ForumComment
        fields = ["content"]
        labels = {
            "content": "评论内容",
        }
        widgets = {
            "content": forms.Textarea(attrs={"placeholder": "输入评论内容"}),
        }


class NoteShareForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ["title", "lesson", "content"]
        labels = {
            "title": "笔记标题",
            "lesson": "关联课时",
            "content": "笔记内容",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "请输入学习笔记标题"}),
            "content": forms.Textarea(attrs={"placeholder": "整理学习收获、关键知识点或答题经验"}),
        }


class ShowcaseShareForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ["title", "lesson", "content"]
        labels = {
            "title": "展示标题",
            "lesson": "关联课时",
            "content": "展示说明",
        }
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "请输入成果展示标题"}),
            "content": forms.Textarea(
                attrs={"placeholder": "可填写展示摘要、核心观点、案例分析或作品说明"}
            ),
        }
