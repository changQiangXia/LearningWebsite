from django.urls import path

from . import views

app_name = "forum"

urlpatterns = [
    path("", views.post_list, name="post_list"),
    path("new/", views.post_create, name="post_create"),
    path("notes/", views.note_list, name="note_list"),
    path("notes/new/", views.note_create, name="note_create"),
    path("<int:post_id>/", views.post_detail, name="post_detail"),
    path("<int:post_id>/comment/", views.comment_create, name="comment_create"),
    path("<int:post_id>/toggle-like/", views.toggle_like, name="toggle_like"),
    path("<int:post_id>/toggle-solved/", views.toggle_solved, name="toggle_solved"),
    path("<int:post_id>/toggle-pin/", views.toggle_pin, name="toggle_pin"),
    path("<int:post_id>/change-status/", views.change_status, name="change_status"),
]
