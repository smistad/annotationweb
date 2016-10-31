import random
from annotationweb.models import Image


def get_next_unprocessed_image(task):
    """
    Get the next unprocessed image  related to a task
    :param task:
    :return image:
    """
    return Image.objects.filter(subject__dataset__task=task).exclude(processedimage__task=task).order_by('id')[0]


def get_previous_image(task, image_id):
    try:
        return Image.objects.filter(subject__dataset__task=task).exclude(id__gte=image_id).order_by('-id')[0].id
    except:
        return None


def get_next_image(task, image_id):
    try:
        return Image.objects.filter(subject__dataset__task=task).exclude(id__lte=image_id).order_by('id')[0].id
    except:
        return None
