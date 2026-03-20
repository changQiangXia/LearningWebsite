from django.contrib.auth.models import User
from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from courses.models import Chapter, Course, CourseStatus, Lesson
from forum.models import ForumPost, ForumPostStatus
from quiz.models import Question, QuestionType
from resources.models import Resource, ResourceType
from search.models import SearchDocument, SearchSourceType


class SearchDocumentTests(TestCase):
    def test_source_pair_must_be_unique(self):
        SearchDocument.objects.create(
            source_type=SearchSourceType.COURSE,
            source_id=101,
            title="Python Basics",
            body="Intro content",
        )

        with self.assertRaises(IntegrityError):
            SearchDocument.objects.create(
                source_type=SearchSourceType.COURSE,
                source_id=101,
                title="Python Basics Duplicate",
                body="Duplicate record",
            )

    def test_metadata_default_is_dict(self):
        doc = SearchDocument.objects.create(
            source_type=SearchSourceType.LESSON,
            source_id=202,
            title="Lesson title",
            body="Lesson body",
        )
        self.assertIsInstance(doc.metadata, dict)


class SearchSignalAndCommandTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="search_signal_user", password="Password123!")

    def test_signals_create_documents_and_active_flags(self):
        published_course = Course.objects.create(
            title="Published Course",
            status=CourseStatus.PUBLISHED,
            description="Published description",
            created_by=self.user,
        )
        draft_course = Course.objects.create(
            title="Draft Course",
            status=CourseStatus.DRAFT,
            description="Draft description",
            created_by=self.user,
        )
        chapter = Chapter.objects.create(course=published_course, title="C1", order_no=1)
        lesson = Lesson.objects.create(chapter=chapter, title="Lesson 1", order_no=1, content="Lesson body")
        post = ForumPost.objects.create(author=self.user, title="Forum Post", content="Forum body")
        question = Question.objects.create(
            lesson=lesson,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="What is Django?",
            options=[{"key": "A", "text": "Framework"}, {"key": "B", "text": "Database"}],
            correct_answer=["A"],
            created_by=self.user,
        )
        published_resource = Resource.objects.create(
            title="Published Resource",
            description="Searchable resource body",
            resource_type=ResourceType.READING,
            course=published_course,
            external_url="https://example.com/public-resource",
            tags="django, resource",
            created_by=self.user,
            is_published=True,
        )
        hidden_resource = Resource.objects.create(
            title="Hidden Resource",
            description="Should be inactive in search.",
            resource_type=ResourceType.TOOL,
            course=published_course,
            external_url="https://example.com/hidden-resource",
            tags="hidden",
            created_by=self.user,
            is_published=False,
        )

        self.assertTrue(
            SearchDocument.objects.filter(
                source_type=SearchSourceType.COURSE,
                source_id=published_course.id,
                is_active=True,
            ).exists()
        )
        self.assertTrue(
            SearchDocument.objects.filter(
                source_type=SearchSourceType.COURSE,
                source_id=draft_course.id,
                is_active=False,
            ).exists()
        )
        self.assertTrue(
            SearchDocument.objects.filter(
                source_type=SearchSourceType.LESSON,
                source_id=lesson.id,
                is_active=True,
            ).exists()
        )
        self.assertTrue(
            SearchDocument.objects.filter(
                source_type=SearchSourceType.FORUM_POST,
                source_id=post.id,
                is_active=True,
            ).exists()
        )
        self.assertTrue(
            SearchDocument.objects.filter(
                source_type=SearchSourceType.QUESTION,
                source_id=question.id,
                is_active=True,
            ).exists()
        )
        self.assertTrue(
            SearchDocument.objects.filter(
                source_type=SearchSourceType.RESOURCE,
                source_id=published_resource.id,
                is_active=True,
            ).exists()
        )
        self.assertTrue(
            SearchDocument.objects.filter(
                source_type=SearchSourceType.RESOURCE,
                source_id=hidden_resource.id,
                is_active=False,
            ).exists()
        )

    def test_rebuild_search_index_command(self):
        course = Course.objects.create(
            title="Command Course",
            status=CourseStatus.PUBLISHED,
            created_by=self.user,
        )
        chapter = Chapter.objects.create(course=course, title="C1", order_no=1)
        lesson = Lesson.objects.create(chapter=chapter, title="L1", order_no=1, content="abc")
        ForumPost.objects.create(author=self.user, title="P1", content="abc", status=ForumPostStatus.PUBLISHED)
        Question.objects.create(
            lesson=lesson,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="Q1",
            options=[{"key": "A", "text": "A"}, {"key": "B", "text": "B"}],
            correct_answer=["A"],
            created_by=self.user,
        )
        resource = Resource.objects.create(
            title="Command Resource",
            description="abc",
            resource_type=ResourceType.COURSEWARE,
            course=course,
            external_url="https://example.com/command-resource",
            tags="command",
            created_by=self.user,
        )

        SearchDocument.objects.all().delete()
        self.assertEqual(SearchDocument.objects.count(), 0)

        call_command("rebuild_search_index")
        self.assertTrue(
            SearchDocument.objects.filter(
                source_type=SearchSourceType.RESOURCE,
                source_id=resource.id,
                is_active=True,
            ).exists()
        )


class SearchViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="search_user", password="Password123!")
        self.course_pub = Course.objects.create(
            title="Python Web Development",
            description="Django intro",
            status=CourseStatus.PUBLISHED,
            created_by=self.user,
        )
        Course.objects.create(
            title="Hidden Course",
            description="Should not be shown",
            status=CourseStatus.DRAFT,
            created_by=self.user,
        )
        chapter = Chapter.objects.create(course=self.course_pub, title="Chapter 1", order_no=1)
        self.lesson = Lesson.objects.create(chapter=chapter, title="Django Model Basics", content="ORM intro", order_no=1)
        ForumPost.objects.create(
            author=self.user,
            title="Django Help",
            content="How to write models?",
            status=ForumPostStatus.PUBLISHED,
        )
        Question.objects.create(
            lesson=self.lesson,
            question_type=QuestionType.SINGLE_CHOICE,
            stem="What does ORM stand for?",
            options=[{"key": "A", "text": "Object Relational Mapping"}, {"key": "B", "text": "Other"}],
            correct_answer=["A"],
            created_by=self.user,
        )
        Resource.objects.create(
            title="Django Resource Pack",
            description="Useful Django references",
            resource_type=ResourceType.READING,
            course=self.course_pub,
            external_url="https://example.com/django-resource",
            tags="Django, ORM",
            created_by=self.user,
            is_published=True,
        )
        Resource.objects.create(
            title="Hidden Django Resource",
            description="Should not be shown",
            resource_type=ResourceType.TOOL,
            course=self.course_pub,
            external_url="https://example.com/hidden-django-resource",
            tags="hidden",
            created_by=self.user,
            is_published=False,
        )

    def test_search_returns_expected_sections(self):
        response = self.client.get(reverse("search:index"), {"q": "Django"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Web Development")
        self.assertContains(response, "Django Model Basics")
        self.assertContains(response, "Django Help")
        self.assertContains(response, "What does ORM stand for?")
        self.assertContains(response, "Django Resource Pack")
        self.assertNotContains(response, "Hidden Course")
        self.assertNotContains(response, "Hidden Django Resource")
