from django import forms

from .models import ForumComment, ForumPost


class ForumPostForm(forms.ModelForm):
    class Meta:
        model = ForumPost
        fields = ["title", "category", "content"]
        labels = {
            "title": "标题",
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
