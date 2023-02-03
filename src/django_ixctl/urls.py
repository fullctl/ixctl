import fullctl.django.rest.urls.service_bridge_proxy as proxy
from django.conf import settings
from django.urls import include, path

import django_ixctl.views as views

proxy.setup(
    "aaactl",
    proxy.proxy_api(
        "aaactl",
        settings.AAACTL_URL,
        [
            (
                "billing/org/{org_tag}/start_trial/",
                "billing/<str:org_tag>/start_trial/",
                "start-trial",
            )
        ],
    ),
)

urlpatterns = proxy.urlpatterns(["aaactl", "devicectl"])

urlpatterns += [
    path(
        "api/",
        include(("django_ixctl.rest.urls.ixctl", "ixctl_api"), namespace="ixctl_api"),
    ),
    path(
        "<str:org_tag>/<str:ix_tag>/export/memberlist.json",
        views.export_ixf,
        name="ixf export",
    ),
    path("<str:org_tag>/<str:ix_tag>/", views.view_instance_load_ix, name="ixctl-home"),
    path("<str:org_tag>/", views.view_instance, name="ixctl-home"),
    path("", views.org_redirect),
]
