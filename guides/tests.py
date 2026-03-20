from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole
from courses.models import Course, CourseStatus
from guides.models import TeachingGuide


def promote_teacher(user):
    user.profile.role = UserRole.TEACHER
    user.profile.save(update_fields=["role"])


class GuideViewTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="guide_teacher", password="Password123!")
        self.other_teacher = User.objects.create_user(username="guide_other", password="Password123!")
        promote_teacher(self.teacher)
        promote_teacher(self.other_teacher)
        self.owned_course = Course.objects.create(
            title="Guide Owned Course",
            status=CourseStatus.PUBLISHED,
            created_by=self.teacher,
        )
        self.other_course = Course.objects.create(
            title="Guide Other Course",
            status=CourseStatus.PUBLISHED,
            created_by=self.other_teacher,
        )
        TeachingGuide.objects.create(
            course=self.owned_course,
            title="Public Guide",
            unit_name="Unit 1",
            objectives="介绍语音识别的基础流程。",
            key_points="麦克风采集与文本转写。",
            order_no=1,
            created_by=self.teacher,
            is_published=True,
        )
        TeachingGuide.objects.create(
            course=self.owned_course,
            title="Hidden Guide",
            unit_name="Unit 2",
            objectives="仅教师可见。",
            key_points="内部备课说明。",
            order_no=2,
            created_by=self.teacher,
            is_published=False,
        )

    def test_anonymous_list_shows_only_published_guides(self):
        response = self.client.get(reverse("guides:guide_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Guide")
        self.assertNotContains(response, "Hidden Guide")

    def test_owner_can_view_unpublished_guide_in_list(self):
        self.client.login(username="guide_teacher", password="Password123!")
        response = self.client.get(reverse("guides:guide_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Guide")
        self.assertContains(response, "Hidden Guide")

    def test_keyword_search_matches_objectives_and_key_points(self):
        response = self.client.get(reverse("guides:guide_list"), {"q": "语音识别"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Guide")
        self.assertNotContains(response, "Hidden Guide")

    def test_manage_guide_form_only_allows_owned_courses(self):
        self.client.login(username="guide_teacher", password="Password123!")
        response = self.client.get(reverse("guides:manage_guide_create"))
        course_queryset = response.context["form"].fields["course"].queryset

        self.assertIn(self.owned_course, course_queryset)
        self.assertNotIn(self.other_course, course_queryset)

        response = self.client.post(
            reverse("guides:manage_guide_create"),
            {
                "course": self.other_course.id,
                "title": "Invalid Guide",
                "unit_name": "Unit X",
                "objectives": "Should not be allowed.",
                "key_points": "Foreign course.",
                "difficult_points": "",
                "learning_methods": "",
                "assignment_suggestion": "",
                "order_no": 1,
                "is_published": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TeachingGuide.objects.filter(title="Invalid Guide").exists())

    def test_teacher_can_create_guide_for_owned_course(self):
        self.client.login(username="guide_teacher", password="Password123!")
        response = self.client.post(
            reverse("guides:manage_guide_create"),
            {
                "course": self.owned_course.id,
                "title": "New Guide",
                "unit_name": "Unit 3",
                "objectives": "Explain resource integration.",
                "key_points": "Tags and course mapping.",
                "difficult_points": "Data organization.",
                "learning_methods": "Combine reading and practice.",
                "assignment_suggestion": "Upload one reading resource.",
                "order_no": 3,
                "is_published": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            TeachingGuide.objects.filter(title="New Guide", created_by=self.teacher, course=self.owned_course).exists()
        )
