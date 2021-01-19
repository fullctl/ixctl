from django.urls import path, include
from django_ixctl.rest.views.ixctl import InternetExchange, Member, Routeserver
import django_ixctl.rest.route.ixctl

ix_list = InternetExchange.as_view({"get": "list", "post": "create"})

ix_detail = InternetExchange.as_view(
    {
        "get": "retrieve",
    }
)

ix_import_peeringdb = InternetExchange.as_view(
    {
        "post": "import_peeringdb",
    }
)

member_list = Member.as_view({"get": "list", "post": "create"})

member_detail = Member.as_view(
    {
        "put": "update",
        "delete": "destroy",
    }
)

rs_list = Routeserver.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

rs_detail = Routeserver.as_view(
    {
        "put": "update",
        "delete": "destroy",
    }
)

urlpatterns = [
    path(
        f"{InternetExchange.ref_tag}/<str:org_tag>/",
        ix_list,
        name=f"{InternetExchange.ref_tag}-list",
    ),
    path(
        f"{InternetExchange.ref_tag}/<str:org_tag>/import_peeringdb",
        ix_import_peeringdb,
        name=f"{InternetExchange.ref_tag}-import-peeringdb",
    ),
    path(
        f"{InternetExchange.ref_tag}/<str:org_tag>/<str:ix_tag>/",
        ix_detail,
        name=f"{InternetExchange.ref_tag}-detail",
    ),
    path(
        f"{Member.ref_tag}/<str:org_tag>/<str:ix_tag>/",
        member_list,
        name=f"{Member.ref_tag}-list",
    ),
    path(
        f"{Member.ref_tag}/<str:org_tag>/<str:ix_tag>/<int:member_id>",
        member_detail,
        name=f"{Member.ref_tag}-detail",
    ),
    path(
        f"{Routeserver.ref_tag}/<str:org_tag>/<str:ix_tag>/",
        rs_list,
        name=f"{Routeserver.ref_tag}-list",
    ),
    path(
        f"{Routeserver.ref_tag}/<str:org_tag>/<str:ix_tag>/<int:rs_id>",
        rs_detail,
        name=f"{Routeserver.ref_tag}-detail",
    ),
    path("<str:org_tag>/", include(django_ixctl.rest.route.ixctl.router.urls)),
]
