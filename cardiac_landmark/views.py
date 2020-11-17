import json
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from annotationweb.models import Task
import common.task
from .models import *


def landmark_next_image(request, task_id):
    return landmark_image(request, task_id, None)

def landmark_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.CARDIAC_LANDMARK, image_id)
        context['javascript_files'] = ['cardiac_landmark/cardiac_landmark.js']

        # Check if image is already segmented, if so get data and pass to template
        try:
            # Load landmarks if they exist
            annotation = ProcessedImage.objects.get(task_id=task_id, image_id=image_id)
            cardiac_landmark = CardiacLandmark.objects.get(image=annotation)
            control_points = ControlPoint.objects.filter(landmark=cardiac_landmark).order_by('index')

            context['landmark'] = cardiac_landmark
            context['control_points'] = control_points
        except ProcessedImage.DoesNotExist:
            pass

        return render(request, 'cardiac_landmark/cardiac_landmark_image.html', context)
    except common.task.NoMoreImages:
        messages.info(request, 'This task is finished, no more images to annotate.')
        return redirect('index')
    except RuntimeError as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def save_landmark(request):
    error_messages = ''
    frame_ED = int(request.POST['frame_ed'])
    frame_ES = int(request.POST['frame_es'])
    # motion_mode_line = int(round(float(request.POST['motion_mode_line'])))
    control_points = json.loads(request.POST['control_points'])
    print(control_points)
    objects = ('Anterior', 'Apex', 'Inferior')

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

            landmark = CardiacLandmark()
            landmark.image = annotation
            landmark.frame_ED = frame_ED
            landmark.frame_ES = frame_ES
            #landmark.motion_mode_line = motion_mode_line
            landmark.save()

            # Save control points
            for phase in range(len(PHASES)):
                for object in range(len(OBJECTS)):
                    for point in range(len(control_points[phase][object])):
                        control_point = ControlPoint()
                        control_point.landmark = landmark
                        control_point.x = float(control_points[phase][object][point]['x'])
                        control_point.y = float(control_points[phase][object][point]['y'])
                        control_point.index = point
                        control_point.phase = phase
                        control_point.object = object
                        control_point.uncertain = bool(control_points[phase][object][point]['uncertain'])
                        control_point.save()

            response = {
                'success': 'true',
                'message': 'Completed'
            }
        except Exception as e:
            response = {
                'success': 'false',
                'message': str(e)
            }

    return JsonResponse(response)

def show_landmarks(request, task_id, image_id):
    pass