from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import UserManager
from django.core import validators
from django.core.mail import send_mail
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.http import urlquote
from django.utils.translation import ugettext_lazy as _

from django_handleref.models import HandleRefModel as SoftDeleteHandleRefModel

from django_ixctl.validators import validate_ip_v4, validate_ip_v6
import django_ixctl.enum

class HardDeleteHandleRefModel(SoftDeleteHandleRefModel):
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


class PdbRefModel(HardDeleteHandleRefModel):

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

        model = None
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


class Exchange(HardDeleteHandleRefModel):
    name = models.CharField(max_length=255, blank=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class HandleRef:
        tag = "ix"

    class Meta:
        db_table = "django_ixctl_ix"
        verbose_name_plural = _("Exchanges")
        verbose_name = _("Exchange")



class ExchangeMember(PdbRefModel):

    ix_id = models.ForeignKey(
        Exchange, help_text=_("Exchanges"), related_name="member_set", on_delete=models.CASCADE)
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

    state = models.CharField(max_length=255, default="active")
    type = models.CharField(
        max_length=255, choices=django_ixctl.enum.IXF_MEMBER_TYPE, default="peering"
    )

    class HandleRef:
        tag = "member"

    class Meta:
        db_table = "django_ixctl_ixmember"
        verbose_name_plural = _("Exchange Members")
        verbose_name = _("Exchange Member")




