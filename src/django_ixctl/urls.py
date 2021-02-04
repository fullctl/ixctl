from django.urls import include, path

import django_ixctl.views as views

urlpatterns = [
    path(
        "api/",
        include(("django_ixctl.rest.urls.ixctl", "ixctl_api"), namespace="ixctl_api"),
    ),
    path(
        "<str:org_tag>/<str:ix_tag>/export/memberlist.json",
        views.export_ixf,
        name="ixf export",
    ),
    path("<str:org_tag>/", views.view_instance, name="ixctl-home"),
    path("", views.org_redirect),
]
