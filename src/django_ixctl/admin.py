from django.contrib import admin
from django.utils.translation import gettext as _
from django_handleref.admin import VersionAdmin

from django_ixctl.models import (
    Organization,
    OrganizationUser,
    APIKey,
    InternetExchange,
    InternetExchangeMember,
    RouteserverConfig,
)


class BaseAdmin(VersionAdmin):
    readonly_fields = ("version",)


class BaseTabularAdmin(admin.TabularInline):
    readonly_fields = ("version",)


@admin.register(APIKey)
class APIKeyAdmin(BaseAdmin):
    list_display = ("id", "user", "key")


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


@admin.register(InternetExchange)
class InternetInternetExchangeAdmin(BaseAdmin):
    list_display = ("name", "id", "instance")
    inlines = (InternetExchangeMemberInline,)

@admin.register(RouteserverConfig)
class RouteserverConfigAdmin(BaseAdmin):
    list_display = ("rs", "created", "updated", "generated")

