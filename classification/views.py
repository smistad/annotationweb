from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import Http404
from django.db.models import Max

from common.task import get_next_unprocessed_image, get_next_image, get_previous_image

from .models import *
from annotationweb.models import Image, Task, ProcessedImage


def label_next_image(request, task_id):
    return label_image(request, task_id, None)


def label_image(request, task_id, image_id):
    context = {}
    context['dark_style'] = 'yes'
    try:
        task = Task.objects.get(pk=task_id, user=request.user)
        labels = Label.objects.filter(task=task)
    except Task.DoesNotExist:
        raise Http404("Task does not exist or user has no access to the task")

    if request.method == 'POST':
        # Check that quality is checked
        if 'quality' not in request.POST:
            messages.error(request, 'ERROR: You must select image quality.')
        else:
            # Save new label

            # Delete any previous labelings
            previous_labels = ImageLabel.objects.filter(image__image_id=image_id, image__task=task, image__user=request.user)
            previous_labels.delete()
            try:
                previous_processed_image = ProcessedImage.objects.get(image_id=image_id, task=task, user=request.user)
                previous_processed_image.delete()
            except:
                pass

            processed_image = ProcessedImage()
            processed_image.image_id = image_id
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
            image_id = get_next_image(task, image_id)

    # Get random unlabeled image
    try:
        if image_id is None:
            image = get_next_unprocessed_image(task)
        else:
            image = Image.objects.get(pk=image_id)
        print('Got the following image: ', image.id, image.filename)

        # Check if image has been labeled
        processed = ImageLabel.objects.filter(image__image=image, image__task=task)
        if processed.exists():
            context['chosen_label'] = processed[0].label.id
            context['chosen_quality'] = processed[0].image.image_quality
        else:
            context['chosen_label'] = -1
            context['chosen_quality'] = -1

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

        # Get all labels for this task
        if len(labels) == 0:
            raise Http404('No labels found!')
        context['labels'] = labels
        return render(request, 'classification/label_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to label.')
        return redirect('index')
