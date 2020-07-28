from django.urls import path, include

import django_ixctl.rest.views.ixctl
import django_ixctl.rest.route.ixctl

urlpatterns = [
    path("", include(django_ixctl.rest.route.ixctl.router.urls)),
]
