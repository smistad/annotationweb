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
        context = common.task.setup_task_context(request, task_id, Task.SEGMENTATION_POLYGON, image_id)
        context['javascript_files'] = ['segmentation_polygon/segmentation.js']

        # Check if image is already segmented, if so get data and pass to template
        try:
            annotation = ProcessedImage.objects.get(task_id=task_id, image_id=image_id)
            segmentation = SegmentationPolygon.objects.get(image=annotation)
            control_points = ControlPoint.objects.filter(segmentation=segmentation).order_by('index')

            context['segmentation_polygon'] = segmentation
            context['control_points'] = control_points
        except ProcessedImage.DoesNotExist:
            pass

        return render(request, 'segmentation_polygon/segment_image.html', context)
    except IndexError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')


def save_segmentation(request):
    error_messages = ''

    target_frames = json.loads(request.POST['target_frames'])
    control_points = json.loads(request.POST['control_points'])
    n_labels = int(request.POST['n_labels'])

    rejected = request.POST['rejected'] == 'true'

    if not rejected:
        if target_frames == []:
            error_messages += 'No target frames<br>'
        # Should be added as a task option:
        #else:
        #    # Check if all control points is present
        #    for i in range(len(target_frames)):
        #        for j in range(n_labels):
        #            if len(control_points[i][j]) < 1:
        #                error_messages += 'Label {1} annotation missing in target frame {0}<br>'.format(i, j)

    if len(error_messages):
        response = {
            'success': 'false',
            'message': error_messages,
        }
    else:
        try:
            annotation = common.task.save_annotation(request)

            # Save segmentation
            segmentation = SegmentationPolygon()
            segmentation.image = annotation
            segmentation.target_frames = str(target_frames)
            segmentation.save()

            # Save control points
            for frame in range(len(target_frames)):
                for object in range(n_labels):
                    for point in range(len(control_points[frame][object])):
                        control_point = ControlPoint()
                        control_point.segmentation = segmentation
                        control_point.x = float(control_points[frame][object][point]['x'])
                        control_point.y = float(control_points[frame][object][point]['y'])
                        control_point.index = point
                        control_point.frame = frame
                        control_point.object = object
                        control_point.uncertain = bool(control_points[frame][object][point]['uncertain'])
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
