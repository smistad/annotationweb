from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
import random
from io import StringIO, BytesIO
import base64
from annotationweb.settings import BASE_DIR
from common.metaimage import *
import numpy as np
from annotationweb.models import Task, Image, ProcessedImage, Label
from common.utility import get_image_as_http_response
import common.task


def segment_next_image(request, task_id):
    return segment_image(request, task_id, None)


def segment_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.CARDIAC_SEGMENTATION, image_id)
        context['javascript_files'] = ['cardiac/segmentation.js']

        return render(request, 'cardiac/segment_image.html', context)
    except IndexError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')


def save_segmentation(request):
    print(request.POST)
    error_messages = ''
    frame_ED = int(request.POST['frame_ed'])
    frame_ES = int(request.POST['frame_es'])
    control_points = json.loads(request.POST['control_points'])
    objects = ('Endocardium', 'Epicardium', 'Left atrium')

    if frame_ED == -1:
        error_messages += 'End Diastole frame not annotated<br>'
    else:
        # Check if all control points for ED is present
        for i in range(len(objects)):
            if len(control_points[0][i]) < 1:
                error_messages += objects[i] + ' annotation missing in End Diastole<br>'

    if frame_ES == -1:
        error_messages += 'End Systole frame not annotated<br>'
    else:
        # Check if all control points for ES is present
        # Check if all control points for ED is present
        for i in range(len(objects)):
            if len(control_points[1][i]) < 1:
                error_messages += objects[i] + ' annotation missing in End Systole<br>'

    if len(error_messages):
        response = {
            'success': 'false',
            'message': error_messages,
        }
    else:
        # TODO store data in database
        response = {
            'success': 'true',
            'message': 'Annotation saved',
        }

    return JsonResponse(response)


def show_segmentation(request, task_id, image_id):
    pass
