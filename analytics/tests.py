from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from courses.models import Chapter, Course, CourseStatus, LearningProgress, Lesson
from forum.models import ForumPost, ForumPostStatus
from quiz.models import Question, QuestionType, QuizSubmission, WrongQuestion


class AnalyticsViewTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="analytics_student", password="Password123!")
        self.staff = User.objects.create_user(username="analytics_staff", password="Password123!", is_staff=True)
        self.another_student = User.objects.create_user(username="analytics_student2", password="Password123!")

        self.course_pub = Course.objects.create(
            title="Published Course",
            status=CourseStatus.PUBLISHED,
            created_by=self.staff,
        )
        self.course_draft = Course.objects.create(
            title="Draft Course",
            status=CourseStatus.DRAFT,
            created_by=self.staff,
        )

        chapter_pub = Chapter.objects.create(course=self.course_pub, title="Chapter 1", order_no=1)
        self.lesson1 = Lesson.objects.create(chapter=chapter_pub, title="Lesson 1", order_no=1)
        self.lesson2 = Lesson.objects.create(chapter=chapter_pub, title="Lesson 2", order_no=2)

        chapter_draft = Chapter.objects.create(course=self.course_draft, title="Chapter D", order_no=1)
        self.lesson_draft = Lesson.objects.create(chapter=chapter_draft, title="Draft Lesson", order_no=1)

        self.q1 = Question.objects.create(
            lesson=self.lesson1,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="Q1",
            options=[{"key": "A", "text": "A"}, {"key": "B", "text": "B"}],
            correct_answer=["A"],
            created_by=self.staff,
        )
        self.q2 = Question.objects.create(
            lesson=self.lesson2,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="Q2",
            options=[{"key": "A", "text": "A"}, {"key": "B", "text": "B"}],
            correct_answer=["B"],
            created_by=self.staff,
        )

        LearningProgress.objects.create(user=self.student, lesson=self.lesson1, completed=True)
        LearningProgress.objects.create(user=self.another_student, lesson=self.lesson2, completed=True)

        QuizSubmission.objects.create(
            user=self.student,
            lesson=self.lesson1,
            total_questions=2,
            correct_count=1,
            total_score=10,
            earned_score=5,
            accuracy=50.0,
        )
        QuizSubmission.objects.create(
            user=self.another_student,
            lesson=self.lesson2,
            total_questions=2,
            correct_count=2,
            total_score=10,
            earned_score=10,
            accuracy=100.0,
        )

        WrongQuestion.objects.create(user=self.student, question=self.q1, wrong_count=2, resolved=False)
        WrongQuestion.objects.create(user=self.student, question=self.q2, wrong_count=1, resolved=True)

        ForumPost.objects.create(
            author=self.student,
            title="Forum P1",
            content="p1",
            status=ForumPostStatus.PUBLISHED,
        )
        ForumPost.objects.create(
            author=self.student,
            title="Forum P2",
            content="p2",
            status=ForumPostStatus.HIDDEN,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("analytics:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_student_dashboard_metrics_are_correct(self):
        self.client.login(username="analytics_student", password="Password123!")
        response = self.client.get(reverse("analytics:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "个人概览")
        self.assertEqual(response.context["mode"], "student")
        self.assertEqual(response.context["total_lessons"], 2)
        self.assertEqual(response.context["completed_lessons"], 1)
        self.assertEqual(response.context["completion_rate"], 50.0)
        self.assertEqual(response.context["submission_count"], 1)
        self.assertEqual(response.context["avg_accuracy"], 50.0)
        self.assertEqual(response.context["open_wrong_count"], 1)
        self.assertEqual(response.context["resolved_wrong_count"], 1)

    def test_staff_dashboard_metrics_are_correct(self):
        self.client.login(username="analytics_staff", password="Password123!")
        response = self.client.get(reverse("analytics:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "平台概览")
        self.assertEqual(response.context["mode"], "staff")
        self.assertEqual(response.context["total_users"], 3)
        self.assertEqual(response.context["total_courses"], 2)
        self.assertEqual(response.context["published_courses"], 1)
        self.assertEqual(response.context["draft_courses"], 1)
        self.assertEqual(response.context["total_lessons"], 3)
        self.assertEqual(response.context["forum_total"], 2)
        self.assertEqual(response.context["submission_count"], 2)

    def test_export_csv_requires_login(self):
        response = self.client.get(reverse("analytics:export_csv"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_student_export_csv(self):
        self.client.login(username="analytics_student", password="Password123!")
        response = self.client.get(reverse("analytics:export_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("analytics_student.csv", response["Content-Disposition"])
        csv_text = response.content.decode()
        self.assertIn("Summary,Total Lessons,2", csv_text)
        self.assertIn("Summary,Completed Lessons,1", csv_text)

    def test_staff_export_csv(self):
        self.client.login(username="analytics_staff", password="Password123!")
        response = self.client.get(reverse("analytics:export_csv"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("analytics_staff.csv", response["Content-Disposition"])
        csv_text = response.content.decode()
        self.assertIn("Users,Total Users,3", csv_text)
        self.assertIn("Courses,Published Courses,1", csv_text)
        self.assertIn("Top Learners", csv_text)
