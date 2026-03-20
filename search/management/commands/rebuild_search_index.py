from django.core.management.base import BaseCommand

from courses.models import Course, Lesson
from forum.models import ForumPost
from quiz.models import Question
from resources.models import Resource
from search.indexing import index_course, index_forum_post, index_lesson, index_question, index_resource
from search.models import SearchDocument


class Command(BaseCommand):
    help = "Rebuild search index documents from business tables."

    def handle(self, *args, **options):
        self.stdout.write("Clearing existing search documents...")
        SearchDocument.objects.all().delete()

        self.stdout.write("Indexing courses...")
        for course in Course.objects.select_related("created_by").iterator():
            index_course(course)

        self.stdout.write("Indexing lessons...")
        for lesson in Lesson.objects.select_related("chapter", "chapter__course").iterator():
            index_lesson(lesson)

        self.stdout.write("Indexing forum posts...")
        for post in ForumPost.objects.iterator():
            index_forum_post(post)

        self.stdout.write("Indexing questions...")
        for question in Question.objects.select_related("lesson", "lesson__chapter", "lesson__chapter__course").iterator():
            index_question(question)

        self.stdout.write("Indexing resources...")
        for resource in Resource.objects.select_related("course").iterator():
            index_resource(resource)

        count = SearchDocument.objects.count()
        self.stdout.write(self.style.SUCCESS(f"Search index rebuild completed. documents={count}"))
