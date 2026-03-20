from django.urls import path

from . import views

app_name = "resources"

urlpatterns = [
    path("", views.resource_list, name="resource_list"),
    path("teacher/", views.teacher_resource_list, name="teacher_resource_list"),
    path("manage/", views.manage_resource_list, name="manage_resource_list"),
    path("manage/new/", views.manage_resource_create, name="manage_resource_create"),
    path("manage/<int:resource_id>/edit/", views.manage_resource_edit, name="manage_resource_edit"),
    path(
        "manage/<int:resource_id>/toggle-publish/",
        views.manage_resource_toggle_publish,
        name="manage_resource_toggle_publish",
    ),
    path("<slug:slug>/", views.resource_detail, name="resource_detail"),
]
