from django.urls import path, include

import django_ixctl.rest.views.account
import django_ixctl.rest.route.account

urlpatterns = [
    path("", include(django_ixctl.rest.route.account.router.urls)),
]
