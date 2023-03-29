from django.db.models import Q
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
        ("ids", "id__in"),
        ("org", "org_id"),
        ("q", "name__icontains"),
        ("sot", "source_of_truth"),
        ("verified", "verified"),
        ("asns", "member_set__asn_in"),
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
        ("ix_verified", "ix__verified"),
        ("asn", "asn"),
        ("asns", "asn__in"),
        ("peers", MethodFilter("peers")),
        ("sot", MethodFilter("sot")),
        ("ip", MethodFilter("ip")),
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

    def filter_ip(self, qset, value):
        return qset.filter(Q(ipaddr4=value) | Q(ipaddr6=value))

    @action(
        detail=False,
        methods=["PUT"],
        url_path="sync/(?P<asn>[^/.]+)/(?P<ip>[^/]+)/mac-address",
    )
    @grainy_endpoint(namespace="service_bridge")
    def mac_address(self, request, asn, ip, *args, **kwargs):
        mac_address = request.data.get("mac_address")

        members = models.InternetExchangeMember.objects.filter(
            ix__verified=True, asn=asn, ipaddr4=ip
        )

        members.update(macaddr=mac_address)
        return Response(Serializers.member(instance=members, many=True).data)

    @action(detail=False, methods=["PUT"], url_path="sync/as-macro")
    @grainy_endpoint(namespace="service_bridge")
    def as_macro(self, request, *args, **kwargs):
        as_macro = request.data.get("as_macro")
        asn = request.data.get("asn")

        members = models.InternetExchangeMember.objects.filter(asn=asn)

        members.update(as_macro_override=as_macro)

        return Response(Serializers.member(instance=members, many=True).data)

    @action(
        detail=False,
        methods=["PUT"],
        url_path="sync/(?P<asn>[^/.]+)/(?P<member_ip>[^/]+)/(?P<router_ip>[^/]+)/md5",
    )
    @grainy_endpoint(namespace="service_bridge")
    def md5(self, request, asn, member_ip, router_ip, *args, **kwargs):
        md5 = request.data.get("md5")

        # find route servers at verified internet exchanges that
        # match the provided router ip

        route_servers = models.Routeserver.objects.filter(
            ix__verified=True, router_id=router_ip
        ).select_related("ix")

        members = []

        # update memember md5s using the member ip to identify them

        for rs in route_servers:
            try:
                member = rs.ix.member_set.get(
                    asn=asn, ipaddr4=member_ip, is_rs_peer=True
                )
                member.md5 = md5
                member.save()
                members.append(member)
            except models.InternetExchangeMember.DoesNotExist:
                continue

        return Response(Serializers.member(instance=members, many=True).data)
