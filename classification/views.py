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
    try:
        annotation = common.task.save_annotation(request)

        label_id = int(request.POST['label_id'])
        label = Label.objects.get(pk=label_id)

        labeled_image = ImageLabel()
        labeled_image.image = annotation
        labeled_image.label = label
        labeled_image.task = annotation.task

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

