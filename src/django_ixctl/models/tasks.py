from fullctl.django.models import Task, LimitAction
from fullctl.django.tasks import register
import django_ixctl.models.ixctl as models


@register
class RsConfGenerate(Task):

    """
    Regenerate RS config


    arguments to pass to `create_task`:

        - rsconf_id (id of rsconf instance)
    """

    class TaskMeta:
        # limit of 1, but this will be per rs
        # see generate_limit_id below
        limit = 1

    class Meta:
        proxy = True

    class HandleRef:
        tag = "task_rsconf_gen"

    @property
    def generate_limit_id(self):
        """
        We want the task limit to be per rsconf so we
        include the rsconf id in the limit_id for the task
        """
        return self.param["args"][0]

    def run(self, rsconf_id, *args, **kwargs):
        """
        Regenerate the rsconfig
        """
        rsconf = models.RouteserverConfig.objects.get(id=rsconf_id)
        rsconf.generate()
