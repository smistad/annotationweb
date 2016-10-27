from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import Http404
from django.db.models import Max

import random

from .models import *
from annotationweb.models import Image, Task, ProcessedImage


def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.filter(subject__dataset__task=task_id).exclude(processedimage__task=task_id)
    return unlabeled_images[random.randrange(0, len(unlabeled_images))]


def label_images(request, task_id):
    context = {}
    context['dark_style'] = 'yes'
    try:
        task = Task.objects.get(pk=task_id, user=request.user)
        labels = Label.objects.filter(task=task)
    except Task.DoesNotExist:
        raise Http404("Task does not exist or user has no access to the task")

    show_image = None
    if request.method == 'POST':
        # Check that quality is checked
        if 'quality' not in request.POST:
            messages.error(request, 'ERROR: You must select image quality.')
            show_image = request.POST['image_id']
        else:
            # Save new label
            processed_image = ProcessedImage()
            processed_image.image_id = request.POST['image_id']
            processed_image.task = task
            processed_image.user = request.user
            processed_image.image_quality = request.POST['quality']
            processed_image.save()

            # Task specific
            labeled_image = ImageLabel()
            labeled_image.image = processed_image
            for label in labels:
                if request.POST.__contains__(label.name):
                    labeled_image.label = label
                    labeled_image.task = task

            labeled_image.save()

    # Get random unlabeled image
    try:
        if show_image is None:
            image = pick_random_image(task_id)
        else:
            image = Image.objects.get(pk=show_image)

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
        context['image_quality_choices'] = ProcessedImage.IMAGE_QUALITY_CHOICES

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
        id_max = ProcessedImage.objects.filter(task_id=task_id, user=request.user).aggregate(Max('id'))['id__max']
        ProcessedImage.objects.get(pk=id_max).delete()
        return redirect('classification:label_image', task_id=task_id)
    except ProcessedImage.DoesNotExist:
        raise Http404('Does not exist')
