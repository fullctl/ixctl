from django.urls import path, include
from django.contrib import admin

import django_ixctl.urls

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("social_django.urls", namespace="social")),
    path("", include("django_ixctl.urls")),
]
