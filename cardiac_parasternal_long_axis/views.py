from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
import random
from io import StringIO, BytesIO
import base64
from annotationweb.settings import BASE_DIR
from common.metaimage import *
import numpy as np
from annotationweb.models import Task, ImageAnnotation, Label
from common.utility import get_image_as_http_response
import common.task
from annotationweb.models import KeyFrameAnnotation
from spline_segmentation.models import ControlPoint
from django.db import transaction


def segment_next_image(request, task_id):
    return segment_image(request, task_id, None)

def add_default_labels(task_id):
    # Check if task has proper labels set up.
    # If not add them to the database,
    task = Task.objects.get(pk=task_id)
    labels = (
        ('Endocardium', (0, 255, 0)),
        ('Epicardium', (0, 0, 255)),
        ('Left atrium', (255, 0, 0)),
        ('Aorta', (150, 70, 50)),
        ('Right ventricle', (255, 255, 0)),
        ('LVOT', (0, 255, 255))
    )
    if len(task.label.all()) != 6:
        # Remove old ones
        for label in task.label.all():
            task.label.remove(label)
        print('Adding labels to task')
        for label in labels:
            try:
                # Check if already exist
                label_obj = Label.objects.get(name=label[0])
            except Label.DoesNotExist:
                label_obj = Label()
                label_obj.name = label[0]
                label_obj.color_red = label[1][0]
                label_obj.color_green = label[1][1]
                label_obj.color_blue = label[1][2]
                label_obj.save()
            task.label.add(label_obj)
        task.save()


def segment_image(request, task_id, image_id):

    add_default_labels(task_id)

    try:
        context = common.task.setup_task_context(request, task_id, Task.CARDIAC_PLAX_SEGMENTATION, image_id)
        image_id = context['image'].id  # Because image_id can initially be None
        context['javascript_files'] = ['cardiac_parasternal_long_axis/segmentation.js']

        # Check if image is already segmented, if so get data and pass to template
        try:

            annotations = KeyFrameAnnotation.objects.filter(image_annotation__task_id=task_id,
                                                            image_annotation__image_id=image_id)
            control_points = ControlPoint.objects.filter(image__in=annotations).order_by('index')
            context['control_points'] = control_points
            context['target_frames'] = annotations
        except KeyFrameAnnotation.DoesNotExist:
            pass

        return render(request, 'cardiac_parasternal_long_axis/segment_image.html', context)
    except common.task.NoMoreImages:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')
    except RuntimeError as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def save_segmentation(request):
    error_messages = ''

    motion_mode_line = int(round(float(request.POST['motion_mode_line'])))
    control_points = json.loads(request.POST['control_points'])
    target_frame_types = json.loads(request.POST['target_frame_types'])
    print(control_points)
    objects = ('Endocardium', 'Epicardium', 'Left atrium', 'Aorta', 'Right ventricle', 'LVOT')

    rejected = request.POST['rejected'] == 'true'

    if not rejected:
        for frame_nr in control_points.keys():
            for i in range(len(objects)):
                if str(i) in control_points[frame_nr] and \
                        len(control_points[frame_nr][str(i)]['control_points']) < 1:
                    error_messages += objects[i] + ' annotation missing in frame ' + str(frame_nr) + '<br>'

    if len(error_messages):
        response = {
            'success': 'false',
            'message': error_messages,
        }
    else:
        try:
            # Use atomic transaction here so if something crashes the annotations are restored..
            with transaction.atomic():
                annotations = common.task.save_annotation(request)

                # Save segmentation
                # Save control points
                for annotation in annotations:
                    frame_nr = str(annotation.frame_nr)

                    # Set frame metadata
                    annotation.frame_metadata = target_frame_types[frame_nr]
                    annotation.save()

                    for object in control_points[frame_nr]:
                        nr_of_control_points = len(control_points[frame_nr][object]['control_points'])
                        if nr_of_control_points < 2:
                            continue
                        for point in range(nr_of_control_points):
                            control_point = ControlPoint()
                            control_point.image = annotation
                            control_point.x = float(control_points[frame_nr][object]['control_points'][point]['x'])
                            control_point.y = float(control_points[frame_nr][object]['control_points'][point]['y'])
                            control_point.index = point
                            control_point.object = int(object)
                            # TODO modify this line to have proper label:
                            control_point.label = Label.objects.get(id=int(control_points[frame_nr][object]['label']['id']))
                            control_point.uncertain = bool(
                                control_points[frame_nr][object]['control_points'][point]['uncertain'])
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
