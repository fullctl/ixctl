from django.conf import settings
from fullctl.django.rest.urls.service_bridge import proxy_api, setup

# set up service bridges

# AAACTL

if getattr(settings, "AAACTL_URL", None):
    setup(
        "aaactl",
        proxy_api(
            "aaactl",
            settings.AAACTL_URL,
            [
                ("billing/org/{org_tag}/services/", "billing/<org_tag>/services/"),
                ("billing/org/{org_tag}/subscribe/", "billing/<org_tag>/subscribe/"),
            ],
        ),
    )

# DEVICECTL

if getattr(settings, "DEVICECTL_URL", None):
    setup(
        "devicectl",
        proxy_api(
            "devicectl",
            settings.DEVICECTL_URL,
            [
                ("device/{org_tag}", "device/{org_tag}"),
            ],
        ),
    )
