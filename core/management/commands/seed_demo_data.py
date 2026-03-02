from django.contrib.auth import get_user_model
from django.core.management import BaseCommand, call_command
from django.db import transaction
from django.utils import timezone

from accounts.models import UserRole
from courses.audit import log_content_action
from courses.models import AuditTargetType, Chapter, Course, CourseStatus, LearningProgress, Lesson
from forum.models import ForumComment, ForumPost, ForumPostCategory, ForumPostStatus
from quiz.models import Question, QuestionDifficulty, QuestionType, QuizAnswer, QuizSubmission, WrongQuestion


User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo users and business data for project demonstration."

    def add_arguments(self, parser):
        parser.add_argument(
            "--password",
            default="DemoPass123!",
            help="Password to set for all demo users.",
        )
        parser.add_argument(
            "--skip-search-index",
            action="store_true",
            help="Skip search index rebuild after seeding.",
        )

    def _ensure_user(self, *, username, email, password, is_staff, is_superuser, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        changed = created
        if user.email != email:
            user.email = email
            changed = True
        if user.is_staff != is_staff:
            user.is_staff = is_staff
            changed = True
        if user.is_superuser != is_superuser:
            user.is_superuser = is_superuser
            changed = True
        user.set_password(password)
        changed = True
        if changed:
            user.save()

        profile = user.profile
        if profile.role != role:
            profile.role = role
            profile.save(update_fields=["role"])
        return user

    @staticmethod
    def _ensure_course(*, title, description, status, created_by):
        course = Course.objects.filter(title=title, created_by=created_by).first()
        if course is None:
            course = Course.objects.create(
                title=title,
                description=description,
                status=status,
                created_by=created_by,
            )
            created = True
        else:
            created = False
            course.description = description
            course.status = status
            course.save(update_fields=["description", "status", "updated_at"])
        return course, created

    @staticmethod
    def _ensure_chapter(*, course, order_no, title, description, is_active=True):
        chapter, _ = Chapter.objects.update_or_create(
            course=course,
            order_no=order_no,
            defaults={
                "title": title,
                "description": description,
                "is_active": is_active,
            },
        )
        return chapter

    @staticmethod
    def _ensure_lesson(
        *,
        chapter,
        order_no,
        title,
        content,
        estimated_minutes=12,
        video_url="",
        attachment_url="",
        is_free_preview=False,
        is_active=True,
    ):
        lesson, _ = Lesson.objects.update_or_create(
            chapter=chapter,
            order_no=order_no,
            defaults={
                "title": title,
                "content": content,
                "estimated_minutes": estimated_minutes,
                "video_url": video_url,
                "attachment_url": attachment_url,
                "is_free_preview": is_free_preview,
                "is_active": is_active,
            },
        )
        return lesson

    @staticmethod
    def _ensure_question(
        *,
        lesson,
        stem,
        question_type,
        options,
        correct_answer,
        created_by,
        score=5,
        difficulty=QuestionDifficulty.MEDIUM,
        is_active=True,
        explanation="",
    ):
        question = Question.objects.filter(lesson=lesson, stem=stem).first()
        if question is None:
            question = Question.objects.create(
                lesson=lesson,
                stem=stem,
                question_type=question_type,
                options=options,
                correct_answer=correct_answer,
                score=score,
                difficulty=difficulty,
                is_active=is_active,
                explanation=explanation,
                created_by=created_by,
            )
        else:
            question.question_type = question_type
            question.options = options
            question.correct_answer = correct_answer
            question.score = score
            question.difficulty = difficulty
            question.is_active = is_active
            question.explanation = explanation
            question.created_by = created_by
            question.save()
        return question

    def handle(self, *args, **options):
        password = options["password"]
        skip_search_index = bool(options["skip_search_index"])

        with transaction.atomic():
            teacher = self._ensure_user(
                username="demo_teacher",
                email="demo_teacher@example.com",
                password=password,
                is_staff=False,
                is_superuser=False,
                role=UserRole.TEACHER,
            )
            student = self._ensure_user(
                username="demo_student",
                email="demo_student@example.com",
                password=password,
                is_staff=False,
                is_superuser=False,
                role=UserRole.STUDENT,
            )
            staff = self._ensure_user(
                username="demo_admin",
                email="demo_admin@example.com",
                password=password,
                is_staff=True,
                is_superuser=True,
                role=UserRole.ADMIN,
            )

            course_pub, created_pub = self._ensure_course(
                title="Python Full Stack 101",
                description="Core Python web stack from model to deployment.",
                status=CourseStatus.PUBLISHED,
                created_by=teacher,
            )
            course_draft, created_draft = self._ensure_course(
                title="Data Structures Practice",
                description="Exam-oriented data structure drills and coding tasks.",
                status=CourseStatus.DRAFT,
                created_by=teacher,
            )
            course_archived, created_archived = self._ensure_course(
                title="Computer Networks Sprint",
                description="Condensed networking concepts and packet-level exercises.",
                status=CourseStatus.ARCHIVED,
                created_by=teacher,
            )

            ch1 = self._ensure_chapter(
                course=course_pub,
                order_no=1,
                title="Python + Django Foundations",
                description="Project structure, settings, routing, and app layout.",
                is_active=True,
            )
            ch2 = self._ensure_chapter(
                course=course_pub,
                order_no=2,
                title="Performance and Deployment",
                description="Caching, static files, and production deployment basics.",
                is_active=False,
            )
            ch3 = self._ensure_chapter(
                course=course_draft,
                order_no=1,
                title="Linear Structures",
                description="Array, list, stack, queue.",
                is_active=True,
            )
            self._ensure_chapter(
                course=course_archived,
                order_no=1,
                title="Legacy Chapter",
                description="Archived chapter sample.",
                is_active=False,
            )

            l1 = self._ensure_lesson(
                chapter=ch1,
                order_no=1,
                title="Django MVC and URL Dispatch",
                content="Understand URL conf, view functions, and template rendering.",
                estimated_minutes=18,
                is_free_preview=True,
                is_active=True,
            )
            l2 = self._ensure_lesson(
                chapter=ch1,
                order_no=2,
                title="ORM Models and Query Patterns",
                content="Build normalized tables and query common business metrics.",
                estimated_minutes=22,
                is_active=True,
            )
            self._ensure_lesson(
                chapter=ch2,
                order_no=1,
                title="Nginx + Gunicorn Quickstart",
                content="Expose WSGI app behind reverse proxy.",
                estimated_minutes=16,
                is_active=True,
            )
            self._ensure_lesson(
                chapter=ch3,
                order_no=1,
                title="Stack and Queue Implementations",
                content="Python class implementations and complexity analysis.",
                estimated_minutes=20,
                is_active=True,
            )

            q1 = self._ensure_question(
                lesson=l1,
                stem="Which command applies pending Django migrations?",
                question_type=QuestionType.SINGLE_CHOICE,
                options=[
                    {"key": "A", "text": "python manage.py runserver"},
                    {"key": "B", "text": "python manage.py migrate"},
                    {"key": "C", "text": "python manage.py collectstatic"},
                ],
                correct_answer=["B"],
                created_by=teacher,
                score=5,
                difficulty=QuestionDifficulty.EASY,
                is_active=True,
                explanation="migrate applies database schema changes.",
            )
            q2 = self._ensure_question(
                lesson=l1,
                stem="Choose valid Django app-layer responsibilities.",
                question_type=QuestionType.MULTIPLE_CHOICE,
                options=[
                    {"key": "A", "text": "Define data models"},
                    {"key": "B", "text": "Write business view logic"},
                    {"key": "C", "text": "Compile Python to machine code"},
                ],
                correct_answer=["A", "B"],
                created_by=teacher,
                score=8,
                difficulty=QuestionDifficulty.MEDIUM,
                is_active=True,
                explanation="A and B are expected backend app responsibilities.",
            )
            self._ensure_question(
                lesson=l2,
                stem="What does ORM stand for?",
                question_type=QuestionType.SHORT_ANSWER,
                options=[],
                correct_answer=["Object Relational Mapping", "ORM full form is Object Relational Mapping"],
                created_by=teacher,
                score=6,
                difficulty=QuestionDifficulty.EASY,
                is_active=False,
                explanation="ORM is short for Object Relational Mapping.",
            )

            forum_post, _ = ForumPost.objects.update_or_create(
                title="How to prepare for project defense?",
                defaults={
                    "author": student,
                    "content": "I need advice on structuring demo flow and Q&A responses.",
                    "category": ForumPostCategory.HELP,
                    "status": ForumPostStatus.PUBLISHED,
                },
            )
            ForumComment.objects.update_or_create(
                post=forum_post,
                author=teacher,
                content="Start from architecture, then live demo, then metrics and tests.",
                defaults={"parent": None, "is_deleted": False},
            )

            progress, _ = LearningProgress.objects.get_or_create(
                user=student,
                lesson=l1,
                defaults={"view_count": 3, "completed": True, "completed_at": timezone.now()},
            )
            if not progress.completed:
                progress.completed = True
                progress.completed_at = timezone.now()
            progress.view_count = max(progress.view_count, 3)
            progress.save(update_fields=["completed", "completed_at", "view_count", "last_viewed_at"])

            QuizSubmission.objects.filter(user=student, lesson=l1).delete()
            submission = QuizSubmission.objects.create(
                user=student,
                lesson=l1,
                total_questions=2,
                correct_count=1,
                total_score=13,
                earned_score=5,
                accuracy=50,
            )
            QuizAnswer.objects.create(
                submission=submission,
                question=q1,
                user_answer=["b"],
                expected_answer=["b"],
                is_correct=True,
                score_awarded=5,
                explanation_snapshot=q1.explanation,
            )
            QuizAnswer.objects.create(
                submission=submission,
                question=q2,
                user_answer=["a"],
                expected_answer=["a", "b"],
                is_correct=False,
                score_awarded=0,
                explanation_snapshot=q2.explanation,
            )
            WrongQuestion.objects.update_or_create(
                user=student,
                question=q2,
                defaults={"wrong_count": 1, "resolved": False},
            )

            if created_pub:
                log_content_action(
                    actor=teacher,
                    target_type=AuditTargetType.COURSE,
                    target_id=course_pub.id,
                    action="create",
                    message=f"Created demo course '{course_pub.title}'.",
                    course=course_pub,
                )
            if created_draft:
                log_content_action(
                    actor=teacher,
                    target_type=AuditTargetType.COURSE,
                    target_id=course_draft.id,
                    action="create",
                    message=f"Created demo course '{course_draft.title}'.",
                    course=course_draft,
                )
            if created_archived:
                log_content_action(
                    actor=staff,
                    target_type=AuditTargetType.COURSE,
                    target_id=course_archived.id,
                    action="archive",
                    message=f"Archived demo course '{course_archived.title}'.",
                    course=course_archived,
                )
            log_content_action(
                actor=teacher,
                target_type=AuditTargetType.QUESTION,
                target_id=q1.id,
                action="seed",
                message=f"Seeded demo question #{q1.id}.",
                course=l1.chapter.course,
                chapter=l1.chapter,
                lesson=l1,
            )

        if not skip_search_index:
            call_command("rebuild_search_index")

        self.stdout.write(self.style.SUCCESS("Demo data seeding completed."))
        self.stdout.write("Users created/updated (same password):")
        self.stdout.write("  demo_teacher (role=teacher)")
        self.stdout.write("  demo_student (role=student)")
        self.stdout.write("  demo_admin (role=admin, is_staff=True, is_superuser=True)")
        self.stdout.write(f"Password: {password}")
