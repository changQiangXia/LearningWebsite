from io import BytesIO
import shutil
import tempfile
from unittest.mock import patch

from PIL import Image

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from courses.models import Chapter, Course, CourseStatus, Lesson
from practice.models import PracticeRecord, PracticeRecordType
from quiz.models import Question, QuestionType


class PracticeViewTests(TestCase):
    def setUp(self):
        self.temp_media = tempfile.mkdtemp()
        self.override = override_settings(MEDIA_ROOT=self.temp_media)
        self.override.enable()

        self.user = User.objects.create_user(username="practice_user", password="Password123!")
        self.course_public = Course.objects.create(
            title="Published Practice Course",
            status=CourseStatus.PUBLISHED,
            created_by=self.user,
        )
        self.course_draft = Course.objects.create(
            title="Draft Practice Course",
            status=CourseStatus.DRAFT,
            created_by=self.user,
        )
        chapter_public = Chapter.objects.create(course=self.course_public, title="Public Chapter", order_no=1)
        chapter_draft = Chapter.objects.create(course=self.course_draft, title="Draft Chapter", order_no=1)
        self.lesson_public = Lesson.objects.create(
            chapter=chapter_public,
            title="Public Lesson",
            order_no=1,
            content="Public lesson content",
        )
        self.lesson_draft = Lesson.objects.create(
            chapter=chapter_draft,
            title="Draft Lesson",
            order_no=1,
            content="Draft lesson content",
        )
        Question.objects.create(
            lesson=self.lesson_public,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="Public question",
            options=[{"key": "A", "text": "One"}, {"key": "B", "text": "Two"}],
            correct_answer=["A"],
            created_by=self.user,
        )
        Question.objects.create(
            lesson=self.lesson_draft,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="Draft question",
            options=[{"key": "A", "text": "One"}, {"key": "B", "text": "Two"}],
            correct_answer=["A"],
            created_by=self.user,
        )

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.temp_media, ignore_errors=True)

    @staticmethod
    def _build_image_upload():
        buffer = BytesIO()
        Image.new("RGB", (120, 80), color=(245, 245, 245)).save(buffer, format="PNG")
        return SimpleUploadedFile("sample.png", buffer.getvalue(), content_type="image/png")

    def test_index_recommends_only_published_course_lessons(self):
        response = self.client.get(reverse("practice:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Lesson")
        self.assertNotContains(response, "Draft Lesson")

    @patch("practice.views.generate_ai_dialogue_reply", return_value="人工智能需要数据、算法和算力协同工作。")
    @patch("practice.views.qwen_is_enabled", return_value=True)
    def test_dialogue_lab_creates_record_for_logged_in_user(self, mocked_enabled, mocked_reply):
        self.client.login(username="practice_user", password="Password123!")
        response = self.client.post(
            reverse("practice:dialogue_lab"),
            {"message": "人工智能为什么需要数据？"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "人工智能需要数据、算法和算力协同工作。")
        record = PracticeRecord.objects.get(user=self.user, practice_type=PracticeRecordType.DIALOGUE)
        self.assertEqual(record.input_text, "人工智能为什么需要数据？")
        self.assertEqual(record.metadata["provider"], "Qwen")
        mocked_enabled.assert_called()
        mocked_reply.assert_called_once()

    def test_speech_lab_saves_transcript_record(self):
        self.client.login(username="practice_user", password="Password123!")
        response = self.client.post(
            reverse("practice:speech_lab"),
            {"transcript": "本系统支持语音识别体验。"},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            PracticeRecord.objects.filter(
                user=self.user,
                practice_type=PracticeRecordType.SPEECH,
                input_text="本系统支持语音识别体验。",
            ).exists()
        )

    @patch("practice.views.analyze_image_with_qwen", return_value="图片主体是一张浅色界面截图。")
    @patch("practice.views.qwen_is_enabled", return_value=True)
    def test_image_lab_analyzes_uploaded_image_and_saves_record(self, mocked_enabled, mocked_qwen):
        self.client.login(username="practice_user", password="Password123!")
        response = self.client.post(
            reverse("practice:image_lab"),
            {"image": self._build_image_upload()},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "识别结果")
        self.assertContains(response, "图片主体是一张浅色界面截图。")
        record = PracticeRecord.objects.get(user=self.user, practice_type=PracticeRecordType.IMAGE)
        self.assertEqual(record.metadata["format"], "PNG")
        self.assertEqual(record.metadata["provider"], "Qwen + 本地分析")
        self.assertIn("AI识别结果：图片主体是一张浅色界面截图。", record.output_text)
        mocked_enabled.assert_called()
        mocked_qwen.assert_called_once()
