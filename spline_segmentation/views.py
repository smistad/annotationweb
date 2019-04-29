from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from annotationweb.models import Task
import common.task
import json
from .models import *


def segment_next_image(request, task_id):
    return segment_image(request, task_id, None)


def segment_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.SPLINE_SEGMENTATION, image_id)
        context['javascript_files'] = ['spline_segmentation/segmentation.js']

        # Check if image is already segmented, if so get data and pass to template
        try:
            annotation = ProcessedImage.objects.get(task_id=task_id, image_id=image_id)
            control_points = ControlPoint.objects.filter(image=annotation).order_by('index')

            context['control_points'] = control_points
        except ProcessedImage.DoesNotExist:
            pass

        return render(request, 'spline_segmentation/segment_image.html', context)
    except IndexError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')


def save_segmentation(request):
    error_messages = ''

    control_points = json.loads(request.POST['control_points'])
    n_labels = int(request.POST['n_labels'])

    if len(error_messages):
        response = {
            'success': 'false',
            'message': error_messages,
        }
    else:
        try:
            annotation = common.task.save_annotation(request)

            # Save segmentation
            # Save control points
            for object in range(n_labels):
                for point in range(len(control_points[object])):
                    control_point = ControlPoint()
                    control_point.image = annotation
                    control_point.x = float(control_points[object][point]['x'])
                    control_point.y = float(control_points[object][point]['y'])
                    control_point.index = point
                    control_point.label = Label.objects.get(id=int(control_points[object][point]['label_id']))
                    control_point.uncertain = bool(control_points[object][point]['uncertain'])
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
