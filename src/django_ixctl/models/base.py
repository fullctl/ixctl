from django.db import models
from django.utils.translation import gettext_lazy as _

from django_handleref.models import HandleRefModel as SoftDeleteHandleRefModel

class HandleRefModel(SoftDeleteHandleRefModel):
    """
    Like handle ref, but with hard delete
    and extended status types
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


