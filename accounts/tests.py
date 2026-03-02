from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole


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
