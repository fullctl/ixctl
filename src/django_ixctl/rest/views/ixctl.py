import fullctl.service_bridge.aaactl as aaactl
import fullctl.service_bridge.pdbctl as pdbctl
from django.conf import settings
from fullctl.django.auditlog import auditlog
from fullctl.django.rest.api_schema import PeeringDBImportSchema
from fullctl.django.rest.core import BadRequest
from fullctl.django.rest.decorators import load_object
from fullctl.django.rest.filters import CaseInsensitiveOrderingFilter
from fullctl.django.rest.mixins import CachedObjectMixin, OrgQuerysetMixin
from fullctl.django.rest.renderers import PlainTextRenderer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import django_ixctl.models as models
from django_ixctl.rest.decorators import grainy_endpoint
from django_ixctl.rest.route.ixctl import route
from django_ixctl.rest.serializers.ixctl import Serializers


class IxOrgQuerysetMixin:
    """
    For objects with URLs that require a "ix_tag" and "org_tag", this filters
    the resulting queryset by matching the org slug and ix slug to the url
    tags.

    Set the 'ix_lookup_field' attribute on the Viewset if the model for the viewset
    does not have an IX attribute, but has a related object with a IX attribute.

    E.g., RouteserverConfig.rs.ix
    """

    def get_queryset(self):
        org_tag = self.kwargs["org_tag"]
        ix_tag = self.kwargs["ix_tag"]
        ix_lookup_field = getattr(self, "ix_lookup_field", "ix")

        filters = {
            f"{ix_lookup_field}__slug": ix_tag,
            f"{ix_lookup_field}__instance__org__slug": org_tag,
        }

        return self.queryset.filter(**filters)


@route
class InternetExchange(CachedObjectMixin, OrgQuerysetMixin, viewsets.GenericViewSet):
    """
    retrieve:
        Return a internet exchange instance.

    list:
        Return all internet exchanges.

    create:
        Create a new internet exchange.

    import_peeringdb:
        Import an internet exhange from Peeringdb.

    update:
        Update an intenet exchange.
    """

    serializer_class = Serializers.ix
    queryset = models.InternetExchange.objects.all()
    ref_tag = "ix"
    lookup_url_kwarg = "ix_tag"
    lookup_field = "slug"

    @grainy_endpoint(namespace="ix.{request.org.permission_id}")
    def list(self, request, org, instance, *args, **kwargs):
        serializer = Serializers.ix(
            instance=models.InternetExchange.objects.filter(instance=instance),
            many=True,
        )
        return Response(serializer.data)

    @auditlog()
    @grainy_endpoint(namespace="ix.{request.org.permission_id}")
    def create(self, request, org, instance, auditlog=None, *args, **kwargs):
        data = request.data
        data["pdb_id"] = None
        data["instance"] = instance.id
        serializer = Serializers.ix(data=data)
        if not serializer.is_valid():
            return BadRequest(serializer.errors)
        ix = serializer.save()

        return Response(Serializers.ix(instance=ix).data)

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @grainy_endpoint(namespace="ix.{request.org.permission_id}.{ix.pk}")
    def retrieve(self, request, org, ix, instance, *args, **kwargs):
        serializer = Serializers.ix(
            instance=ix,
            many=False,
        )
        return Response(serializer.data)

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @auditlog()
    @grainy_endpoint(namespace="ix.{request.org.permission_id}.{ix.pk}")
    def update(self, request, org, ix, instance, auditlog=None, *args, **kwargs):
        serializer = Serializers.ix(
            ix,
            data=request.data,
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)
        ix = serializer.save()
        ix.instance = instance
        ix.save()

        return Response(Serializers.ix(instance=ix).data)

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @auditlog()
    @grainy_endpoint(namespace="ix.{request.org.permission_id}.{ix.pk}")
    def destroy(self, request, org, ix, instance, auditlog=None, *args, **kwargs):
        ix.delete()
        ix.id = request.data.get("id")
        return Response(Serializers.ix(instance=ix).data)

    @action(detail=False, methods=["POST"], schema=PeeringDBImportSchema())
    @auditlog()
    @grainy_endpoint(namespace="ix.{request.org.permission_id}")
    def import_peeringdb(self, request, org, instance, auditlog=None, *args, **kwargs):
        serializer = Serializers.impix(
            data=request.data,
            context={"instance": instance},
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        ix = serializer.save()

        auditlog.log("ix:import", log_object=ix, **request.data)

        return Response(Serializers.ix(instance=ix).data)


@route
class Member(CachedObjectMixin, IxOrgQuerysetMixin, viewsets.GenericViewSet):
    """
    list:
        Return all member instances.

    create:
        Create a new member.

    update:
        Update a member.

    delete:
        Delete a member.
    """

    serializer_class = Serializers.member
    ref_tag = "member"
    queryset = models.InternetExchangeMember.objects.all()
    lookup_url_kwarg = "member_id"
    lookup_field = "id"
    ix_tag_needed = True

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @grainy_endpoint(
        namespace="member.{request.org.permission_id}.{ix.pk}.?",
        handlers={"*": {"key": lambda row, idx: row["asn"]}},
    )
    def list(self, request, org, instance, ix, *args, **kwargs):
        ordering_filter = CaseInsensitiveOrderingFilter(
            ["name", "asn", "ipaddr4", "ipaddr6", "speed"]
        )

        queryset = self.get_queryset().select_related("ix", "ix__instance")

        queryset = ordering_filter.filter_queryset(request, queryset, self)

        members = models.InternetExchangeMember.preload_as_macro(queryset)

        serializer = Serializers.member(
            instance=members,
            many=True,
        )

        return Response(serializer.data)

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @auditlog()
    @grainy_endpoint(
        namespace="member.{request.org.permission_id}.{ix.pk}.?",
        handlers={"*": {"key": lambda row, idx: row["asn"]}},
    )
    def create(self, request, org, instance, ix, *args, **kwargs):
        # retrieve max. memmbers count according
        # to active ixctl plan for org

        max_members = aaactl.OrganizationProduct().get_product_property(
            "ixctl", org.slug, "members"
        )

        num_members = ix.member_set.all().count()

        if num_members + 1 > max_members:
            return BadRequest(
                {
                    "non_field_errors": [
                        f"You have reached the limit of allowed networks ({max_members}). "
                        "Please upgrade your ixCtl subscription to add additional networks."
                        f"You can contact us at {settings.SUPPORT_EMAIL} for further information"
                    ]
                }
            )

        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=ix.pk).id
        serializer = Serializers.member(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        return Response(Serializers.member(instance=member).data)

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @load_object("member", models.InternetExchangeMember, ix="ix", id="member_id")
    @auditlog()
    @grainy_endpoint(
        namespace="member.{request.org.permission_id}.{ix.pk}.{member.asn}.?",
    )
    def update(self, request, org, instance, ix, member, *args, **kwargs):
        serializer = request.grainy_update_serializer(
            Serializers.member, member, context={"instance": instance}
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        return Response(Serializers.member(instance=member).data)

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @load_object("member", models.InternetExchangeMember, ix="ix", id="member_id")
    @auditlog()
    @grainy_endpoint(
        namespace="member.{request.org.permission_id}.{ix.pk}.{member.asn}",
    )
    def destroy(self, request, org, instance, ix, member, *args, **kwargs):
        r = Response(Serializers.member(instance=member).data)
        member.delete()
        return r


@route
class Routeserver(CachedObjectMixin, IxOrgQuerysetMixin, viewsets.GenericViewSet):
    serializer_class = Serializers.routeserver
    queryset = models.Routeserver.objects.all()
    ref_tag = "routeserver"
    ix_tag_needed = True
    lookup_url_kwarg = "routeserver_id"
    lookup_field = "id"

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @grainy_endpoint(
        namespace="routeserver.{request.org.permission_id}.{ix.pk}.?",
        handlers={"*": {"key": lambda row, idx: row["asn"]}},
    )
    def list(self, request, org, instance, ix, *args, **kwargs):
        queryset = self.get_queryset().order_by("name")
        ordering_filter = CaseInsensitiveOrderingFilter(["name", "asn", "router_id"])
        queryset = ordering_filter.filter_queryset(request, queryset, self)

        serializer = Serializers.routeserver(
            instance=queryset,
            many=True,
        )

        return Response(serializer.data)

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @auditlog()
    @grainy_endpoint(
        namespace="routeserver.{request.org.permission_id}.{ix.pk}.?",
        handlers={"*": {"key": lambda row, idx: row["asn"]}},
    )
    def create(self, request, org, instance, ix, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=ix.pk).id
        serializer = Serializers.routeserver(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        routeserver = serializer.save()

        return Response(Serializers.routeserver(instance=routeserver).data)

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @load_object("routeserver", models.Routeserver, ix="ix", id="routeserver_id")
    @auditlog()
    @grainy_endpoint(
        namespace="routeserver.{request.org.permission_id}.{ix.pk}.{routeserver_id}",
    )
    def update(self, request, org, instance, ix, routeserver, *args, **kwargs):
        serializer = Serializers.routeserver(
            data=request.data, instance=routeserver, context={"instance": instance}
        )
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        routeserver = serializer.save()

        return Response(Serializers.routeserver(instance=routeserver).data)

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @load_object("routeserver", models.Routeserver, ix="ix", id="routeserver_id")
    @auditlog()
    @grainy_endpoint(
        namespace="routeserver.{request.org.permission_id}.{ix.pk}.{routeserver_id}",
    )
    def destroy(self, request, org, instance, ix, routeserver, *args, **kwargs):
        r = Response(Serializers.routeserver(instance=routeserver).data)
        routeserver.delete()
        return r


@route
class RouteserverConfig(CachedObjectMixin, IxOrgQuerysetMixin, viewsets.GenericViewSet):
    serializer_class = Serializers.config__routeserver
    queryset = models.RouteserverConfig.objects.all()
    lookup_value_regex = r"[^\/]+"  # noqa: W605
    lookup_url_kwarg = "name"
    lookup_field = "routeserver__name"
    ref_tag = "config/routeserver"
    ix_tag_needed = True
    ix_lookup_field = "routeserver__ix"

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @grainy_endpoint(
        namespace="config.routeserver.{request.org.permission_id}",
    )
    def retrieve(self, request, org, instance, ix, name, *args, **kwargs):
        rs_config = models.RouteserverConfig.objects.get(
            routeserver__name=name, routeserver__ix=ix
        )
        if request.method == "OPTIONS":
            return self._options(request, rs_config)

        serializer = Serializers.config__routeserver(
            instance=rs_config,
            many=False,
        )
        return Response(serializer.data)

    @action(
        detail=True, methods=["GET", "OPTIONS"], renderer_classes=[PlainTextRenderer]
    )
    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @grainy_endpoint(
        namespace="config.routeserver.{request.org.permission_id}",
    )
    def plain(self, request, org, instance, ix, name, *args, **kwargs):
        rs_config = models.RouteserverConfig.objects.get(
            routeserver__name=name, routeserver__ix=ix
        )

        if request.method == "OPTIONS":
            return self._options(request, rs_config)

        serializer = Serializers.config__routeserver(
            instance=rs_config,
            many=False,
        )
        # return Response(serializer.instance.body)
        return Response(serializer.instance.body)

    @action(detail=True, methods=["POST"])
    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @grainy_endpoint(
        namespace="config.routeserver.{request.org.permission_id}",
    )
    def status(self, request, org, instance, ix, name, *args, **kwargs):
        rs_config = self.get_object()
        rs_config.rs_response = request.data
        rs_config.save()
        serializer = Serializers.config__routeserver(
            instance=rs_config,
            many=False,
        )
        return Response(serializer.data)

    def _options(self, request, rs_config):
        response = Response(self.metadata_class().determine_metadata(request, self))
        response.headers["Last-Modified"] = rs_config.generated.strftime(
            "%a, %d %b %Y %H:%M:%S GMT"
        )
        return response


@route
class PeeringDBRouteservers(
    CachedObjectMixin, IxOrgQuerysetMixin, viewsets.GenericViewSet
):
    serializer_class = Serializers.pdbrouteserver
    queryset = models.Routeserver.objects.all()
    ix_tag_needed = True
    ref_tag = "pdbrouteserver"

    @load_object("ix", models.InternetExchange, instance="instance", slug="ix_tag")
    @grainy_endpoint(namespace="routeserver.{request.org.permission_id}")
    def list(self, request, org, instance, ix, *args, **kwargs):
        if not ix.pdb_id:
            return Response(self.serializer_class([], many=True).data)
        candidates = list(pdbctl.NetworkIXLan().objects(ix=ix.pdb_id, routeserver=1))
        return Response(self.serializer_class(candidates, many=True).data)


@route
class Network(CachedObjectMixin, OrgQuerysetMixin, viewsets.GenericViewSet):
    serializer_class = Serializers.net
    queryset = models.Network.objects.all()

    lookup_url_kwarg = "asn"
    lookup_field = "asn"

    @grainy_endpoint(namespace="net.{request.org.permission_id}")
    def list(self, request, org, instance, *args, **kwargs):
        serializer = Serializers.net(
            instance.net_set.all(),
            many=True,
        )
        return Response(serializer.data)

    @action(
        detail=False, methods=["GET"], url_path=r"presence/(?P<asn>[\d]+)"  # noqa: W605
    )
    @grainy_endpoint(namespace="net.{request.org.permission_id}.{asn}")
    @load_object("net", models.Network, asn="asn", instance="instance")
    def presence(self, request, org, instance, asn, net=None, *args, **kwargs):
        serializer = Serializers.presence(
            net.members,
            many=True,
            context={"perms": request.perms, "user": request.user},
        )
        return Response(serializer.data)


@route
class PermissionRequest(CachedObjectMixin, viewsets.GenericViewSet):
    serializer_class = Serializers.permreq
    queryset = models.PermissionRequest.objects.all()

    @grainy_endpoint()
    def list(self, request, org, *args, **kwargs):
        serializer = Serializers.permreq(
            org.permreq_set.all(),
            many=True,
            context={
                "user": request.user,
                "perms": request.perms,
            },
        )
        return Response(serializer.data)

    """
    @grainy_endpoint(namespace="?.?")
    def create(self, request, org, instance, *args, **kwargs):
        data = request.data
        data["user"] = request.user.id
        data["org"] = org.id
        serializer = Serializers.permreq(data=data)

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        permreq = serializer.save()
        return Response(serializer.data)
    """
