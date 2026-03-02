from django.core.management import call_command
from django.test import TestCase

from courses.models import Course
from quiz.models import Question, QuizSubmission


class SeedDemoDataCommandTests(TestCase):
    def test_seed_demo_data_command_creates_key_records(self):
        call_command("seed_demo_data", skip_search_index=True)

        self.assertTrue(Course.objects.filter(title="Python Full Stack 101").exists())
        self.assertTrue(Question.objects.filter(stem__icontains="Django migrations").exists())
        self.assertTrue(QuizSubmission.objects.filter(user__username="demo_student").exists())

    def test_seed_demo_data_can_run_twice(self):
        call_command("seed_demo_data", skip_search_index=True)
        call_command("seed_demo_data", skip_search_index=True)

        self.assertTrue(Course.objects.filter(title="Python Full Stack 101").exists())
