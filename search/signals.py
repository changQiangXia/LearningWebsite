from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from courses.models import Chapter, Course, Lesson
from forum.models import ForumPost
from quiz.models import Question
from search.indexing import (
    index_course,
    index_forum_post,
    index_lesson,
    index_question,
    remove_document,
)
from search.models import SearchSourceType


@receiver(post_save, sender=Course)
def index_course_on_save(sender, instance: Course, **kwargs):
    index_course(instance)
    for lesson in Lesson.objects.select_related("chapter", "chapter__course").filter(chapter__course=instance):
        index_lesson(lesson)
    for question in Question.objects.select_related("lesson", "lesson__chapter", "lesson__chapter__course").filter(
        lesson__chapter__course=instance
    ):
        index_question(question)


@receiver(post_delete, sender=Course)
def remove_course_on_delete(sender, instance: Course, **kwargs):
    remove_document(SearchSourceType.COURSE, instance.id)


@receiver(post_save, sender=Lesson)
def index_lesson_on_save(sender, instance: Lesson, **kwargs):
    index_lesson(instance)
    for question in Question.objects.select_related("lesson", "lesson__chapter", "lesson__chapter__course").filter(
        lesson=instance
    ):
        index_question(question)


@receiver(post_delete, sender=Lesson)
def remove_lesson_on_delete(sender, instance: Lesson, **kwargs):
    remove_document(SearchSourceType.LESSON, instance.id)


@receiver(post_save, sender=Chapter)
def reindex_chapter_related_documents(sender, instance: Chapter, **kwargs):
    for lesson in Lesson.objects.select_related("chapter", "chapter__course").filter(chapter=instance):
        index_lesson(lesson)
    for question in Question.objects.select_related("lesson", "lesson__chapter", "lesson__chapter__course").filter(
        lesson__chapter=instance
    ):
        index_question(question)


@receiver(post_save, sender=ForumPost)
def index_forum_post_on_save(sender, instance: ForumPost, **kwargs):
    index_forum_post(instance)


@receiver(post_delete, sender=ForumPost)
def remove_forum_post_on_delete(sender, instance: ForumPost, **kwargs):
    remove_document(SearchSourceType.FORUM_POST, instance.id)


@receiver(post_save, sender=Question)
def index_question_on_save(sender, instance: Question, **kwargs):
    index_question(instance)


@receiver(post_delete, sender=Question)
def remove_question_on_delete(sender, instance: Question, **kwargs):
    remove_document(SearchSourceType.QUESTION, instance.id)
