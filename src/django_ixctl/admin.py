from django.contrib import admin
from django.forms import ModelForm
from fullctl.django.admin import BaseAdmin, BaseTabularAdmin
from fullctl.django.models.concrete import OrganizationUser

from django_ixctl.models import (
    InternetExchange,
    InternetExchangeMember,
    Network,
    Organization,
    PermissionRequest,
    Routeserver,
    RouteserverConfig,
)


class OrganizationUserInline(admin.TabularInline):
    model = OrganizationUser
    extra = 0
    fields = ("status", "user")


@admin.register(Organization)
class OrganizationAdmin(BaseAdmin):
    list_display = ("id", "name", "slug")
    inlines = (OrganizationUserInline,)


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


@admin.register(InternetExchange)
class InternetInternetExchangeAdmin(BaseAdmin):
    list_display = ("name", "id", "org")
    readonly_fields = ("org",)
    inlines = (InternetExchangeMemberInline, RouteserverInline)

    def org(self, obj):
        return obj.instance.org


@admin.register(RouteserverConfig)
class RouteserverConfigAdmin(BaseAdmin):
    list_display = ("rs", "created", "updated", "generated")


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
