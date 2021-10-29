from fullctl.django.rest.decorators import grainy_endpoint
from fullctl.django.rest.route.service_bridge import route
from fullctl.django.rest.views.service_bridge import (
    DataViewSet,
    HeartbeatViewSet,
    MethodFilter,
    StatusViewSet,
)
from rest_framework.decorators import action
from rest_framework.response import Response

import django_ixctl.models.ixctl as models
from django_ixctl.rest.serializers.service_bridge import Serializers


@route
class Status(StatusViewSet):
    checks = ("bridge_peerctl", "bridge_aaactl", "bridge_pdbctl")


@route
class Heartbeat(HeartbeatViewSet):
    pass


@route
class InternetExchange(DataViewSet):

    path_prefix = "/data"
    allowed_http_methods = ["GET"]
    valid_filters = [
        ("org", "org_id"),
        ("q", "name__icontains"),
        ("sot", "source_of_truth"),
    ]
    autocomplete = "name"
    allow_unfiltered = True

    queryset = models.InternetExchange.objects.filter(status="ok")
    serializer_class = Serializers.ix


@route
class InternetExchangeMember(DataViewSet):

    path_prefix = "/data"
    allowed_http_methods = ["GET"]
    valid_filters = [
        ("ix", "ix_id"),
        ("asn", "asn"),
        ("asns", "asn__in"),
        ("peers", MethodFilter("peers")),
        ("sot", MethodFilter("sot")),
    ]

    join_xl = {"ix": ("ix",)}

    queryset = models.InternetExchangeMember.objects.filter(status="ok")
    serializer_class = Serializers.member

    def filter_peers(self, qset, value):
        member = self.get_queryset().filter(id=value).first()
        return qset.filter(ix_id=member.ix_id, status="ok").exclude(id=value)

    def filter_sot(self, qset, value):
        return qset.filter(ix__source_of_truth=True).exclude(
            ix__pdb_id__isnull=True, ix__pdb_id=0
        )

    @action(detail=True, methods=["PUT"], url_path="sync/mac-address")
    @grainy_endpoint(namespace="service_bridge")
    def mac_address(self, request, pk, *args, **kwargs):
        member = self.get_object()
        mac_address = request.data.get("mac_address")
        member.macaddr = mac_address
        member.save()
        return Response(Serializers.member(instance=member).data)

    @action(detail=False, methods=["PUT"], url_path="sync/as-macro")
    @grainy_endpoint(namespace="service_bridge")
    def as_macro(self, request, *args, **kwargs):
        as_macro = request.data.get("as_macro")
        asn = request.data.get("asn")

        members = models.InternetExchangeMember.objects.filter(
            ix__source_of_truth=True, asn=asn
        )

        members.update(as_macro=as_macro)

        return Response(Serializers.member(instance=members, many=True).data)
