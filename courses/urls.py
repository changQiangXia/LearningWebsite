from django.urls import path

from . import views

app_name = "courses"

urlpatterns = [
    path("", views.course_list, name="course_list"),
    path("manage/", views.manage_dashboard, name="manage_dashboard"),
    path("manage/course/new/", views.manage_course_create, name="manage_course_create"),
    path("manage/course/<int:course_id>/edit/", views.manage_course_edit, name="manage_course_edit"),
    path(
        "manage/course/<int:course_id>/toggle-status/",
        views.manage_course_toggle_status,
        name="manage_course_toggle_status",
    ),
    path(
        "manage/course/<int:course_id>/toggle-archive/",
        views.manage_course_toggle_archive,
        name="manage_course_toggle_archive",
    ),
    path("manage/course/<int:course_id>/chapter/new/", views.manage_chapter_create, name="manage_chapter_create"),
    path("manage/chapter/<int:chapter_id>/edit/", views.manage_chapter_edit, name="manage_chapter_edit"),
    path(
        "manage/chapter/<int:chapter_id>/toggle-active/",
        views.manage_chapter_toggle_active,
        name="manage_chapter_toggle_active",
    ),
    path("manage/chapter/<int:chapter_id>/lesson/new/", views.manage_lesson_create, name="manage_lesson_create"),
    path("manage/lesson/<int:lesson_id>/edit/", views.manage_lesson_edit, name="manage_lesson_edit"),
    path(
        "manage/lesson/<int:lesson_id>/toggle-active/",
        views.manage_lesson_toggle_active,
        name="manage_lesson_toggle_active",
    ),
    path("lesson/<int:lesson_id>/complete/", views.mark_lesson_complete, name="mark_lesson_complete"),
    path("lesson/<int:lesson_id>/", views.lesson_detail, name="lesson_detail"),
    path("<slug:slug>/", views.course_detail, name="course_detail"),
]
