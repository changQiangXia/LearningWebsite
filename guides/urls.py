from django.urls import path

from . import views

app_name = "guides"

urlpatterns = [
    path("", views.guide_list, name="guide_list"),
    path("manage/", views.manage_guide_list, name="manage_guide_list"),
    path("manage/new/", views.manage_guide_create, name="manage_guide_create"),
    path("manage/<int:guide_id>/edit/", views.manage_guide_edit, name="manage_guide_edit"),
    path(
        "manage/<int:guide_id>/toggle-publish/",
        views.manage_guide_toggle_publish,
        name="manage_guide_toggle_publish",
    ),
    path("<int:guide_id>/", views.guide_detail, name="guide_detail"),
]
