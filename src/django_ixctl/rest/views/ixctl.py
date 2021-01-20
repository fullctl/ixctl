import re
from django.utils.translation import gettext_lazy as _

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.schemas.openapi import AutoSchema


from fullctl.django.rest.core import BadRequest
from fullctl.django.rest.filters import CaseInsensitiveOrderingFilter
from fullctl.django.rest.renderers import PlainTextRenderer
from fullctl.django.rest.api_schema import PeeringDBImportSchema
from fullctl.django.util import verified_asns

from django_ixctl.peeringdb import import_org
from django_ixctl.rest.serializers.ixctl import Serializers
import django_ixctl.models as models
from django_ixctl.rest.route.ixctl import route


from django_ixctl.rest.decorators import grainy_endpoint
from fullctl.django.rest.decorators import load_object


@route
class InternetExchange(viewsets.GenericViewSet):
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

    @grainy_endpoint(namespace="ix.{request.org.permission_id}")
    def create(self, request, org, instance, *args, **kwargs):
        data = request.data
        data["pdb_id"] = None
        serializer = Serializers.ix(data=data)
        if not serializer.is_valid():
            return BadRequest(serializer.errors)
        ix = serializer.save()
        ix.instance = instance
        ix.save()
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
    @grainy_endpoint(namespace="ix.{request.org.permission_id}.{ix.pk}")
    def update(self, request, org, ix, instance, *args, **kwargs):
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

    @action(detail=False, methods=["POST"], schema=PeeringDBImportSchema())
    @grainy_endpoint(namespace="ix.{request.org.permission_id}")
    def import_peeringdb(self, request, org, instance, *args, **kwargs):
        serializer = Serializers.impix(
            data=request.data,
            context={"instance": instance},
        )

        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        ix = serializer.save()

        return Response(Serializers.ix(instance=ix).data)


@route
class Member(viewsets.GenericViewSet):
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

        queryset = models.InternetExchangeMember.objects.filter(
            ix=ix, ix__instance=instance
        ).select_related("ix", "ix__instance")

        queryset = ordering_filter.filter_queryset(request, queryset, self)

        serializer = Serializers.member(
            instance=queryset,
            many=True,
        )

        return Response(serializer.data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @grainy_endpoint(
        namespace="member.{request.org.permission_id}.{ix.pk}.?",
        handlers={"*": {"key": lambda row, idx: row["asn"]}},
    )
    def create(self, request, org, instance, ix, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=ix.pk).id
        serializer = Serializers.member(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        member = serializer.save()

        return Response(Serializers.member(instance=member).data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @load_object("member", models.InternetExchangeMember, id="member_id")
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

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @load_object("member", models.InternetExchangeMember, id="member_id")
    @grainy_endpoint(
        namespace="member.{request.org.permission_id}.{ix.pk}.{member.asn}.?",
    )
    def destroy(self, request, org, instance, ix, member_id, *args, **kwargs):
        ix = models.InternetExchange.objects.get(instance=instance, id=ix.pk)
        member = models.InternetExchangeMember.objects.get(ix=ix, id=member_id)
        member.delete()
        member.id = request.data.get("id")
        return Response(Serializers.member(instance=member).data)


@route
class Routeserver(viewsets.GenericViewSet):

    serializer_class = Serializers.rs
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

        serializer = Serializers.rs(
            instance=models.Routeserver.objects.filter(
                ix_id=ix.pk, ix__instance=instance
            ).order_by("name"),
            many=True,
        )

        return Response(serializer.data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @grainy_endpoint(
        namespace="rs.{request.org.permission_id}.{ix.pk}.?",
        handlers={"*": {"key": lambda row, idx: row["asn"]}},
    )
    def create(self, request, org, instance, ix, *args, **kwargs):
        data = request.data
        data["ix"] = models.InternetExchange.objects.get(instance=instance, id=ix.pk).id
        serializer = Serializers.rs(data=data, context={"instance": instance})
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        routeserver = serializer.save()

        return Response(Serializers.rs(instance=routeserver).data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @grainy_endpoint(
        namespace="rs.{request.org.permission_id}.{ix.pk}.{rs_id}",
    )
    def update(self, request, org, instance, ix, rs_id, *args, **kwargs):
        routeserver = models.Routeserver.objects.get(
            ix__instance=instance, ix_id=ix.pk, id=rs_id
        )
        serializer = Serializers.rs(
            data=request.data, instance=routeserver, context={"instance": instance}
        )
        if not serializer.is_valid():
            return BadRequest(serializer.errors)

        routeserver = serializer.save()

        return Response(Serializers.rs(instance=routeserver).data)

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @grainy_endpoint(
        namespace="rs.{request.org.permission_id}.{ix.pk}.{rs_id}",
    )
    def destroy(self, request, org, instance, ix, rs_id, *args, **kwargs):
        ix = models.InternetExchange.objects.get(instance=instance, id=ix.pk)
        routeserver = models.Routeserver.objects.get(ix=ix, id=rs_id)
        routeserver.delete()
        routeserver.id = request.data.get("id")
        return Response(Serializers.rs(instance=routeserver).data)


@route
class RouteserverConfig(viewsets.GenericViewSet):
    serializer_class = Serializers.rsconf
    queryset = models.RouteserverConfig.objects.all()
    lookup_value_regex = "[^\/]+"
    lookup_url_kwarg = "name"
    lookup_field = "rs__name"
    ref_tag = "rsconf"
    ix_tag_needed = True

    @load_object("ix", models.InternetExchange, slug="ix_tag")
    @grainy_endpoint(
        namespace="rsconf.{request.org.permission_id}",
    )
    def retrieve(self, request, org, instance, ix, name, *args, **kwargs):
        rs_config = models.RouteserverConfig.objects.get(
                rs__ix=ix, rs__name=name
        )
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
        rs_config = models.RouteserverConfig.objects.get(
                rs__ix=ix, rs__name=name
        )
        serializer = Serializers.rsconf(
            instance=rs_config,
            many=False,
        )
        # return Response(serializer.instance.body)
        return Response(serializer.instance.body)


@route
class Network(viewsets.GenericViewSet):
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

    @action(detail=False, methods=["GET"], url_path="presence/(?P<asn>[\d]+)")
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
class PermissionRequest(viewsets.GenericViewSet):

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
