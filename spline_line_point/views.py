from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from annotationweb.models import Task, KeyFrameAnnotation
import common.task
import json
from spline_segmentation.models import *
from django.db import transaction


def segment_next_image(request, task_id):
    return segment_image(request, task_id, None)


def segment_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.SPLINE_LINE_POINT, image_id)
        context['javascript_files'] = ['spline_line_point/segmentation.js']

        # Check if image is already segmented, if so get data and pass to template
        try:
            annotations = KeyFrameAnnotation.objects.filter(image_annotation__task_id=task_id, image_annotation__image_id=image_id)
            control_points = ControlPoint.objects.filter(image__in=annotations).order_by('index')
            context['control_points'] = control_points
            context['target_frames'] = annotations
        except KeyFrameAnnotation.DoesNotExist:
            pass

        return render(request, 'spline_line_point/segment_image.html', context)
    except common.task.NoMoreImages:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')
    except RuntimeError as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def save_segmentation(request):
    error_messages = ''

    control_points = json.loads(request.POST['control_points'])
    n_labels = int(request.POST['n_labels'])

    try:
        # Use atomic transaction here so if something crashes the annotations are restored..
        with transaction.atomic():
            annotations = common.task.save_annotation(request)

            # Save segmentation
            # Save control points
            for annotation in annotations:
                frame_nr = str(annotation.frame_nr)
                for object in control_points[frame_nr]:
                    nr_of_control_points = len(control_points[frame_nr][object]['control_points'])
                    if nr_of_control_points < 1:
                        continue
                    for point in range(nr_of_control_points):
                        control_point = ControlPoint()
                        control_point.image = annotation
                        control_point.x = float(control_points[frame_nr][object]['control_points'][point]['x'])
                        control_point.y = float(control_points[frame_nr][object]['control_points'][point]['y'])
                        control_point.index = point
                        control_point.object = int(object)
                        control_point.label = Label.objects.get(id=int(control_points[frame_nr][object]['label']['id']))
                        control_point.uncertain = bool(control_points[frame_nr][object]['control_points'][point]['uncertain'])
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
        raise e

    return JsonResponse(response)


def show_segmentation(request, task_id, image_id):
    pass
