from django import forms


class DialogueForm(forms.Form):
    message = forms.CharField(
        label="问题或对话内容",
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "例如：人工智能为什么需要数据？语音识别和图像识别有什么区别？",
            }
        ),
    )


class SpeechTranscriptForm(forms.Form):
    transcript = forms.CharField(
        label="识别文本",
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": "点击“开始识别”后，这里会显示语音转写结果，也可以手动输入。",
            }
        ),
    )


class ImageRecognitionForm(forms.Form):
    image = forms.ImageField(label="上传图片")
