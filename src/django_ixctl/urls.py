from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.conf import settings

import fullctl.django.rest.urls.proxy
import django_ixctl.views as views

# wire proxied apis
urlpatterns = fullctl.django.rest.urls.proxy.urlpatterns(["devicectl"])

# wire ixctl urls
urlpatterns += [
    path(
        "api/<str:org_tag>/",
        include(("django_ixctl.rest.urls.ixctl", "ixctl_api"), namespace="ixctl_api"),
    ),
    path("<str:org_tag>/export/ixf/<slug:urlkey>", views.export_ixf, name="ixf export"),
    path("<str:org_tag>/", views.view_instance, name="ixctl-home"),
    path("", views.org_redirect),
]
