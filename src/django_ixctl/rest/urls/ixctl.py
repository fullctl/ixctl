from django.urls import include, path

import django_ixctl.rest.route.ixctl
import django_ixctl.rest.views.ixctl

urlpatterns = [
    path("", include(django_ixctl.rest.route.ixctl.router.urls)),
]
