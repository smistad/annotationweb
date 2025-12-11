from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .models import *
from annotationweb.models import Task, ImageAnnotation
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
import random
import json
import common.task
from django.db import transaction


def process_next_image(request, task_id):
    return process_image(request, task_id, None)


def process_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, image_id)
        context['javascript_files'] = ['landmark/landmark.js']

        # Load landmarks if they exist
        context['landmarks'] = Landmark.objects.filter(image__image_annotation__image_id=image_id, image__image_annotation__task_id=task_id)

        return render(request, 'landmark/process_image.html', context)
    except common.task.NoMoreImages:
        messages.info(request, 'This task is finished, no more images to annotate.')
        return redirect('index')
    except RuntimeError as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(request.headers.get('referer'))


def save(request):
    try:
        with transaction.atomic():
            annotations = common.task.save_annotation(request)

            # Store every landmark
            landmarks = json.loads(request.POST['landmarks'])
            counter = 0
            for annotation in annotations:
                frame_nr = str(annotation.frame_nr)
                for landmark in landmarks[frame_nr]:
                    new_landmark = Landmark()
                    new_landmark.x = int(landmark['x'])
                    new_landmark.y = int(landmark['y'])
                    new_landmark.image = annotation
                    new_landmark.label_id = int(landmark['label_id'])
                    new_landmark.save()
                    counter += 1

            response = {
                'success': 'true',
                'message': 'Completed'
            }
            messages.success(request, str(counter) + ' landmarks were saved')
    except Exception as e:
        response = {
            'success': 'false',
            'message': str(e)
        }

    return JsonResponse(response)
