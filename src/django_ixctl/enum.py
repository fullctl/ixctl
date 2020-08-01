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


