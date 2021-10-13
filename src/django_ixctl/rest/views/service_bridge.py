from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from fullctl.django.rest.core import BadRequest
from fullctl.django.rest.decorators import load_object
from fullctl.django.rest.route.service_bridge import route
from fullctl.django.rest.views.service_bridge import DataViewSet, MethodFilter, Exclude
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

import django_ixctl.models.ixctl as models

from django_ixctl.rest.decorators import grainy_endpoint
from django_ixctl.rest.serializers.service_bridge import Serializers


@route
class InternetExchange(DataViewSet):

    path_prefix = "/data"
    allowed_http_methods = ["GET"]
    valid_filters = [
        ("org", "org_id"),
        ("q", "name__icontains"),
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
        ("ix", "ixlan_id"),
        ("net", "net_id"),
        ("asn", "net__asn"),
        ("asns", "net__asn__in"),
        ("peers", MethodFilter("peers")),
    ]

    join_xl = {"ix": ("ixlan", "ixlan__ix")}

    queryset = models.InternetExchangeMember.objects.filter(status="ok")
    serializer_class = Serializers.member

    def filter_peers(self, qset, value):
        member = self.get_queryset().filter(id=value).first()
        return qset.filter(ixlan_id=member.ixlan_id, status="ok").exclude(id=value)
