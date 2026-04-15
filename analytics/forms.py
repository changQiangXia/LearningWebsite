from django import forms

from .models import LearningFeedback


MASTERY_CHOICES = [
    ("A", "A. 完全掌握"),
    ("B", "B. 基本掌握"),
    ("C", "C. 不太熟练"),
    ("D", "D. 完全不会"),
]

PRACTICE_CHOICES = [
    ("A", "A. 非常熟练"),
    ("B", "B. 基本会用"),
    ("C", "C. 偶尔困难"),
    ("D", "D. 完全不会"),
]

ABILITY_CHOICES = [
    ("A", "A. 完全能"),
    ("B", "B. 基本能"),
    ("C", "C. 有点难"),
    ("D", "D. 完全不能"),
]

ENGAGEMENT_CHOICES = [
    ("A", "A. 总是"),
    ("B", "B. 经常"),
    ("C", "C. 偶尔"),
    ("D", "D. 很少"),
]

INTEREST_CHOICES = [
    ("A", "A. 非常感兴趣"),
    ("B", "B. 比较感兴趣"),
    ("C", "C. 一般"),
    ("D", "D. 不感兴趣"),
]

LEVEL_CHOICES = [
    ("excellent", "优秀"),
    ("good", "良好"),
    ("pass", "合格"),
    ("improve", "待提高"),
]


class LearningFeedbackForm(forms.ModelForm):
    class Meta:
        model = LearningFeedback
        fields = [
            "student_name",
            "class_name",
            "knowledge_q1",
            "knowledge_q2",
            "knowledge_q3",
            "knowledge_q4",
            "practice_q5",
            "practice_q6",
            "practice_q7",
            "attitude_q8",
            "attitude_q9",
            "attitude_q10",
            "reflection_gain",
            "reflection_gap",
            "reflection_advice",
            "overall_level",
        ]
        labels = {
            "student_name": "姓名",
            "class_name": "班级",
            "knowledge_q1": "1. 我能准确说出人工智能的定义与四大核心特征",
            "knowledge_q2": "2. 我能清晰理解数据、算法、算力三大要素的含义与作用",
            "knowledge_q3": "3. 我能列举 AI 在医疗、交通、教育、金融等领域的典型应用",
            "knowledge_q4": "4. 我了解人工智能带来的伦理问题（就业、隐私、深度伪造等）",
            "practice_q5": "5. 我能顺利完成语音识别、图像识别、AI 对话等实践操作",
            "practice_q6": "6. 我能结合实践，分析 AI 工作时如何用到数据、算法、算力",
            "practice_q7": "7. 我能辨别生活中的 AI 应用，区分 AI 与普通程序",
            "attitude_q8": "8. 我认真完成每节课学习、笔记与在线答题",
            "attitude_q9": "9. 我积极参与社区讨论、发言或回复同学观点",
            "attitude_q10": "10. 我对人工智能学习感兴趣，愿意继续探索",
            "reflection_gain": "11. 本单元我收获最大的知识点是",
            "reflection_gap": "12. 我还不太理解、需要加强的内容是",
            "reflection_advice": "13. 我对 AI 学习的建议",
            "overall_level": "综合等级",
        }
        widgets = {
            "student_name": forms.TextInput(attrs={"placeholder": "可填写真实姓名或学号姓名"}),
            "class_name": forms.TextInput(attrs={"placeholder": "例如：七年级 1 班"}),
            "knowledge_q1": forms.RadioSelect(choices=MASTERY_CHOICES),
            "knowledge_q2": forms.RadioSelect(choices=MASTERY_CHOICES),
            "knowledge_q3": forms.RadioSelect(choices=MASTERY_CHOICES),
            "knowledge_q4": forms.RadioSelect(choices=MASTERY_CHOICES),
            "practice_q5": forms.RadioSelect(choices=PRACTICE_CHOICES),
            "practice_q6": forms.RadioSelect(choices=ABILITY_CHOICES),
            "practice_q7": forms.RadioSelect(choices=ABILITY_CHOICES),
            "attitude_q8": forms.RadioSelect(choices=ENGAGEMENT_CHOICES),
            "attitude_q9": forms.RadioSelect(choices=ENGAGEMENT_CHOICES),
            "attitude_q10": forms.RadioSelect(choices=INTEREST_CHOICES),
            "reflection_gain": forms.Textarea(attrs={"rows": 3, "placeholder": "例如：更清楚地理解了人工智能四大特征。"}),
            "reflection_gap": forms.Textarea(attrs={"rows": 3, "placeholder": "例如：还需要继续理解数据、算法、算力的关系。"}),
            "reflection_advice": forms.Textarea(attrs={"rows": 3, "placeholder": "例如：希望增加更多生活案例或课堂演示。"}),
            "overall_level": forms.RadioSelect(choices=LEVEL_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in [
            "knowledge_q1",
            "knowledge_q2",
            "knowledge_q3",
            "knowledge_q4",
            "practice_q5",
            "practice_q6",
            "practice_q7",
            "attitude_q8",
            "attitude_q9",
            "attitude_q10",
            "overall_level",
        ]:
            self.fields[field_name].required = True
