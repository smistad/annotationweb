from django.shortcuts import render, redirect
from .forms import *
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
import random
import os
from io import StringIO, BytesIO
import base64
import PIL
from AnnotationWeb.settings import PROJECT_PATH
from common.metaimage import MetaImageReader, MetaImageWriter
import numpy as np

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
        context['number_of_labeled_images'] = Image.objects.filter(segmentedimage__task=task_id).count()
        context['total_number_of_images'] = Image.objects.filter(dataset__task=task_id).count()
        context['percentage_finished'] = round(context['number_of_labeled_images']*100 / context['total_number_of_images'], 1)

        print('Got the following random image: ', image.filename)
        return render(request, 'segmentation/segment_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('annotation:index')


def save_segmentation(request):
    if request.method != 'POST':
        raise Http404('')

    # Save the image

    try:
        # Save to DB
        result = SegmentedImage()
        result.image_id = int(request.POST['image_id'])
        result.task_id = int(request.POST['task_id'])
        result.save()

        # Save segmentation image to disk
        base_path = PROJECT_PATH + '/segmentations/' + str(result.task_id) + '/'
        try:
            os.makedirs(base_path)
        except:
            # Path already exists
            pass
        image_string = request.POST['image']
        image_string = image_string.replace('data:image/png;base64,', '')
        image_string = image_string.replace(' ', '+')
        image_string = BytesIO(base64.b64decode(image_string))

        # Store as png
        image = PIL.Image.open(image_string)
        image.save(base_path + str(result.id) + '.png')

        # TODO have to convert colors into labels

        # Store as metaimage
        writer = MetaImageWriter(base_path + str(result.id) + '.mhd', np.asarray(image))
        writer.write()

        response = {
            'success': 'true',
            'message': 'Complete'
        }
        messages.success(request, 'Segmentation was saved')
    except Exception as e:
        response = {
            'success': 'false',
            'message': str(e)
        }

    return JsonResponse(response)