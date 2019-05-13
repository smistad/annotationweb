from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .models import *
from annotationweb.models import Task, Annotation
from .forms import *
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
import random
import json
import common.task


def process_next_image(request, task_id):
    return process_image(request, task_id, None)


def process_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.BOUNDING_BOX, image_id)
        context['javascript_files'] = ['boundingbox/boundingbox.js']

        # Load boxes if they exist
        context['boxes'] = BoundingBox.objects.filter(image__image_id=image_id, image__task_id=task_id)

        return render(request, 'boundingbox/process_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')


def save_boxes(request):
    try:
        annotation = common.task.save_annotation(request)

        # Store every box
        boxes = json.loads(request.POST['boxes'])
        for box in boxes:
            bb = BoundingBox()
            bb.x = int(box['x'])
            bb.y = int(box['y'])
            bb.width = int(box['width'])
            bb.height = int(box['height'])
            bb.image = annotation
            bb.label_id = int(box['label_id'])
            bb.save()

        response = {
            'success': 'true',
            'message': 'Completed'
        }
        messages.success(request, str(len(boxes)) + ' boxes were saved')
    except Exception as e:
        response = {
            'success': 'false',
            'message': str(e)
        }

    return JsonResponse(response)

