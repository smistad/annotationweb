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


def setup_task_context(request, task_id, type, image_id):
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

        # Only show next and previous buttons if we processing specific images
        context['next_image_id'] = get_next_image(task, image.id)
        context['previous_image_id'] = get_previous_image(task, image.id)

        # Give return URL to template if it exists
        if 'return_to_url' in request.session:
            context['return_url'] = request.session['return_to_url']

    # Delete return URL
    if 'return_to_url' in request.session:
        del request.session['return_to_url']

    # Check if image belongs to an image sequence
    if hasattr(image, 'keyframe'):
        context['image_sequence'] = image.keyframe.image_sequence
        context['frame_nr'] = image.keyframe.frame_nr

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


def save_annotation(request):
    if request.method != 'POST':
        raise Exception('ERROR: Must use POST when saving processed image.')

    # Image quality is required
    if 'quality' not in request.POST:
        raise Exception('ERROR: You must select image quality.')

    image_id = int(request.POST['image_id'])
    task_id = int(request.POST['task_id'])

    # Delete old annotations if it exists
    annotations = ProcessedImage.objects.filter(image_id=image_id, task_id=task_id)
    annotations.delete()

    # Save to DB
    annotation = ProcessedImage()
    annotation.image_id = image_id
    annotation.task_id = task_id
    annotation.user = request.user
    annotation.image_quality = request.POST['quality']
    annotation.save()

    return annotation
