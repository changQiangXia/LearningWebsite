from django.core.management import call_command
from django.test import TestCase

from accounts.models import FavoriteItem
from courses.models import Course
from forum.models import ForumPost, ForumPostCategory
from guides.models import TeachingGuide
from practice.models import PracticeRecord
from quiz.models import Question, QuizSubmission
from resources.models import Resource


class SeedDemoDataCommandTests(TestCase):
    def test_seed_demo_data_command_creates_key_records(self):
        call_command("seed_demo_data", skip_search_index=True)

        self.assertTrue(Course.objects.filter(title="走进人工智能").exists())
        self.assertEqual(Question.objects.filter(lesson__chapter__course__title="走进人工智能").count(), 40)
        self.assertTrue(QuizSubmission.objects.filter(user__username="demo_student").exists())
        self.assertTrue(Resource.objects.filter(title="单元知识思维导图").exists())
        self.assertTrue(TeachingGuide.objects.filter(title="走进人工智能——教学指引").exists())
        self.assertTrue(
            ForumPost.objects.filter(title="我的学习总结", category=ForumPostCategory.SHARE).exists()
        )
        self.assertTrue(PracticeRecord.objects.filter(user__username="demo_student").exists())
        self.assertEqual(FavoriteItem.objects.filter(user__username="demo_student").count(), 4)

    def test_seed_demo_data_can_run_twice(self):
        call_command("seed_demo_data", skip_search_index=True)
        call_command("seed_demo_data", skip_search_index=True)

        self.assertEqual(Resource.objects.filter(title="单元知识思维导图").count(), 1)
        self.assertEqual(TeachingGuide.objects.filter(course__title="走进人工智能", order_no=1).count(), 1)
        self.assertEqual(FavoriteItem.objects.filter(user__username="demo_student").count(), 4)
