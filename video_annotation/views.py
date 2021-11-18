from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .models import *
from annotationweb.models import Task, ImageAnnotation
from .forms import *
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse, HttpResponseRedirect
import random
import json
import common.task


def process_next_image(request, task_id):
    return process_image(request, task_id, None)


def process_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.VIDEO_ANNOTATION, image_id)
        context['javascript_files'] = ['video_annotation/video_annotation.js']

        # Load boxes if they exist
        try:
            annotations = KeyFrameAnnotation.objects.filter(image_annotation__task_id=task_id,
                                                            image_annotation__image_id=image_id)
            context['boxes'] = VideoAnnotation.objects.filter(image__in=annotations)
            context['target_frames'] = annotations
        except KeyFrameAnnotation.DoesNotExist:
            pass

        return render(request, 'video_annotation/process_image.html', context)
    except common.task.NoMoreImages:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')
    except RuntimeError as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def save_boxes(request):
    try:
        annotations = common.task.save_annotation(request)
        boxes = json.loads(request.POST['boxes'])

        # Store every box
        for annotation in annotations:
            frame_nr = str(annotation.frame_nr)
            for box in boxes[frame_nr]:
                bb = VideoAnnotation()
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

