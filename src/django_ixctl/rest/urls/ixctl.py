from django.urls import path, include
from django_ixctl.rest.views.ixctl import (
    InternetExchange,
    Member,
    Routeserver,
    RouteserverConfig,
)
import django_ixctl.rest.route.ixctl


urlpatterns = [
    path("", include(django_ixctl.rest.route.ixctl.router.urls)),
]
