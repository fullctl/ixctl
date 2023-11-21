from django.db.models import Q
from django_filters import rest_framework as filters
from netfields import InetAddressField

from django_ixctl.models.ixctl import InternetExchangeMember


class InternetExchangeMemberFilter(filters.FilterSet):
    has_md5 = filters.BooleanFilter(method="filter_has_md5")

    class Meta:
        model = InternetExchangeMember
        fields = {
            "ix": ["exact"],
            "asn": ["exact"],
            "ipaddr4": ["exact"],
            "ipaddr6": ["exact"],
        }
        filter_overrides = {
            InetAddressField: {
                "filter_class": filters.CharFilter,
                "extra": lambda f: {
                    "lookup_expr": "icontains",
                },
            },
        }

    def filter_has_md5(self, queryset, name, value):
        if value:
            return queryset.exclude(Q(md5__isnull=True) | Q(md5__exact=""))
        else:
            return queryset.filter(Q(md5__isnull=True) | Q(md5__exact=""))
