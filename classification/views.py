from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.http import Http404
from django.db.models import Max

from common.task import get_next_unprocessed_image, get_next_image, get_previous_image

from .models import *
from annotationweb.models import Image, Task, ProcessedImage


def label_next_image(request, task_id):
    return label_image(request, task_id, None)


def label_image(request, task_id, image_id):
    context = {}
    context['dark_style'] = 'yes'
    context['javascript_files'] = ['classification/classification.js']
    try:
        task = Task.objects.get(pk=task_id, user=request.user)
        labels = Label.objects.filter(task=task)
    except Task.DoesNotExist:
        raise Http404("Task does not exist or user has no access to the task")

    # Get random unlabeled image
    try:
        if image_id is None:
            image = get_next_unprocessed_image(task)
        else:
            image = Image.objects.get(pk=image_id)
        print('Got the following image: ', image.id, image.filename)

        # Check if image has been labeled
        processed = ImageLabel.objects.filter(image__image=image, image__task=task)
        if processed.exists():
            context['chosen_label'] = processed[0].label.id
            context['chosen_quality'] = processed[0].image.image_quality
        else:
            context['chosen_quality'] = -1

        # Check if image belongs to an image sequence
        if hasattr(image, 'keyframe'):
            print('Is part of image sequence')
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

        # Get all labels for this task
        if len(labels) == 0:
            raise Http404('No labels found!')
        context['labels'] = labels
        return render(request, 'classification/label_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to label.')
        return redirect('index')


def save_labels(request):
    if request.method != 'POST':
        raise Http404('')

    try:
        if 'quality' not in request.POST:
            raise Exception('ERROR: You must select image quality.')

        image_id = int(request.POST['image_id'])
        task_id = int(request.POST['task_id'])
        label_id = int(request.POST['label_id'])

        task = Task.objects.get(pk=task_id, user=request.user)
        label = Label.objects.get(pk=label_id)

        previous_processed_image = ProcessedImage.objects.filter(image_id=image_id, task=task_id)
        previous_processed_image.delete()

        processed_image = ProcessedImage()
        processed_image.image_id = image_id
        processed_image.task = task
        processed_image.user = request.user
        processed_image.image_quality = request.POST['quality']
        processed_image.save()

        # Task specific
        labeled_image = ImageLabel()
        labeled_image.image = processed_image
        labeled_image.label = label
        labeled_image.task = task

        labeled_image.save()

        response = {
            'success': 'true',
            'message': 'Completed'
        }
        messages.success(request, 'Classification saved')
    except Exception as e:
        response = {
            'success': 'false',
            'message': str(e)
        }

    return JsonResponse(response)

