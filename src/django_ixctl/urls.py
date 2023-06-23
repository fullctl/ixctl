import fullctl.django.rest.urls.service_bridge_proxy as proxy
from django.conf import settings
from django.urls import include, path

import django_ixctl.views as views

proxy.setup(
    "devicectl",
    proxy.proxy_api(
        "devicectl",
        settings.DEVICECTL_URL,
        [
            # facilities
            ("facility/{org_tag}", "facility/<str:org_tag>/", "facility-list"),
            # devices for each facility
            (
                "facility/{org_tag}/{fac_tag}/devices/",
                "facility/<str:org_tag>/<str:fac_tag>/devices/",
                "facility-devices",
            ),
            # virtual ports for each device
            (
                "device/{org_tag}/{pk}/virtual_ports",
                "device/<str:org_tag>/<int:pk>/virtual_ports/",
                "device-virtual-ports",
            ),
            # traffic graphs
            (
                "virtual_port/{org_tag}/{pk}/traffic",
                "virtual_port/<str:org_tag>/<int:pk>/traffic/",
                "virtual-port-traffic",
            )
        ],
    ),
)

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
