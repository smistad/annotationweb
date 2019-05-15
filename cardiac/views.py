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
from annotationweb.models import Task, ImageAnnotation, Label
from common.utility import get_image_as_http_response
import common.task
from .models import *


def segment_next_image(request, task_id):
    return segment_image(request, task_id, None)


def segment_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.CARDIAC_SEGMENTATION, image_id)
        context['javascript_files'] = ['cardiac/segmentation.js']

        # Check if image is already segmented, if so get data and pass to template
        try:
            annotation = ProcessedImage.objects.get(task_id=task_id, image_id=image_id)
            segmentation = Segmentation.objects.get(image=annotation)
            control_points = ControlPoint.objects.filter(segmentation=segmentation).order_by('index')

            context['segmentation'] = segmentation
            context['control_points'] = control_points
        except ProcessedImage.DoesNotExist:
            pass

        return render(request, 'cardiac/segment_image.html', context)
    except IndexError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')


def save_segmentation(request):
    error_messages = ''
    frame_ED = int(request.POST['frame_ed'])
    frame_ES = int(request.POST['frame_es'])
    motion_mode_line = int(round(float(request.POST['motion_mode_line'])))
    control_points = json.loads(request.POST['control_points'])
    print(control_points)
    objects = ('Endocardium', 'Epicardium', 'Left atrium')

    rejected = request.POST['rejected'] == 'true'

    if not rejected:
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
        try:
            annotation = common.task.save_annotation(request)

            # Save segmentation (frame_ED and frame_ES)
            segmentation = Segmentation()
            segmentation.image = annotation
            segmentation.frame_ED = frame_ED
            segmentation.frame_ES = frame_ES
            segmentation.motion_mode_line = motion_mode_line
            segmentation.save()

            # Save control points
            for phase in range(len(PHASES)):
                for object in range(len(OBJECTS)):
                    for point in range(len(control_points[phase][object])):
                        control_point = ControlPoint()
                        control_point.segmentation = segmentation
                        control_point.x = float(control_points[phase][object][point]['x'])
                        control_point.y = float(control_points[phase][object][point]['y'])
                        control_point.index = point
                        control_point.phase = phase
                        control_point.object = object
                        control_point.uncertain = bool(control_points[phase][object][point]['uncertain'])
                        control_point.save()

            response = {
                'success': 'true',
                'message': 'Annotation saved',
            }
        except Exception as e:
            response = {
                'success': 'false',
                'message': str(e),
            }

    return JsonResponse(response)


def show_segmentation(request, task_id, image_id):
    pass
