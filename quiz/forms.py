from django import forms

from .models import Question, QuestionType


class ManageQuestionForm(forms.ModelForm):
    options_text = forms.CharField(
        required=False,
        label="选项文本",
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "A|选项内容\nB|选项内容"}),
        help_text="每行一个选项，格式：键|内容（客观题必填）。",
    )
    correct_answer_text = forms.CharField(
        required=True,
        label="正确答案",
        widget=forms.TextInput(attrs={"placeholder": "A 或 A,B"}),
        help_text="客观题填选项键（逗号分隔），简答题填写可接受答案文本。",
    )

    class Meta:
        model = Question
        fields = (
            "question_type",
            "difficulty",
            "stem",
            "options",
            "correct_answer",
            "score",
            "is_active",
            "explanation",
        )
        labels = {
            "question_type": "题型",
            "difficulty": "难度",
            "stem": "题干",
            "score": "分值",
            "is_active": "是否启用",
            "explanation": "解析",
        }
        widgets = {
            "stem": forms.Textarea(attrs={"rows": 4, "placeholder": "输入题干内容"}),
            "options": forms.HiddenInput(),
            "correct_answer": forms.HiddenInput(),
            "explanation": forms.Textarea(attrs={"rows": 4, "placeholder": "输入题目解析（可选）"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["options"].required = False
        self.fields["correct_answer"].required = False
        if self.instance and self.instance.pk:
            option_lines = []
            for item in self.instance.options:
                if isinstance(item, dict):
                    key = str(item.get("key", "")).strip()
                    text = str(item.get("text", "")).strip()
                    if key and text:
                        option_lines.append(f"{key}|{text}")
            self.fields["options_text"].initial = "\n".join(option_lines)
            self.fields["correct_answer_text"].initial = ", ".join(
                str(item).strip() for item in self.instance.correct_answer if str(item).strip()
            )

    @staticmethod
    def _parse_answers(text):
        return [part.strip() for part in str(text).split(",") if part.strip()]

    @staticmethod
    def _parse_options(text):
        options = []
        seen = set()
        errors = []
        for idx, raw_line in enumerate(str(text).splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue
            if "|" not in line:
                errors.append(f"第 {idx} 行格式错误，应为 键|内容。")
                continue
            key, item_text = line.split("|", 1)
            key = key.strip()
            item_text = item_text.strip()
            if not key or not item_text:
                errors.append(f"第 {idx} 行错误：键和值都不能为空。")
                continue
            if key in seen:
                errors.append(f"第 {idx} 行错误：选项键“{key}”重复。")
                continue
            seen.add(key)
            options.append({"key": key, "text": item_text})
        return options, errors

    def clean(self):
        cleaned = super().clean()
        question_type = cleaned.get("question_type")
        answers = self._parse_answers(cleaned.get("correct_answer_text", ""))
        if not answers:
            self.add_error("correct_answer_text", "至少填写一个答案。")

        objective_types = {
            QuestionType.SINGLE_CHOICE,
            QuestionType.MULTIPLE_CHOICE,
            QuestionType.TRUE_FALSE,
        }

        options = []
        if question_type in objective_types:
            options, option_errors = self._parse_options(cleaned.get("options_text", ""))
            if question_type == QuestionType.TRUE_FALSE and not options and not option_errors:
                options = [{"key": "T", "text": "正确"}, {"key": "F", "text": "错误"}]
            for err in option_errors:
                self.add_error("options_text", err)
            if len(options) < 2:
                self.add_error("options_text", "至少需要两个选项。")

            if question_type in {QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE} and len(answers) != 1:
                self.add_error("correct_answer_text", "单选题和判断题必须且只能有一个答案。")

            option_keys = {item["key"] for item in options}
            missing = [item for item in answers if item not in option_keys]
            if missing:
                self.add_error("correct_answer_text", f"以下答案键在选项中不存在：{missing}")
        elif question_type == QuestionType.SHORT_ANSWER:
            options = []

        cleaned["_parsed_options"] = options
        cleaned["_parsed_answers"] = answers
        cleaned["options"] = options
        cleaned["correct_answer"] = answers
        return cleaned

    def save(self, commit=True, *, user=None, lesson=None):
        instance = super().save(commit=False)
        instance.options = self.cleaned_data.get("_parsed_options", [])
        instance.correct_answer = self.cleaned_data.get("_parsed_answers", [])
        if lesson is not None:
            instance.lesson = lesson
        if user is not None and not instance.created_by_id:
            instance.created_by = user
        if commit:
            instance.save()
        return instance
