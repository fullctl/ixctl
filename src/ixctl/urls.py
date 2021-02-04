from django.contrib import admin
from django.urls import include, path

# import django_ixctl.urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("social_django.urls", namespace="social")),
    path("", include("fullctl.django.urls")),
    path("", include("django_ixctl.urls")),
]
