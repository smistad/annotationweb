from django.shortcuts import render, redirect
from .forms import *
from django.contrib import messages
import random

def new_task(request):
    if request.method == 'POST':
        form = SegmentationTaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New task was created.')
            return redirect('annotation:index')
    else:
        form = SegmentationTaskForm()

    return render(request, 'segmentation/new_task.html', {'form': form})

def delete_task(request, task_id):
    pass


def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.filter(dataset__segmentationtask = task_id).exclude(segmentedimage__task = task_id)
    return unlabeled_images[random.randrange(0, len(unlabeled_images))]

def segment_image(request, task_id):
    context = {}
    context['dark_style'] = 'yes'
    try:
        task = SegmentationTask.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    if request.method == 'POST':
        pass
        # TODO Save segmentation


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
        context['number_of_labeled_images'] = Image.objects.filter(labeledimage__label__task = task_id).count()
        context['total_number_of_images'] = Image.objects.filter(dataset__task = task_id).count()
        context['percentage_finished'] = round(context['number_of_labeled_images']*100 / context['total_number_of_images'], 1)

        print('Got the following random image: ', image.filename)
        return render(request, 'segmentation/segment_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to label.')
        return redirect('annotation:index')
