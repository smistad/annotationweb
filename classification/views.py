from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.db.models import Max
from django.contrib.admin.views.decorators import staff_member_required

import random

from .models import *
from annotationweb.models import Image, Task, ProcessedImage


def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.filter(dataset__task=task_id).exclude(processedimage__task=task_id)
    return unlabeled_images[random.randrange(0, len(unlabeled_images))]


def label_images(request, task_id):
    context = {}
    context['dark_style'] = 'yes'
    try:
        task = Task.objects.get(pk=task_id)
        labels = Label.objects.filter(task=task)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    if request.method == 'POST':
        # Save new label
        processed_image = ProcessedImage()
        processed_image.image_id = request.POST['image_id']
        processed_image.task = task
        processed_image.user = request.user
        processed_image.save()

        labeled_image = ImageLabel()
        labeled_image.image = processed_image
        for label in labels:
            if request.POST.__contains__(label.name):
                labeled_image.label = label
                labeled_image.task = task

        labeled_image.save()

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
        context['total_number_of_images'] = Image.objects.filter(dataset__task=task_id).count()
        context['percentage_finished'] = round(context['number_of_labeled_images']*100 / context['total_number_of_images'], 1)

        # Get all labels for this task
        if len(labels) == 0:
            raise Http404('No labels found!')
        context['labels'] = labels
        print('Got the following random image: ', image.filename)
        return render(request, 'classification/label_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to label.')
        return redirect('index')


def undo_image_label(request, task_id):
    try:
        id_max = ProcessedImage.objects.filter(task_id=task_id).aggregate(Max('id'))['id__max']
        ProcessedImage.objects.get(pk=id_max).delete()
        return redirect('classification:label_image', task_id=task_id)
    except Task.DoesNotExist:
        raise Http404('Image label does not exist')
