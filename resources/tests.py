from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole
from courses.models import Course, CourseStatus
from resources.models import Resource, ResourceType


def promote_teacher(user):
    user.profile.role = UserRole.TEACHER
    user.profile.save(update_fields=["role"])


class ResourceModelTests(TestCase):
    def test_resource_requires_file_or_external_url(self):
        resource = Resource(title="No Access", resource_type=ResourceType.READING)
        with self.assertRaises(ValidationError):
            resource.full_clean()


class ResourceViewTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username="resource_teacher", password="Password123!")
        self.other_teacher = User.objects.create_user(username="resource_other", password="Password123!")
        promote_teacher(self.teacher)
        promote_teacher(self.other_teacher)
        self.owned_course = Course.objects.create(
            title="Owned Course",
            status=CourseStatus.PUBLISHED,
            created_by=self.teacher,
        )
        self.other_course = Course.objects.create(
            title="Other Course",
            status=CourseStatus.PUBLISHED,
            created_by=self.other_teacher,
        )
        Resource.objects.create(
            title="Public Resource",
            description="Visible to everyone.",
            resource_type=ResourceType.READING,
            course=self.owned_course,
            external_url="https://example.com/public",
            created_by=self.teacher,
            is_published=True,
        )
        Resource.objects.create(
            title="Hidden Resource",
            description="Visible only to owner.",
            resource_type=ResourceType.TOOL,
            course=self.owned_course,
            external_url="https://example.com/hidden",
            created_by=self.teacher,
            is_published=False,
        )

    def test_anonymous_list_shows_only_published_resources(self):
        response = self.client.get(reverse("resources:resource_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Resource")
        self.assertNotContains(response, "Hidden Resource")

    def test_owner_can_view_unpublished_resource_in_list(self):
        self.client.login(username="resource_teacher", password="Password123!")
        response = self.client.get(reverse("resources:resource_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Resource")
        self.assertContains(response, "Hidden Resource")

    def test_manage_resource_form_only_allows_owned_courses(self):
        self.client.login(username="resource_teacher", password="Password123!")
        response = self.client.get(reverse("resources:manage_resource_create"))
        course_queryset = response.context["form"].fields["course"].queryset

        self.assertIn(self.owned_course, course_queryset)
        self.assertNotIn(self.other_course, course_queryset)

        response = self.client.post(
            reverse("resources:manage_resource_create"),
            {
                "title": "Invalid Resource",
                "description": "Should fail because the course is not owned.",
                "resource_type": ResourceType.COURSEWARE,
                "course": self.other_course.id,
                "external_url": "https://example.com/invalid",
                "tags": "invalid",
                "is_published": True,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Resource.objects.filter(title="Invalid Resource").exists())

    def test_teacher_can_create_resource_for_owned_course(self):
        self.client.login(username="resource_teacher", password="Password123!")
        response = self.client.post(
            reverse("resources:manage_resource_create"),
            {
                "title": "New Owned Resource",
                "description": "Created by the resource owner.",
                "resource_type": ResourceType.VIDEO,
                "course": self.owned_course.id,
                "external_url": "https://example.com/video",
                "tags": "demo",
                "is_published": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Resource.objects.filter(title="New Owned Resource", created_by=self.teacher, course=self.owned_course).exists()
        )
