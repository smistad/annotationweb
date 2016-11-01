from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .models import *
from annotationweb.models import Image, Task, ProcessedImage
from .forms import *
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
import random
import json
from common.task import get_previous_image, get_next_image, get_next_unprocessed_image


def process_next_image(request, task_id):
    return process_image(request, task_id, None)


def process_image(request, task_id, image_id):
    context = {}
    context['dark_style'] = 'yes'
    context['javascript_files'] = ['boundingbox/boundingbox.js']
    try:
        task = Task.objects.get(pk=task_id,type=Task.BOUNDING_BOX)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    try:
        if image_id is None:
            image = get_next_unprocessed_image(task)
        else:
            image = Image.objects.get(pk=image_id)

        # Check if image belongs to an image sequence
        if hasattr(image, 'keyframe'):
            print('Is part of image sequence')
            context['image_sequence'] = image.keyframe.image_sequence
            context['frame_nr'] = image.keyframe.frame_nr

        context['next_image_id'] = get_next_image(task, image.id)
        context['previous_image_id'] = get_previous_image(task, image.id)
        context['image'] = image
        context['task'] = task
        context['number_of_labeled_images'] = ProcessedImage.objects.filter(task=task_id).count()
        context['total_number_of_images'] = Image.objects.filter(subject__dataset__task=task_id).count()
        context['percentage_finished'] = round(context['number_of_labeled_images']*100 / context['total_number_of_images'], 1)
        context['image_quality_choices'] = ProcessedImage.IMAGE_QUALITY_CHOICES

        # Check if image has been annotated
        processed = ProcessedImage.objects.filter(image=image, task=task)
        if processed.exists():
            context['chosen_quality'] = processed[0].image_quality
        else:
            context['chosen_quality'] = -1

        # Load boxes if they exist
        context['boxes'] = BoundingBox.objects.filter(image__image=image, image__task=task)

        return render(request, 'boundingbox/process_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')


def save_boxes(request):
    if request.method != 'POST':
        raise Http404('')

    try:
        if 'quality' not in request.POST:
            raise Exception('ERROR: You must select image quality.')

        image_id = int(request.POST['image_id'])
        task_id = int(request.POST['task_id'])
        # Delete old boxes if they exist
        processed_images = ProcessedImage.objects.filter(image_id=image_id, task_id=task_id)
        processed_images.delete()

        image = ProcessedImage()
        image.image_id = image_id
        image.task_id = task_id
        image.user = request.user
        image.image_quality = request.POST['quality']
        image.save()

        # Store every box
        boxes = json.loads(request.POST['boxes'])
        for box in boxes:
            bb = BoundingBox()
            bb.x = int(box['x'])
            bb.y = int(box['y'])
            bb.width = int(box['width'])
            bb.height = int(box['height'])
            bb.image = image
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

