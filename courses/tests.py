from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole
from courses.models import AuditTargetType, Chapter, ContentAuditLog, Course, CourseStatus, LearningProgress, Lesson


class CourseModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="teacher", password="Password123!")

    def test_slug_is_generated_and_unique(self):
        course1 = Course.objects.create(title="Python Intro", created_by=self.user)
        course2 = Course.objects.create(title="Python Intro", created_by=self.user)
        self.assertEqual(course1.slug, "python-intro")
        self.assertEqual(course2.slug, "python-intro-1")

    def test_chapter_order_is_unique_in_same_course(self):
        course = Course.objects.create(title="Data Structures", created_by=self.user)
        Chapter.objects.create(course=course, title="Chapter 1", order_no=1)
        with self.assertRaises(IntegrityError):
            Chapter.objects.create(course=course, title="Chapter 1 Copy", order_no=1)

    def test_learning_progress_is_unique_per_user_lesson(self):
        course = Course.objects.create(title="Algorithms", created_by=self.user, status=CourseStatus.PUBLISHED)
        chapter = Chapter.objects.create(course=course, title="Chapter A", order_no=1)
        lesson = Lesson.objects.create(chapter=chapter, title="Lesson A", order_no=1)

        LearningProgress.objects.create(user=self.user, lesson=lesson)
        with self.assertRaises(IntegrityError):
            LearningProgress.objects.create(user=self.user, lesson=lesson)


class CourseViewTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="student1", password="Password123!")
        self.staff = User.objects.create_user(username="staff1", password="Password123!", is_staff=True)

        self.course_published = Course.objects.create(
            title="Public Course",
            status=CourseStatus.PUBLISHED,
            description="Published course description",
            created_by=self.student,
        )
        self.course_draft = Course.objects.create(
            title="Draft Course",
            status=CourseStatus.DRAFT,
            description="Draft course description",
            created_by=self.student,
        )
        chapter = Chapter.objects.create(course=self.course_published, title="Chapter 1", order_no=1)
        self.lesson = Lesson.objects.create(chapter=chapter, title="Lesson 1", order_no=1, content="Lesson content")

    def test_anonymous_list_shows_only_published_courses(self):
        response = self.client.get(reverse("courses:course_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Course")
        self.assertNotContains(response, "Draft Course")

    def test_staff_list_can_see_draft_courses(self):
        self.client.login(username="staff1", password="Password123!")
        response = self.client.get(reverse("courses:course_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Draft Course")

    def test_lesson_detail_updates_view_count_for_authenticated_user(self):
        self.client.login(username="student1", password="Password123!")
        url = reverse("courses:lesson_detail", kwargs={"lesson_id": self.lesson.id})

        response1 = self.client.get(url)
        response2 = self.client.get(url)

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        progress = LearningProgress.objects.get(user=self.student, lesson=self.lesson)
        self.assertEqual(progress.view_count, 2)
        self.assertFalse(progress.completed)

    def test_mark_lesson_complete_requires_login(self):
        url = reverse("courses:mark_lesson_complete", kwargs={"lesson_id": self.lesson.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_mark_lesson_complete_sets_progress_completed(self):
        self.client.login(username="student1", password="Password123!")
        url = reverse("courses:mark_lesson_complete", kwargs={"lesson_id": self.lesson.id})
        response = self.client.post(url, follow=True)

        self.assertEqual(response.status_code, 200)
        progress = LearningProgress.objects.get(user=self.student, lesson=self.lesson)
        self.assertTrue(progress.completed)
        self.assertIsNotNone(progress.completed_at)

    def test_course_detail_shows_completion_summary(self):
        self.client.login(username="student1", password="Password123!")
        self.client.post(reverse("courses:mark_lesson_complete", kwargs={"lesson_id": self.lesson.id}))
        response = self.client.get(reverse("courses:course_detail", kwargs={"slug": self.course_published.slug}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "已完成课时")


class CourseManageViewTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="student_mgr", password="Password123!")
        self.teacher = User.objects.create_user(username="teacher_mgr", password="Password123!")
        self.other_teacher = User.objects.create_user(username="teacher_other_mgr", password="Password123!")
        self.admin_role_user = User.objects.create_user(username="admin_role_mgr", password="Password123!")
        self.staff = User.objects.create_user(username="staff_mgr", password="Password123!", is_staff=True)

        self.teacher.profile.role = UserRole.TEACHER
        self.teacher.profile.save(update_fields=["role"])
        self.other_teacher.profile.role = UserRole.TEACHER
        self.other_teacher.profile.save(update_fields=["role"])
        self.admin_role_user.profile.role = UserRole.ADMIN
        self.admin_role_user.profile.save(update_fields=["role"])

        self.teacher_course = Course.objects.create(
            title="Teacher Course",
            description="Teacher course body",
            status=CourseStatus.DRAFT,
            created_by=self.teacher,
        )
        self.other_course = Course.objects.create(
            title="Other Teacher Course",
            description="Other course body",
            status=CourseStatus.DRAFT,
            created_by=self.other_teacher,
        )
        self.teacher_chapter = Chapter.objects.create(course=self.teacher_course, title="Teacher Chapter", order_no=1)
        self.other_chapter = Chapter.objects.create(course=self.other_course, title="Other Chapter", order_no=1)
        self.teacher_lesson = Lesson.objects.create(
            chapter=self.teacher_chapter,
            title="Teacher Lesson",
            content="Teacher lesson body",
            order_no=1,
            estimated_minutes=12,
        )
        self.other_lesson = Lesson.objects.create(
            chapter=self.other_chapter,
            title="Other Lesson",
            content="Other lesson body",
            order_no=1,
            estimated_minutes=10,
        )

    def test_manage_dashboard_requires_login(self):
        response = self.client.get(reverse("courses:manage_dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_student_cannot_access_manage_dashboard(self):
        self.client.login(username="student_mgr", password="Password123!")
        response = self.client.get(reverse("courses:manage_dashboard"))
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_access_manage_dashboard_and_only_own_courses(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.get(reverse("courses:manage_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Teacher Course")
        self.assertNotContains(response, "Other Teacher Course")

    def test_admin_role_user_can_access_manage_dashboard(self):
        self.client.login(username="admin_role_mgr", password="Password123!")
        response = self.client.get(reverse("courses:manage_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_staff_can_access_manage_dashboard_and_see_all_courses(self):
        self.client.login(username="staff_mgr", password="Password123!")
        response = self.client.get(reverse("courses:manage_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Teacher Course")
        self.assertContains(response, "Other Teacher Course")

    def test_teacher_can_create_course(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_course_create"),
            {
                "title": "New Managed Course",
                "description": "Managed description",
                "status": CourseStatus.PUBLISHED,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        created = Course.objects.get(title="New Managed Course")
        self.assertEqual(created.created_by, self.teacher)
        self.assertEqual(created.status, CourseStatus.PUBLISHED)

    def test_teacher_can_edit_own_course(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_course_edit", kwargs={"course_id": self.teacher_course.id}),
            {
                "title": "Teacher Course Updated",
                "description": "Updated body",
                "status": CourseStatus.DRAFT,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.teacher_course.refresh_from_db()
        self.assertEqual(self.teacher_course.title, "Teacher Course Updated")
        self.assertEqual(self.teacher_course.created_by, self.teacher)

    def test_teacher_cannot_edit_other_users_course(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.get(reverse("courses:manage_course_edit", kwargs={"course_id": self.other_course.id}))
        self.assertEqual(response.status_code, 404)

    def test_toggle_course_status_requires_post(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.get(
            reverse("courses:manage_course_toggle_status", kwargs={"course_id": self.teacher_course.id})
        )
        self.assertEqual(response.status_code, 405)

    def test_teacher_can_toggle_own_course_status(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_course_toggle_status", kwargs={"course_id": self.teacher_course.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.teacher_course.refresh_from_db()
        self.assertEqual(self.teacher_course.status, CourseStatus.PUBLISHED)

    def test_teacher_cannot_toggle_other_users_course_status(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_course_toggle_status", kwargs={"course_id": self.other_course.id}),
        )
        self.assertEqual(response.status_code, 404)
        self.other_course.refresh_from_db()
        self.assertEqual(self.other_course.status, CourseStatus.DRAFT)

    def test_teacher_can_archive_and_restore_course(self):
        self.client.login(username="teacher_mgr", password="Password123!")

        archive_resp = self.client.post(
            reverse("courses:manage_course_toggle_archive", kwargs={"course_id": self.teacher_course.id}),
            follow=True,
        )
        self.assertEqual(archive_resp.status_code, 200)
        self.teacher_course.refresh_from_db()
        self.assertEqual(self.teacher_course.status, CourseStatus.ARCHIVED)

        restore_resp = self.client.post(
            reverse("courses:manage_course_toggle_archive", kwargs={"course_id": self.teacher_course.id}),
            follow=True,
        )
        self.assertEqual(restore_resp.status_code, 200)
        self.teacher_course.refresh_from_db()
        self.assertEqual(self.teacher_course.status, CourseStatus.DRAFT)

    def test_teacher_can_create_chapter_for_owned_course(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_chapter_create", kwargs={"course_id": self.teacher_course.id}),
            {"title": "New Chapter", "description": "Chapter body", "order_no": 2},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Chapter.objects.filter(course=self.teacher_course, title="New Chapter", order_no=2).exists()
        )

    def test_duplicate_chapter_order_shows_form_error_instead_of_server_error(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_chapter_create", kwargs={"course_id": self.teacher_course.id}),
            {"title": "Duplicate Chapter", "description": "Duplicate", "order_no": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Chapter.objects.filter(course=self.teacher_course, order_no=1).count(), 1)

    def test_teacher_cannot_create_chapter_for_other_course(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_chapter_create", kwargs={"course_id": self.other_course.id}),
            {"title": "Invalid Chapter", "order_no": 2},
        )
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_toggle_owned_chapter_active(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_chapter_toggle_active", kwargs={"chapter_id": self.teacher_chapter.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.teacher_chapter.refresh_from_db()
        self.assertFalse(self.teacher_chapter.is_active)

    def test_teacher_can_edit_owned_chapter(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_chapter_edit", kwargs={"chapter_id": self.teacher_chapter.id}),
            {"title": "Teacher Chapter Updated", "description": "Updated chapter", "order_no": 1},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.teacher_chapter.refresh_from_db()
        self.assertEqual(self.teacher_chapter.title, "Teacher Chapter Updated")

    def test_teacher_cannot_edit_other_users_chapter(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.get(reverse("courses:manage_chapter_edit", kwargs={"chapter_id": self.other_chapter.id}))
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_create_lesson_for_owned_chapter(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_lesson_create", kwargs={"chapter_id": self.teacher_chapter.id}),
            {
                "title": "Managed Lesson",
                "content": "Lesson body",
                "video_url": "",
                "attachment_url": "",
                "order_no": 2,
                "estimated_minutes": 15,
                "is_free_preview": True,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Lesson.objects.filter(chapter=self.teacher_chapter, title="Managed Lesson").exists())

    def test_duplicate_lesson_order_shows_form_error_instead_of_server_error(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_lesson_create", kwargs={"chapter_id": self.teacher_chapter.id}),
            {
                "title": "Duplicate Lesson",
                "content": "Duplicate",
                "video_url": "",
                "attachment_url": "",
                "order_no": 1,
                "estimated_minutes": 15,
                "is_free_preview": False,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Lesson.objects.filter(chapter=self.teacher_chapter, order_no=1).count(), 1)

    def test_teacher_cannot_create_lesson_for_other_users_chapter(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_lesson_create", kwargs={"chapter_id": self.other_chapter.id}),
            {
                "title": "Invalid Lesson",
                "content": "Should fail",
                "order_no": 1,
                "estimated_minutes": 10,
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_edit_owned_lesson(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_lesson_edit", kwargs={"lesson_id": self.teacher_lesson.id}),
            {
                "title": "Teacher Lesson Updated",
                "content": "Updated lesson body",
                "video_url": "",
                "attachment_url": "",
                "order_no": 1,
                "estimated_minutes": 18,
                "is_free_preview": True,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.teacher_lesson.refresh_from_db()
        self.assertEqual(self.teacher_lesson.title, "Teacher Lesson Updated")
        self.assertEqual(self.teacher_lesson.estimated_minutes, 18)
        self.assertTrue(self.teacher_lesson.is_free_preview)

    def test_teacher_cannot_edit_other_users_lesson(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.get(reverse("courses:manage_lesson_edit", kwargs={"lesson_id": self.other_lesson.id}))
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_toggle_owned_lesson_active(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        response = self.client.post(
            reverse("courses:manage_lesson_toggle_active", kwargs={"lesson_id": self.teacher_lesson.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.teacher_lesson.refresh_from_db()
        self.assertFalse(self.teacher_lesson.is_active)

    def test_inactive_lesson_not_visible_to_student(self):
        self.teacher_course.status = CourseStatus.PUBLISHED
        self.teacher_course.save(update_fields=["status"])
        self.teacher_lesson.is_active = False
        self.teacher_lesson.save(update_fields=["is_active"])

        self.client.login(username="student_mgr", password="Password123!")
        response = self.client.get(reverse("courses:lesson_detail", kwargs={"lesson_id": self.teacher_lesson.id}))
        self.assertEqual(response.status_code, 404)

    def test_manage_actions_write_audit_logs(self):
        self.client.login(username="teacher_mgr", password="Password123!")
        self.client.post(
            reverse("courses:manage_course_edit", kwargs={"course_id": self.teacher_course.id}),
            {"title": "Teacher Course v2", "description": "Updated", "status": CourseStatus.DRAFT},
            follow=True,
        )
        self.assertTrue(
            ContentAuditLog.objects.filter(
                course=self.teacher_course,
                target_type=AuditTargetType.COURSE,
                action="update",
            ).exists()
        )
