from django.utils.translation import gettext_lazy as _

IXF_MEMBER_TYPE = (
    ("peering", _("peering")),
    ("ixp", _("ixp")),
    ("routeserver", _("routeserver")),
    ("probono", _("probono")),
)

ARS_TYPES = (
    ("bird", _("Bird")),
    ("bird2", _("Bird 2")),
    ("openbgpd", _("OpenBGPD")),
)

ARS_NO_EXPORT_ACTIONS = (
    ("pass", _("Pass (Treat as transitive)")),
    ("strip", _("Strip (Treat as non-transitive)")),
)

PERMISSION_REQUEST_TYPES = (
    ("net_ix", _("Manage network at exchange")),
)

IXF_EXPORT_PRIVACY_TYPES = (
    ("public", _("IX-F export feed is public")),
    ("private", _("IX-F export feed requires secret key to view")),
)
