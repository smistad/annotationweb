from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .models import *
from annotationweb.models import Image, Task, ProcessedImage
from .forms import *
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
import random
import json


def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.filter(subject__dataset__task=task_id).exclude(processedimage__task=task_id)
    return unlabeled_images[random.randrange(0, len(unlabeled_images))]


def process_image(request, task_id):
    context = {}
    context['dark_style'] = 'yes'
    context['javascript_files'] = ['boundingbox/boundingbox.js']
    try:
        task = Task.objects.get(pk=task_id,type=Task.BOUNDING_BOX)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    # Get random unlabeled image
    try:
        image = pick_random_image(task_id)

        # Check if image belongs to an image sequence
        if hasattr(image, 'keyframe'):
            print('Is part of image sequence')
            context['image_sequence'] = image.keyframe.image_sequence
            context['frame_nr'] = image.keyframe.frame_nr

        context['image'] = image
        context['task'] = task
        context['number_of_labeled_images'] = ProcessedImage.objects.filter(task=task_id).count()
        context['total_number_of_images'] = Image.objects.filter(subject__dataset__task=task_id).count()
        context['percentage_finished'] = round(context['number_of_labeled_images']*100 / context['total_number_of_images'], 1)

        print('Got the following random image: ', image.filename)
        return render(request, 'boundingbox/process_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('annotation:index')


def save_boxes(request):
    if request.method != 'POST':
        raise Http404('')

    try:
        image = ProcessedImage()
        image.image_id = int(request.POST['image_id'])
        image.task_id = int(request.POST['task_id'])
        image.user = request.user
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

