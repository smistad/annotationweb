from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.http import Http404

import common.task

from .models import *
from annotationweb.models import Image, Task, ProcessedImage


def label_next_image(request, task_id):
    return label_image(request, task_id, None)


def label_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(task_id, Task.CLASSIFICATION, image_id)
        context['javascript_files'] = ['classification/classification.js']

        # Load labels
        context['labels'] = Label.objects.filter(task=task_id)

        # Get label, if image has been already labeled
        try:
            processed = ImageLabel.objects.get(image__image_id=image_id, image__task_id=task_id)
            context['chosen_label'] = processed.label.id
        except:
            pass

        return render(request, 'classification/label_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to segment.')
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

