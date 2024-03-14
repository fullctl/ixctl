from django.contrib import admin
from django.forms import ModelForm
from fullctl.django.admin import BaseAdmin, BaseTabularAdmin

from django_ixctl.models import (
    InternetExchange,
    InternetExchangeMember,
    InternetExchangePrefix,
    Network,
    PermissionRequest,
    Routeserver,
    RouteserverConfig,
)

# from fullctl.django.models.concrete import OrganizationUser


class MemberForm(ModelForm):
    def clean_macaddr(self):
        macaddr = self.cleaned_data["macaddr"]
        if not macaddr:
            return None
        return macaddr

    def clean_ipaddr4(self):
        ipaddr4 = self.cleaned_data["ipaddr4"]
        if not ipaddr4:
            return None
        return ipaddr4

    def clean_ipaddr6(self):
        ipaddr6 = self.cleaned_data["ipaddr6"]
        if not ipaddr6:
            return None
        return ipaddr6


class InternetExchangeMemberInline(BaseTabularAdmin):
    model = InternetExchangeMember
    form = MemberForm


class RouteserverInline(BaseTabularAdmin):
    model = Routeserver


class PrefixInline(admin.TabularInline):
    model = InternetExchangePrefix
    extra = 0


@admin.register(InternetExchange)
class InternetInternetExchangeAdmin(BaseAdmin):
    list_display = ("name", "id", "org", "source_of_truth")
    list_filter = ("source_of_truth",)
    readonly_fields = ("org",)
    search_fields = ("name", "instance__org__slug", "instance__org__name")

    inlines = (PrefixInline,)

    def org(self, obj):
        return obj.instance.org


@admin.register(InternetExchangeMember)
class MemberAdmin(BaseAdmin):
    list_display = ("ix", "org", "asn", "ipaddr4", "ipaddr6", "port")
    readonly_fields = ("org",)
    search_fields = (
        "ix__name",
        "ix__instance__org__slug",
        "ix__instance__org__name",
        "ipaddr4",
        "ipaddr6",
    )
    form = MemberForm

    def org(self, obj):
        return obj.ix.instance.org


@admin.register(Routeserver)
class RouteserverAdmin(BaseAdmin):
    list_display = ("ix", "org", "asn", "router_id", "name")
    readonly_fields = ("org",)
    search_fields = (
        "ix__name",
        "ix__instance__org__slug",
        "ix__instance__org__name",
        "router_id",
        "name",
    )

    def org(self, obj):
        return obj.ix.instance.org


@admin.register(RouteserverConfig)
class RouteserverConfigAdmin(BaseAdmin):
    list_display = ("routeserver", "created", "updated", "generated")


@admin.register(Network)
class NetworkAdmin(BaseAdmin):
    list_display = ("asn", "name", "created", "updated", "org")
    readonly_fields = ("org",)

    def org(self, obj):
        if obj.instance:
            return obj.instance.org
        return "<orphan>"


@admin.register(PermissionRequest)
class PermissionRequestAdmin(BaseAdmin):
    list_display = ("org", "user", "created", "type")
