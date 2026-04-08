from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from accounts.models import UserRole
from courses.models import AuditTargetType, Chapter, ContentAuditLog, Course, CourseStatus, Lesson
from quiz.models import Question, QuestionType, QuizAnswer, QuizSubmission, WrongQuestion


class QuestionModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quiz_user", password="Password123!")
        self.course = Course.objects.create(title="Math", created_by=self.user)
        self.chapter = Chapter.objects.create(course=self.course, title="Basics", order_no=1)
        self.lesson = Lesson.objects.create(chapter=self.chapter, title="Integers", order_no=1)

    def test_single_choice_requires_answer_key_in_options(self):
        question = Question(
            lesson=self.lesson,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="1+1=?",
            options=[{"key": "A", "text": "1"}, {"key": "B", "text": "2"}],
            correct_answer=["C"],
            created_by=self.user,
        )
        with self.assertRaises(ValidationError):
            question.save()

    def test_valid_single_choice_question_can_be_saved(self):
        question = Question.objects.create(
            lesson=self.lesson,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="2+2=?",
            options=[{"key": "A", "text": "3"}, {"key": "B", "text": "4"}],
            correct_answer=["B"],
            created_by=self.user,
        )
        self.assertIsNotNone(question.pk)


class QuizPersistenceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="quiz_view_user", password="Password123!")
        self.course = Course.objects.create(
            title="Quiz Course",
            status=CourseStatus.PUBLISHED,
            created_by=self.user,
        )
        self.chapter = Chapter.objects.create(course=self.course, title="Chapter A", order_no=1)
        self.lesson = Lesson.objects.create(chapter=self.chapter, title="Lesson A", order_no=1)

        self.q1 = Question.objects.create(
            lesson=self.lesson,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="2+2=?",
            options=[{"key": "A", "text": "3"}, {"key": "B", "text": "4"}],
            correct_answer=["B"],
            explanation="2+2=4",
            score=5,
            created_by=self.user,
        )
        self.q2 = Question.objects.create(
            lesson=self.lesson,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="3+3=?",
            options=[{"key": "A", "text": "6"}, {"key": "B", "text": "5"}],
            correct_answer=["A"],
            explanation="3+3=6",
            score=5,
            created_by=self.user,
        )

    def test_submission_creates_persistent_records(self):
        self.client.login(username="quiz_view_user", password="Password123!")
        response = self.client.post(
            reverse("quiz:take_lesson_quiz", kwargs={"lesson_id": self.lesson.id}),
            {f"q_{self.q1.id}": "B", f"q_{self.q2.id}": "B"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "提交编号")

        self.assertEqual(QuizSubmission.objects.count(), 1)
        submission = QuizSubmission.objects.first()
        self.assertEqual(submission.total_questions, 2)
        self.assertEqual(submission.correct_count, 1)
        self.assertEqual(submission.earned_score, 5)
        self.assertEqual(submission.total_score, 10)
        self.assertEqual(QuizAnswer.objects.filter(submission=submission).count(), 2)

        wrong = WrongQuestion.objects.get(user=self.user, question=self.q2)
        self.assertEqual(wrong.wrong_count, 1)
        self.assertFalse(wrong.resolved)

    def test_course_quiz_page_renders(self):
        self.client.login(username="quiz_view_user", password="Password123!")
        response = self.client.get(reverse("quiz:take_course_quiz", kwargs={"course_slug": self.course.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "单元综合测验")
        self.assertContains(response, self.q1.stem)

    def test_course_quiz_submission_creates_records(self):
        self.client.login(username="quiz_view_user", password="Password123!")
        response = self.client.post(
            reverse("quiz:take_course_quiz", kwargs={"course_slug": self.course.slug}),
            {f"q_{self.q1.id}": "B", f"q_{self.q2.id}": "A"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "单元综合测验")
        submission = QuizSubmission.objects.order_by("-id").first()
        self.assertEqual(submission.total_questions, 2)
        self.assertEqual(submission.correct_count, 2)

    def test_wrong_question_counter_and_resolve_flow(self):
        self.client.login(username="quiz_view_user", password="Password123!")
        url = reverse("quiz:take_lesson_quiz", kwargs={"lesson_id": self.lesson.id})

        self.client.post(url, {f"q_{self.q1.id}": "B", f"q_{self.q2.id}": "B"})
        self.client.post(url, {f"q_{self.q1.id}": "B", f"q_{self.q2.id}": "B"})

        wrong = WrongQuestion.objects.get(user=self.user, question=self.q2)
        self.assertEqual(wrong.wrong_count, 2)
        self.assertFalse(wrong.resolved)

        self.client.post(url, {f"q_{self.q1.id}": "B", f"q_{self.q2.id}": "A"})
        wrong.refresh_from_db()
        self.assertEqual(wrong.wrong_count, 2)
        self.assertTrue(wrong.resolved)

    def test_history_and_wrong_book_require_login(self):
        history_url = reverse("quiz:submission_history")
        wrong_url = reverse("quiz:wrong_question_list")

        history_resp = self.client.get(history_url)
        wrong_resp = self.client.get(wrong_url)

        self.assertEqual(history_resp.status_code, 302)
        self.assertIn("/accounts/login/", history_resp.url)
        self.assertEqual(wrong_resp.status_code, 302)
        self.assertIn("/accounts/login/", wrong_resp.url)

    def test_retry_wrong_questions_requires_login(self):
        retry_url = reverse("quiz:retry_wrong_questions", kwargs={"lesson_id": self.lesson.id})
        response = self.client.get(retry_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_retry_wrong_questions_returns_404_when_no_open_wrong_question(self):
        self.client.login(username="quiz_view_user", password="Password123!")
        retry_url = reverse("quiz:retry_wrong_questions", kwargs={"lesson_id": self.lesson.id})
        response = self.client.get(retry_url)
        self.assertEqual(response.status_code, 404)

    def test_retry_wrong_questions_contains_only_open_wrong_items(self):
        self.client.login(username="quiz_view_user", password="Password123!")
        quiz_url = reverse("quiz:take_lesson_quiz", kwargs={"lesson_id": self.lesson.id})
        self.client.post(quiz_url, {f"q_{self.q1.id}": "B", f"q_{self.q2.id}": "B"})

        retry_url = reverse("quiz:retry_wrong_questions", kwargs={"lesson_id": self.lesson.id})
        response = self.client.get(retry_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.q2.stem)
        self.assertNotContains(response, self.q1.stem)

    def test_retry_wrong_questions_submission_resolves_item(self):
        self.client.login(username="quiz_view_user", password="Password123!")
        quiz_url = reverse("quiz:take_lesson_quiz", kwargs={"lesson_id": self.lesson.id})
        self.client.post(quiz_url, {f"q_{self.q1.id}": "B", f"q_{self.q2.id}": "B"})

        retry_url = reverse("quiz:retry_wrong_questions", kwargs={"lesson_id": self.lesson.id})
        response = self.client.post(retry_url, {f"q_{self.q2.id}": "A"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "错题重练")

        wrong = WrongQuestion.objects.get(user=self.user, question=self.q2)
        self.assertTrue(wrong.resolved)

        last_submission = QuizSubmission.objects.order_by("-id").first()
        self.assertEqual(last_submission.total_questions, 1)
        self.assertEqual(last_submission.correct_count, 1)

    def test_history_and_wrong_book_pages_render_for_authenticated_user(self):
        self.client.login(username="quiz_view_user", password="Password123!")
        quiz_url = reverse("quiz:take_lesson_quiz", kwargs={"lesson_id": self.lesson.id})
        self.client.post(quiz_url, {f"q_{self.q1.id}": "A", f"q_{self.q2.id}": "A"})

        history_resp = self.client.get(reverse("quiz:submission_history"))
        wrong_resp = self.client.get(reverse("quiz:wrong_question_list"))

        self.assertEqual(history_resp.status_code, 200)
        self.assertContains(history_resp, "我的测验提交历史")
        self.assertEqual(wrong_resp.status_code, 200)
        self.assertContains(wrong_resp, "我的错题本")


class QuizManageViewTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(username="quiz_manage_student", password="Password123!")
        self.teacher = User.objects.create_user(username="quiz_manage_teacher", password="Password123!")
        self.other_teacher = User.objects.create_user(username="quiz_manage_teacher_2", password="Password123!")
        self.staff = User.objects.create_user(username="quiz_manage_staff", password="Password123!", is_staff=True)

        self.teacher.profile.role = UserRole.TEACHER
        self.teacher.profile.save(update_fields=["role"])
        self.other_teacher.profile.role = UserRole.TEACHER
        self.other_teacher.profile.save(update_fields=["role"])

        self.teacher_course = Course.objects.create(title="Teacher Quiz Course", created_by=self.teacher)
        self.other_course = Course.objects.create(title="Other Quiz Course", created_by=self.other_teacher)
        self.teacher_chapter = Chapter.objects.create(course=self.teacher_course, title="Teacher Chapter", order_no=1)
        self.other_chapter = Chapter.objects.create(course=self.other_course, title="Other Chapter", order_no=1)
        self.teacher_lesson = Lesson.objects.create(chapter=self.teacher_chapter, title="Teacher Lesson", order_no=1)
        self.other_lesson = Lesson.objects.create(chapter=self.other_chapter, title="Other Lesson", order_no=1)

        self.teacher_question = Question.objects.create(
            lesson=self.teacher_lesson,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="Teacher Question",
            options=[{"key": "A", "text": "Yes"}, {"key": "B", "text": "No"}],
            correct_answer=["A"],
            created_by=self.teacher,
        )
        self.other_question = Question.objects.create(
            lesson=self.other_lesson,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="Other Question",
            options=[{"key": "A", "text": "1"}, {"key": "B", "text": "2"}],
            correct_answer=["B"],
            created_by=self.other_teacher,
        )

    def test_manage_question_list_requires_login(self):
        response = self.client.get(reverse("quiz:manage_question_list", kwargs={"lesson_id": self.teacher_lesson.id}))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_student_cannot_access_manage_question_list(self):
        self.client.login(username="quiz_manage_student", password="Password123!")
        response = self.client.get(reverse("quiz:manage_question_list", kwargs={"lesson_id": self.teacher_lesson.id}))
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_access_own_question_list(self):
        self.client.login(username="quiz_manage_teacher", password="Password123!")
        response = self.client.get(reverse("quiz:manage_question_list", kwargs={"lesson_id": self.teacher_lesson.id}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Teacher Question")

    def test_teacher_can_create_question(self):
        self.client.login(username="quiz_manage_teacher", password="Password123!")
        response = self.client.post(
            reverse("quiz:manage_question_create", kwargs={"lesson_id": self.teacher_lesson.id}),
            {
                "question_type": QuestionType.SINGLE_CHOICE,
                "difficulty": "medium",
                "stem": "Created Question",
                "options_text": "A|Apple\nB|Banana",
                "correct_answer_text": "B",
                "score": 6,
                "is_active": "on",
                "explanation": "Because B is correct.",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        created = Question.objects.get(stem="Created Question")
        self.assertEqual(created.lesson, self.teacher_lesson)
        self.assertEqual(created.correct_answer, ["B"])
        self.assertEqual(created.options, [{"key": "A", "text": "Apple"}, {"key": "B", "text": "Banana"}])
        self.assertTrue(
            ContentAuditLog.objects.filter(
                target_type=AuditTargetType.QUESTION,
                target_id=created.id,
                action="create",
            ).exists()
        )

    def test_teacher_cannot_create_question_for_other_lesson(self):
        self.client.login(username="quiz_manage_teacher", password="Password123!")
        response = self.client.post(
            reverse("quiz:manage_question_create", kwargs={"lesson_id": self.other_lesson.id}),
            {
                "question_type": QuestionType.SINGLE_CHOICE,
                "difficulty": "easy",
                "stem": "Should fail",
                "options_text": "A|1\nB|2",
                "correct_answer_text": "A",
                "score": 5,
                "is_active": "on",
                "explanation": "",
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_edit_own_question(self):
        self.client.login(username="quiz_manage_teacher", password="Password123!")
        response = self.client.post(
            reverse("quiz:manage_question_edit", kwargs={"question_id": self.teacher_question.id}),
            {
                "question_type": QuestionType.MULTIPLE_CHOICE,
                "difficulty": "hard",
                "stem": "Teacher Question Updated",
                "options_text": "A|Alpha\nB|Beta\nC|Gamma",
                "correct_answer_text": "A,C",
                "score": 8,
                "is_active": "on",
                "explanation": "Updated explanation",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.teacher_question.refresh_from_db()
        self.assertEqual(self.teacher_question.stem, "Teacher Question Updated")
        self.assertEqual(self.teacher_question.correct_answer, ["A", "C"])

    def test_teacher_cannot_edit_other_question(self):
        self.client.login(username="quiz_manage_teacher", password="Password123!")
        response = self.client.get(reverse("quiz:manage_question_edit", kwargs={"question_id": self.other_question.id}))
        self.assertEqual(response.status_code, 404)

    def test_toggle_question_active_requires_post(self):
        self.client.login(username="quiz_manage_teacher", password="Password123!")
        response = self.client.get(
            reverse("quiz:manage_question_toggle_active", kwargs={"question_id": self.teacher_question.id})
        )
        self.assertEqual(response.status_code, 405)

    def test_teacher_can_toggle_own_question_active(self):
        self.client.login(username="quiz_manage_teacher", password="Password123!")
        response = self.client.post(
            reverse("quiz:manage_question_toggle_active", kwargs={"question_id": self.teacher_question.id}),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.teacher_question.refresh_from_db()
        self.assertFalse(self.teacher_question.is_active)

    def test_teacher_cannot_toggle_other_question_active(self):
        self.client.login(username="quiz_manage_teacher", password="Password123!")
        response = self.client.post(
            reverse("quiz:manage_question_toggle_active", kwargs={"question_id": self.other_question.id}),
        )
        self.assertEqual(response.status_code, 404)
