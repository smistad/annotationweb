import random

from django.http import Http404

from annotationweb.models import Image, Task, ProcessedImage


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


def setup_task_context(task_id, type, image_id):
    context = {}
    context['dark_style'] = 'yes'
    try:
        task = Task.objects.get(pk=task_id, type=type)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    if image_id is None:
        image = get_next_unprocessed_image(task)
    else:
        image = Image.objects.get(pk=image_id)

    # Check if image belongs to an image sequence
    if hasattr(image, 'keyframe'):
        context['image_sequence'] = image.keyframe.image_sequence
        context['frame_nr'] = image.keyframe.frame_nr

    context['next_image_id'] = get_next_image(task, image.id)
    context['previous_image_id'] = get_previous_image(task, image.id)
    context['image'] = image
    context['task'] = task
    context['number_of_labeled_images'] = ProcessedImage.objects.filter(task=task_id).count()
    context['total_number_of_images'] = Image.objects.filter(subject__dataset__task=task_id).count()
    context['percentage_finished'] = round(context['number_of_labeled_images']*100 / context['total_number_of_images'], 1)
    context['image_quality_choices'] = ProcessedImage.IMAGE_QUALITY_CHOICES

    # Check if image has been annotated
    processed = ProcessedImage.objects.filter(image=image, task=task)
    if processed.exists():
        context['chosen_quality'] = processed[0].image_quality
    else:
        context['chosen_quality'] = -1

    return context

