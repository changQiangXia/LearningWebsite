from django import forms


class DialogueForm(forms.Form):
    message = forms.CharField(
        label="问题或对话内容",
        widget=forms.Textarea(attrs={"rows": 4, "placeholder": "例如：如何规划一门 AI 入门课程？"}),
    )


class SpeechTranscriptForm(forms.Form):
    transcript = forms.CharField(
        label="识别文本",
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "点击开始识别后，这里会显示语音转写结果"}),
    )


class ImageRecognitionForm(forms.Form):
    image = forms.ImageField(label="上传图片")
