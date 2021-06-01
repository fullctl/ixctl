from fullctl.django.rest.api_schema import PeeringDBImportSchema
from fullctl.django.rest.core import BadRequest
from fullctl.django.rest.decorators import load_object, billable
from fullctl.django.rest.mixins import CachedObjectMixin, OrgQuerysetMixin
from fullctl.django.rest.filters import CaseInsensitiveOrderingFilter
from fullctl.django.rest.renderers import PlainTextRenderer
from fullctl.django.auditlog import auditlog

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
        serializer = Serializers.ix(data=data)
        if not serializer.is_valid():
            return BadRequest(serializer.errors)
        ix = serializer.save()
        ix.instance = instance
        ix.save()

        auditlog.log("ix:create", log_object=ix, **data)

        return Response(Serializers.ix(instance=ix).data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @grainy_endpoint(namespace="ix.{request.org.permission_id}.{ix.pk}")
    def retrieve(self, request, org, ix, instance, *args, **kwargs):
        serializer = Serializers.ix(
            instance=ix,
            many=False,
        )
        return Response(serializer.data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
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

        auditlog.log("ix:update", log_object=ix, **request.data)

        return Response(Serializers.ix(instance=ix).data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @auditlog()
    @grainy_endpoint(namespace="ix.{request.org.permission_id}.{ix.pk}")
    def destroy(self, request, org, ix, instance, auditlog=None, *args, **kwargs):
        ix.delete()
        ix.id = request.data.get("id")
        auditlog.log("ix:delete", log_object=ix, **request.data)
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

        for member in ix.member_set.all():
            auditlog.log(
                "member:import",
                log_object=member,
                ix_id=member.ix_id,
                pdb_id=member.pdb_id,
            )

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

    @load_object("ix", models.InternetExchange, slug="ix_tag")
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

        serializer = Serializers.member(
            instance=queryset,
            many=True,
        )

        return Response(serializer.data)

    @billable("fullctl.ixctl.members")
    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @auditlog()
    @grainy_endpoint(
        namespace="member.{request.org.permission_id}.{ix.pk}.?",
        handlers={"*": {"key": lambda row, idx: row["asn"]}},
    )
    def create(self, request, org, instance, ix, auditlog=None, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=ix.pk).id
        serializer = Serializers.member(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        auditlog.log("member:create", log_object=member, **data)

        return Response(Serializers.member(instance=member).data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @load_object("member", models.InternetExchangeMember, id="member_id")
    @auditlog()
    @grainy_endpoint(
        namespace="member.{request.org.permission_id}.{ix.pk}.{member.asn}.?",
    )
    def update(
        self, request, org, instance, ix, member, auditlog=None, *args, **kwargs
    ):
        serializer = request.grainy_update_serializer(
            Serializers.member, member, context={"instance": instance}
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        auditlog.log("member:update", log_object=member, **request.data)

        return Response(Serializers.member(instance=member).data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @load_object("member", models.InternetExchangeMember, id="member_id")
    @auditlog()
    @grainy_endpoint(
        namespace="member.{request.org.permission_id}.{ix.pk}.{member.asn}",
    )
    def destroy(
        self, request, org, instance, ix, member, auditlog=None, *args, **kwargs
    ):
        member.delete()
        member.id = request.data.get("id")
        auditlog.log("member:delete", log_object=member, **request.data)
        return Response(Serializers.member(instance=member).data)


@route
class Routeserver(CachedObjectMixin, IxOrgQuerysetMixin, viewsets.GenericViewSet):

    serializer_class = Serializers.rs
    queryset = models.Routeserver.objects.all()
    ref_tag = "rs"
    ix_tag_needed = True
    lookup_url_kwarg = "rs_id"
    lookup_field = "id"

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @grainy_endpoint(
        namespace="rs.{request.org.permission_id}.{ix.pk}.?",
        handlers={"*": {"key": lambda row, idx: row["asn"]}},
    )
    def list(self, request, org, instance, ix, *args, **kwargs):
        queryset = self.get_queryset().order_by("name")
        serializer = Serializers.rs(
            instance=queryset,
            many=True,
        )

        return Response(serializer.data)

    @billable("fullctl.ixctl.routeservers")
    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @auditlog()
    @grainy_endpoint(
        namespace="rs.{request.org.permission_id}.{ix.pk}.?",
        handlers={"*": {"key": lambda row, idx: row["asn"]}},
    )
    def create(self, request, org, instance, ix, auditlog=None, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=ix.pk).id
        serializer = Serializers.rs(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        routeserver = serializer.save()

        auditlog.log("rs:create", log_object=routeserver, **request.data)

        return Response(Serializers.rs(instance=routeserver).data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @auditlog()
    @grainy_endpoint(
        namespace="rs.{request.org.permission_id}.{ix.pk}.{rs_id}",
    )
    def update(self, request, org, instance, ix, rs_id, auditlog=None, *args, **kwargs):
        routeserver = self.get_object()
        serializer = Serializers.rs(
            data=request.data, instance=routeserver, context={"instance": instance}
        )
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        routeserver = serializer.save()

        auditlog.log("rs:update", log_object=routeserver, **request.data)

        return Response(Serializers.rs(instance=routeserver).data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @auditlog()
    @grainy_endpoint(
        namespace="rs.{request.org.permission_id}.{ix.pk}.{rs_id}",
    )
    def destroy(
        self, request, org, instance, ix, rs_id, auditlog=None, *args, **kwargs
    ):
        routeserver = self.get_object()
        routeserver.delete()
        routeserver.id = request.data.get("id")

        auditlog.log("rs:delete", log_object=routeserver)

        return Response(Serializers.rs(instance=routeserver).data)


@route
class RouteserverConfig(CachedObjectMixin, IxOrgQuerysetMixin, viewsets.GenericViewSet):
    serializer_class = Serializers.rsconf
    queryset = models.RouteserverConfig.objects.all()
    lookup_value_regex = "[^\/]+"  # noqa: W605
    lookup_url_kwarg = "name"
    lookup_field = "rs__name"
    ref_tag = "rsconf"
    ix_tag_needed = True
    ix_lookup_field = "rs__ix"

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @grainy_endpoint(
        namespace="rsconf.{request.org.permission_id}",
    )
    def retrieve(self, request, org, instance, ix, name, *args, **kwargs):
        rs_config = self.get_object()
        serializer = Serializers.rsconf(
            instance=rs_config,
            many=False,
        )
        return Response(serializer.data)

    @action(detail=True, methods=["GET"], renderer_classes=[PlainTextRenderer])
    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @grainy_endpoint(
        namespace="rsconf.{request.org.permission_id}",
    )
    def plain(self, request, org, instance, ix, name, *args, **kwargs):
        rs_config = self.get_object()
        serializer = Serializers.rsconf(
            instance=rs_config,
            many=False,
        )
        # return Response(serializer.instance.body)
        return Response(serializer.instance.body)


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
        detail=False, methods=["GET"], url_path="presence/(?P<asn>[\d]+)"  # noqa: W605
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
