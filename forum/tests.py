from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from forum.models import ForumComment, ForumPost, ForumPostCategory, ForumPostStatus


class ForumModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="forum_user", password="Password123!")
        self.post1 = ForumPost.objects.create(author=self.user, title="Post 1", content="Body 1")
        self.post2 = ForumPost.objects.create(author=self.user, title="Post 2", content="Body 2")

    def test_post_defaults(self):
        self.assertEqual(self.post1.category, ForumPostCategory.DISCUSSION)
        self.assertEqual(self.post1.status, ForumPostStatus.PUBLISHED)
        self.assertFalse(self.post1.is_pinned)
        self.assertFalse(self.post1.is_solved)

    def test_comment_parent_must_belong_to_same_post(self):
        parent = ForumComment.objects.create(post=self.post1, author=self.user, content="Parent")
        invalid = ForumComment(post=self.post2, author=self.user, parent=parent, content="Invalid child")
        with self.assertRaises(ValidationError):
            invalid.save()

    def test_comment_updates_post_last_activity(self):
        old_time = timezone.now() - timedelta(days=1)
        self.post1.last_activity_at = old_time
        self.post1.save(update_fields=["last_activity_at"])

        ForumComment.objects.create(post=self.post1, author=self.user, content="New reply")
        self.post1.refresh_from_db()

        self.assertGreater(self.post1.last_activity_at, old_time)


class ForumViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="forum_u1", password="Password123!")
        self.staff = User.objects.create_user(username="forum_staff", password="Password123!", is_staff=True)
        self.other = User.objects.create_user(username="forum_other", password="Password123!")
        self.post = ForumPost.objects.create(author=self.user, title="Need Help", content="Can someone help?")

    def test_post_create_requires_login(self):
        response = self.client.get(reverse("forum:post_create"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_logged_in_user_can_create_post(self):
        self.client.login(username="forum_u1", password="Password123!")
        response = self.client.post(
            reverse("forum:post_create"),
            {"title": "My Question", "category": ForumPostCategory.HELP, "content": "Detail text"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ForumPost.objects.filter(title="My Question").exists())

    def test_logged_in_user_can_create_note(self):
        self.client.login(username="forum_u1", password="Password123!")
        response = self.client.post(
            reverse("forum:note_create"),
            {"title": "My Note", "content": "Key learning points."},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            ForumPost.objects.filter(title="My Note", category=ForumPostCategory.SHARE, author=self.user).exists()
        )

    def test_note_list_shows_only_share_posts(self):
        ForumPost.objects.create(
            author=self.user,
            title="Shared Note",
            content="Shared content",
            category=ForumPostCategory.SHARE,
        )
        ForumPost.objects.create(
            author=self.user,
            title="Discussion Post",
            content="Discussion content",
            category=ForumPostCategory.DISCUSSION,
        )

        response = self.client.get(reverse("forum:note_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Shared Note")
        self.assertNotContains(response, "Discussion Post")

    def test_logged_in_user_can_comment_post(self):
        self.client.login(username="forum_u1", password="Password123!")
        response = self.client.post(
            reverse("forum:comment_create", kwargs={"post_id": self.post.id}),
            {"content": "First reply"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ForumComment.objects.filter(post=self.post, content="First reply").exists())

    def test_author_can_toggle_solved(self):
        self.client.login(username="forum_u1", password="Password123!")
        response = self.client.post(reverse("forum:toggle_solved", kwargs={"post_id": self.post.id}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_solved)

    def test_non_author_non_staff_cannot_toggle_solved(self):
        self.client.login(username="forum_other", password="Password123!")
        response = self.client.post(reverse("forum:toggle_solved", kwargs={"post_id": self.post.id}))
        self.assertEqual(response.status_code, 404)
        self.post.refresh_from_db()
        self.assertFalse(self.post.is_solved)

    def test_staff_can_toggle_pin_and_change_status(self):
        self.client.login(username="forum_staff", password="Password123!")
        pin_resp = self.client.post(reverse("forum:toggle_pin", kwargs={"post_id": self.post.id}), follow=True)
        self.assertEqual(pin_resp.status_code, 200)

        status_resp = self.client.post(
            reverse("forum:change_status", kwargs={"post_id": self.post.id}),
            {"status": ForumPostStatus.HIDDEN},
            follow=True,
        )
        self.assertEqual(status_resp.status_code, 200)
        self.post.refresh_from_db()
        self.assertTrue(self.post.is_pinned)
        self.assertEqual(self.post.status, ForumPostStatus.HIDDEN)

    def test_non_staff_cannot_change_status(self):
        self.client.login(username="forum_u1", password="Password123!")
        response = self.client.post(
            reverse("forum:change_status", kwargs={"post_id": self.post.id}),
            {"status": ForumPostStatus.HIDDEN},
        )
        self.assertEqual(response.status_code, 404)
