from django.urls import path

from . import views

app_name = "quiz"

urlpatterns = [
    path("", views.index, name="index"),
    path("manage/lesson/<int:lesson_id>/questions/", views.manage_question_list, name="manage_question_list"),
    path("manage/lesson/<int:lesson_id>/question/new/", views.manage_question_create, name="manage_question_create"),
    path("manage/question/<int:question_id>/edit/", views.manage_question_edit, name="manage_question_edit"),
    path(
        "manage/question/<int:question_id>/toggle-active/",
        views.manage_question_toggle_active,
        name="manage_question_toggle_active",
    ),
    path("lesson/<int:lesson_id>/", views.take_lesson_quiz, name="take_lesson_quiz"),
    path("retry-wrong/<int:lesson_id>/", views.retry_wrong_questions, name="retry_wrong_questions"),
    path("history/", views.submission_history, name="submission_history"),
    path("wrong-questions/", views.wrong_question_list, name="wrong_question_list"),
]
