from django import forms

from .models import LearningFeedback


SCORE_CHOICES = [(value, f"{value} 分") for value in range(1, 6)]


class LearningFeedbackForm(forms.ModelForm):
    class Meta:
        model = LearningFeedback
        fields = [
            "concept_score",
            "mechanism_score",
            "ethics_score",
            "expression_score",
            "exploration_score",
            "reflection",
        ]
        labels = {
            "concept_score": "对人工智能概念的理解程度",
            "mechanism_score": "对数据、算法、算力关系的理解程度",
            "ethics_score": "对 AI 伦理与风险的认识程度",
            "expression_score": "进行成果展示或课堂表达的自信程度",
            "exploration_score": "继续探索 AI 主题的兴趣程度",
            "reflection": "学习反思",
        }
        widgets = {
            "concept_score": forms.Select(choices=SCORE_CHOICES),
            "mechanism_score": forms.Select(choices=SCORE_CHOICES),
            "ethics_score": forms.Select(choices=SCORE_CHOICES),
            "expression_score": forms.Select(choices=SCORE_CHOICES),
            "exploration_score": forms.Select(choices=SCORE_CHOICES),
            "reflection": forms.Textarea(
                attrs={
                    "placeholder": "可填写本单元最大的收获、仍然困惑的问题，或后续继续学习的计划。",
                }
            ),
        }
