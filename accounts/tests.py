from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import FavoriteItem, UserRole
from courses.models import Chapter, Course, CourseStatus, LearningProgress, Lesson
from forum.models import ForumPost, ForumPostCategory
from guides.models import TeachingGuide
from practice.models import PracticeRecord, PracticeRecordType
from quiz.models import Question, QuestionType, WrongQuestion
from resources.models import Resource, ResourceType


class UserProfileSignalTests(TestCase):
    def test_profile_created_when_user_is_created(self):
        user = User.objects.create_user(username="alice", password="Password123!")
        self.assertTrue(hasattr(user, "profile"))
        self.assertEqual(user.profile.role, UserRole.STUDENT)


class AccountViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="acc_user",
            email="acc@example.com",
            password="Password123!",
        )

    def _create_dashboard_data(self):
        course = Course.objects.create(
            title="Python Project Demo",
            description="Course for dashboard testing.",
            status=CourseStatus.PUBLISHED,
            created_by=self.user,
        )
        chapter = Chapter.objects.create(course=course, title="Chapter 1", order_no=1)
        lesson_completed = Lesson.objects.create(chapter=chapter, title="Lesson Done", order_no=1, content="Done")
        lesson_in_progress = Lesson.objects.create(
            chapter=chapter,
            title="Lesson Doing",
            order_no=2,
            content="Doing",
        )
        question = Question.objects.create(
            lesson=lesson_completed,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="Which command starts the Django dev server?",
            options=[{"key": "A", "text": "python manage.py runserver"}, {"key": "B", "text": "python app.py"}],
            correct_answer=["A"],
            created_by=self.user,
        )
        LearningProgress.objects.create(user=self.user, lesson=lesson_completed, view_count=2, completed=True)
        LearningProgress.objects.create(user=self.user, lesson=lesson_in_progress, view_count=1, completed=False)
        WrongQuestion.objects.create(user=self.user, question=question, wrong_count=1, resolved=False)
        ForumPost.objects.create(
            author=self.user,
            title="Study Note",
            category=ForumPostCategory.SHARE,
            content="Organize key points before taking the quiz.",
        )
        PracticeRecord.objects.create(
            user=self.user,
            practice_type=PracticeRecordType.DIALOGUE,
            input_text="How do I organize a defense demo?",
            output_text="Start with module overview, then live demo.",
        )
        Resource.objects.create(
            title="Django Slide Deck",
            description="Course slides.",
            resource_type=ResourceType.COURSEWARE,
            course=course,
            external_url="https://example.com/slides",
            tags="django, slides",
            created_by=self.user,
        )
        TeachingGuide.objects.create(
            course=course,
            title="Teaching Guide",
            unit_name="Unit 1",
            objectives="Understand app structure.",
            key_points="Routing and templates.",
            order_no=1,
            created_by=self.user,
        )
        return course

    def test_signup_creates_user_and_logs_in(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "new_user",
                "email": "new_user@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username="new_user").exists())
        self.assertContains(response, "账户中心")

    def test_signup_rejects_duplicate_email(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "username": "other_user",
                "email": "acc@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "该邮箱已被使用。")
        self.assertFalse(User.objects.filter(username="other_user").exists())

    def test_authenticated_user_redirected_from_signup(self):
        self.client.login(username="acc_user", password="Password123!")
        response = self.client.get(reverse("accounts:signup"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:index"))

    def test_account_center_requires_login(self):
        response = self.client.get(reverse("accounts:index"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_profile_edit_updates_profile_fields(self):
        self.client.login(username="acc_user", password="Password123!")
        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "school": "Example University",
                "major": "Computer Science",
                "grade": "2026",
                "bio": "Interested in web development.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.school, "Example University")
        self.assertEqual(self.user.profile.major, "Computer Science")
        self.assertEqual(self.user.profile.grade, "2026")
        self.assertEqual(self.user.profile.bio, "Interested in web development.")

    def test_toggle_favorite_adds_and_removes_item(self):
        course = Course.objects.create(
            title="Favorite Course",
            status=CourseStatus.PUBLISHED,
            created_by=self.user,
        )
        self.client.login(username="acc_user", password="Password123!")

        response = self.client.post(
            reverse("accounts:toggle_favorite", kwargs={"target_type": "course", "target_id": course.id}),
            {"next": reverse("accounts:index")},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            FavoriteItem.objects.filter(user=self.user, target_type="course", target_id=course.id).exists()
        )

        response = self.client.post(
            reverse("accounts:toggle_favorite", kwargs={"target_type": "course", "target_id": course.id}),
            {"next": reverse("accounts:index")},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            FavoriteItem.objects.filter(user=self.user, target_type="course", target_id=course.id).exists()
        )

    def test_account_center_shows_summary_and_favorites(self):
        course = self._create_dashboard_data()
        self.client.login(username="acc_user", password="Password123!")
        self.client.post(
            reverse("accounts:toggle_favorite", kwargs={"target_type": "course", "target_id": course.id}),
            {"next": reverse("accounts:index")},
            follow=True,
        )

        response = self.client.get(reverse("accounts:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["completed_count"], 1)
        self.assertEqual(response.context["in_progress_count"], 1)
        self.assertEqual(response.context["wrong_question_count"], 1)
        self.assertEqual(response.context["favorite_count"], 1)
        self.assertEqual(response.context["shared_note_count"], 1)
        self.assertEqual(response.context["practice_record_count"], 1)
        self.assertContains(response, "Python Project Demo")
        self.assertContains(response, "公开笔记")
