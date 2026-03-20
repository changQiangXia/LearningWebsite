from django.urls import path

from . import views

app_name = "practice"

urlpatterns = [
    path("", views.index, name="index"),
    path("dialogue/", views.dialogue_lab, name="dialogue_lab"),
    path("speech/", views.speech_lab, name="speech_lab"),
    path("image/", views.image_lab, name="image_lab"),
]
