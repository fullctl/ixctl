from django.conf import settings
from fullctl.django.rest.urls.service_bridge import setup, proxy_api

# set up service bridges

# AAACTL

if getattr(settings, "AAACTL_HOST", None):
    setup(
        "aaactl",
        proxy_api(
            "aaactl",
            settings.AAACTL_HOST,
            [
                ("billing/org/{org_tag}/services/", "billing/<org_tag>/services/"),
                ("billing/org/{org_tag}/subscribe/", "billing/<org_tag>/subscribe/"),
            ],
        ),
    )

# DEVICECTL

if getattr(settings, "DEVICECTL_HOST", None):
    setup(
        "devicectl",
        proxy_api(
            "devicectl",
            settings.DEVICECTL_HOST,
            [
                ("device/{org_tag}", "device/{org_tag}"),
            ],
        ),
    )
