from fullctl.django.models import Task
from fullctl.django.tasks import register
import django_ixctl.models.ixctl as models


@register
class RsConfGenerate(Task):

    """
    Regenerate RS config


    arguments to pass to `create_task`:

        - rsconf_id (id of rsconf instance)
    """

    class Meta:
        proxy = True

    class HandleRef:
        tag = "task_rsconf_gen"

    def run(self, rsconf_id, *args, **kwargs):
        rsconf = models.RouteserverConfig.objects.get(id=rsconf_id)
        rsconf.generate()
