"""Root URL configuration for the LearningWebsite project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("core.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("courses/", include("courses.urls")),
    path("resources/", include("resources.urls")),
    path("guides/", include("guides.urls")),
    path("practice/", include("practice.urls")),
    path("quiz/", include("quiz.urls")),
    path("forum/", include("forum.urls")),
    path("search/", include("search.urls")),
    path("analytics/", include("analytics.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
