from celery import shared_task
from django.contrib.contenttypes.models import ContentType


def launch_task(task):
    """
    Use this function to launch a task, by passing a common.Task
    instance

    Arguments:
        - task <common.Task>
    """
    content_type = ContentType.objects.get_for_model(task._meta.model)
    celery_id = _launch_task.delay(content_type.id, task.id)
    task.queue_id = celery_id
    task.save()


@shared_task
def _launch_task(content_type_id, pk):
    """
    This is will send the task to the celery queue.

    This will be done automatically by `launch_task`
    """
    task_model = ContentType.objects.get(id=content_type_id).model_class()
    task = task_model.objects.get(id=pk)
    task._run()
