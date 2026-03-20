from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class PracticeRecordType(models.TextChoices):
    SPEECH = "speech", "语音识别"
    DIALOGUE = "dialogue", "AI 对话"
    IMAGE = "image", "图像识别"


class PracticeRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="practice_records")
    practice_type = models.CharField(max_length=20, choices=PracticeRecordType.choices, db_index=True)
    input_text = models.TextField(blank=True)
    output_text = models.TextField(blank=True)
    image = models.ImageField(upload_to="practice/images/", blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.practice_type}:{self.id}"

# Create your models here.
