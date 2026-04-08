from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.index, name="index"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("feedback/<slug:course_slug>/", views.feedback_form, name="feedback_form"),
]
