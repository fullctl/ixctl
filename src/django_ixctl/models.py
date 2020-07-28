from secrets import token_urlsafe

from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _

import reversion

from django_handleref.models import HandleRefModel as SoftDeleteHandleRefModel
from django_peeringdb.models.concrete import IXLan, NetworkIXLan

from django_ixctl.inet.util import pdb_lookup
from django_ixctl.validators import validate_ip_v4, validate_ip_v6
import django_ixctl.enum
def generate_secret():
    return token_urlsafe()



class HandleRefModel(SoftDeleteHandleRefModel):
    """
    Like handle ref, but with hard delete
    """

    status = models.CharField(
        max_length=12,
        default="ok",
        choices=(
            ("ok", _("Ok")),
            ("pending", _("Pending")),
            ("deactivated", _("Deactivated")),
            ("failed", _("Failed")),
            ("expired", _("Expired")),
        ),
    )

    class Meta:
        abstract = True

    def delete(self):
        return super().delete(hard=True)


class PdbRefModel(HandleRefModel):

    """
    Base class for models that reference a peeringdb model
    """

    # id of the peeringdb instance that is referenced by
    # this model
    pdb_id = models.PositiveIntegerField(blank=True, null=True)

    # if object was creates from it's pdb reference, the version
    # at the time of the creation should be stored here
    pdb_version = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        abstract = True

    class PdbRef:
        """ defines which peeringdb model is referenced """
        model = NetworkIXLan
        fields = {"pk": "pdb_id"}

    @classmethod
    def create_from_pdb(cls, pdb_object, save=True, **fields):
        """ create object from peeringdb instance """

        if not isinstance(pdb_object, cls.PdbRef.model):
            raise ValueError(_("Expected {} instance".format(cls.PdbRef.model)))

        for k, v in cls.PdbRef.fields.items():
            fields[v] = getattr(pdb_object, k, k)

        instance = cls(status="ok", **fields)
        if save:
            instance.save()
        return instance

    @property
    def pdb(self):
        """ returns PeeringDB object """
        if not hasattr(self, "_pdb"):
            filters = {}
            for k, v in self.PdbRef.fields.items():
                if v and hasattr(self, v):
                    v = getattr(self, v)
                filters[k] = v
            self._pdb = pdb_lookup(self.PdbRef.model, **filters)
        return self._pdb





@reversion.register()
class Organization(HandleRefModel):

    """
    Describes an organization
    """

    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=64, unique=True)
    personal = models.BooleanField(default=False)

    permission_namespaces = [
      "management",
      "ixctl",
    ]

    class HandleRef:
        tag = "org"

    @classmethod
    def sync(cls, orgs, user):
        synced = []
        with reversion.create_revision():
            reversion.set_user(user)
            for org_data in orgs:
                org = cls.sync_single(org_data, user)
                synced.append(org)

            for org in user.org_set.exclude(org_id__in=[o["id"] for o in orgs]):
                org.delete()
        return synced

    @classmethod
    def sync_single(cls, data, user):
        try:
            changed = False
            org = cls.objects.get(id=data["id"])
            if data["slug"] != org.slug:
                org.slug = data["slug"]
                changed = True
            if data["name"] != org.name:
                org.name = data["name"]
                changed = True
            if data["personal"] != org.personal:
                org.personal = data["personal"]
                changed = True
            if changed:
                org.save()
        except cls.DoesNotExist:
            org = cls.objects.create(
                id=data["id"],
                name=data["name"],
                slug=data["slug"],
                personal=data["personal"],
            )

        if not user.org_set.filter(org=org).exists():
            OrganizationUser.objects.create(org=org, user=user)

        return org

    @property
    def tag(self):
        return self.slug

    @property
    def display_name(self):
        if self.personal:
            return _("Personal")
        return self.name


    def __str__(self):
        return f"{self.name} ({self.slug})"

class Instance(HandleRefModel):

    """
    app instance, one per org per app

    Needs to specify an `org` ForeignKey pointing to
    Organization
    """

    org = models.ForeignKey(
        Organization, help_text=_("owned by org"), on_delete=models.CASCADE
    )
    secret = models.CharField(max_length=255, default=generate_secret)
    app_id = "ixctl"

    class Meta:
        db_table = "ixctl_instance"

    class HandleRef:
        tag = "instance"

    @classmethod
    def get_or_create(cls, org):
        """
        Returns an organization's instance

        Will create a new instance if it does not exist
        """

        try:
            instance = cls.objects.get(org=org)
        except cls.DoesNotExist:
            instance = cls.objects.create(org=org, status="ok")
        return instance



@reversion.register()
class OrganizationUser(HandleRefModel):

    """
    Describes a user -> organization relationship
    """

    org = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="user_set"
    )
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="org_set"
    )

    class HandleRef:
        tag = "orguser"

    class Meta:
        db_table = "account_org_user"
        verbose_name = _("Organization User")
        verbose_name = _("Organization Users")

    def __str__(self):
        return f"{self.user.username} <{self.user.email}>"


@reversion.register
class APIKey(HandleRefModel):
    """
    Describes an APIKey

    These are managed in account.20c.com, but will also be cached here

    Creation should always happen at account.20c.com
    """

    key = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="key_set"
    )

    class Meta:
        db_table = "account_api_key"
        verbose_name = _("API Key")
        verbose_name_plural = _("API Keys")

    class HandleRef:
        tag = "key"


@reversion.register()
class InternetExchange(PdbRefModel):
    name = models.CharField(max_length=255, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    urlkey = models.CharField(max_length=255, default=generate_secret, unique=True)

    instance = models.ForeignKey(
        Instance, related_name="ix_set", on_delete=models.CASCADE, null=True
    )

    class PdbRef(PdbRefModel.PdbRef):
        model = IXLan

    class HandleRef:
        tag = "ix"

    class Meta:
        db_table = "django_ixctl_ix"
        verbose_name_plural = _("Internet Exchanges")
        verbose_name = _("Internet Exchange")


    @classmethod
    def create_from_pdb(cls, instance, pdb_object, save=True, **fields):

        ix = super().create_from_pdb(pdb_object, save=save, instance=instance, **fields)

        ix.name = pdb_object.ix.name

        if save:
            ix.save()

        for netixlan in ix.pdb.netixlan_set.filter(status="ok"):
            InternetExchangeMember.create_from_pdb(netixlan, ix=ix)

        return ix

    @property
    def display_name(self):
        if self.name:
            return self.name
        if self.pdb_id:
            return ixlan.ix.name
        return f"Nameless Exchange ({self.id})"

    @property
    def ixf_export_url(self):
        # TODO: CRUFT (check any references and remove)
        return "/ix/export/ixf/{}/{}".format(self.instance.secret.self.id)

@reversion.register()
class InternetExchangeMember(PdbRefModel):

    ix = models.ForeignKey(
        InternetExchange, help_text=_("Members at this Exchange"), related_name="member_set", on_delete=models.CASCADE)
    ipaddr4 = models.CharField(
        max_length=255, blank=True, null=True, validators=[validate_ip_v4]
    )
    ipaddr6 = models.CharField(
        max_length=255, blank=True, null=True, validators=[validate_ip_v6]
    )
    is_rs_peer = models.BooleanField(default=False)
    speed = models.PositiveIntegerField()
    asn = models.PositiveIntegerField()
    name = models.CharField(max_length=255, blank=True, null=True)

    ixf_state = models.CharField(max_length=255, default="active")
    ixf_member_type = models.CharField(
        max_length=255, choices=django_ixctl.enum.IXF_MEMBER_TYPE, default="peering"
    )

    class HandleRef:
        tag = "member"

    class Meta:
        db_table = "django_ixctl_ixmember"
        verbose_name_plural = _("Internet Exchange Members")
        verbose_name = _("Internet Exchange Member")
        unique_together = (("ipaddr4", "ix"), ("ipaddr6", "ix"))

    @classmethod
    def create_from_pdb(cls, pdb_object, ix, save=True, **fields):

        member = super().create_from_pdb(
            pdb_object, ix=ix, save=False, **fields
        )

        member.ipaddr4 = pdb_object.ipaddr4
        member.ipaddr6 = pdb_object.ipaddr6
        member.is_rs_peer = pdb_object.is_rs_peer
        member.speed = pdb_object.speed
        member.asn = pdb_object.net.asn
        member.name = pdb_object.net.name

        if save:
            member.save()

        return member

    @property
    def display_name(self):
        return self.name or f"AS{self.asn}"



