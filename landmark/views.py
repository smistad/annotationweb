from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .models import *
from annotationweb.models import Task, ImageAnnotation
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
import random
import json
import common.task


def process_next_image(request, task_id):
    return process_image(request, task_id, None)


def process_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.LANDMARK, image_id)
        context['javascript_files'] = ['landmark/landmark.js']

        # Load landmarks if they exist
        context['landmarks'] = Landmark.objects.filter(image__image_id=image_id, image__task_id=task_id)

        return render(request, 'landmark/process_image.html', context)
    except common.task.NoMoreImages:
        messages.info(request, 'This task is finished, no more images to annotate.')
        return redirect('index')
    except RuntimeError as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))



def save(request):
    try:
        annotation = common.task.save_annotation(request)

        # Store every landmark
        landmarks = json.loads(request.POST['landmarks'])
        for landmark in landmarks:
            new_landmark = Landmark()
            new_landmark.x = int(landmark['x'])
            new_landmark.y = int(landmark['y'])
            new_landmark.image = annotation
            new_landmark.label_id = int(landmark['label_id'])
            new_landmark.save()

        response = {
            'success': 'true',
            'message': 'Completed'
        }
        messages.success(request, str(len(landmarks)) + ' landmarks were saved')
    except Exception as e:
        response = {
            'success': 'false',
            'message': str(e)
        }

    return JsonResponse(response)
