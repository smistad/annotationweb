import json

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.http import Http404

import common.task

from .models import *
from annotationweb.models import Task, ImageAnnotation


def label_next_image(request, task_id):
    return label_image(request, task_id, None)


def label_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.CLASSIFICATION, image_id)
        context['javascript_files'] = ['classification/classification.js']

        # Get label, if image has been already labeled
        try:
            target_frames = context['frames']
            processed = ImageLabel.objects.get(image_id=target_frames[0].id)
            context['chosen_label'] = processed.label.id
            context['target_labels'] = ImageLabel.objects.filter(image__in=target_frames)
        except:
            pass

        return render(request, 'classification/label_image.html', context)
    except IndexError:
        messages.info(request, 'This task is finished, no more images to annotate.')
        return redirect('index')


def save_labels(request):
    try:
        rejected = request.POST['rejected'] == 'true'
        if rejected:
            annotation = common.task.save_annotation(request)
        else:
            try:
                labels = json.loads(request.POST['target_labels'])
            except:
                raise Exception('You must select a classification label.')

            annotations = common.task.save_annotation(request)
            for annotation in annotations:
                frame_nr = str(annotation.frame_nr)
                labeled_image = ImageLabel()
                labeled_image.image = annotation
                labeled_image.label = Label.objects.get(id=int(labels[frame_nr]['label']['id']))
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
