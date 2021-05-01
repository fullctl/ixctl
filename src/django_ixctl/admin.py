from django.contrib import admin
from django_handleref.admin import VersionAdmin
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


class BaseAdmin(VersionAdmin):
    readonly_fields = ("version",)


class BaseTabularAdmin(admin.TabularInline):
    readonly_fields = ("version",)


class OrganizationUserInline(admin.TabularInline):
    model = OrganizationUser
    extra = 0
    fields = ("status", "user")


@admin.register(Organization)
class OrganizationAdmin(BaseAdmin):
    list_display = ("id", "name", "slug")
    inlines = (OrganizationUserInline,)


class InternetExchangeMemberInline(BaseTabularAdmin):
    model = InternetExchangeMember


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
        return obj.instance.org


@admin.register(PermissionRequest)
class PermissionRequestAdmin(BaseAdmin):
    list_display = ("org", "user", "created", "type")
