from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.conf import settings

import fullctl.django.rest.urls.service_bridge as service_bridge
import django_ixctl.views as views
import django_ixctl.service_bridge

urlpatterns = service_bridge.urlpatterns(["aaactl", "devicectl"])

urlpatterns += [
    path(
        "api/",
        include(("django_ixctl.rest.urls.ixctl", "ixctl_api"), namespace="ixctl_api"),
    ),
    path("<str:org_tag>/<str:ix_tag>/export/memberlist.json", views.export_ixf, name="ixf export"),
    path("<str:org_tag>/", views.view_instance, name="ixctl-home"),
    path("", views.org_redirect),
]
