from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from .forms import *
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
import random
from io import StringIO, BytesIO
import base64
from annotationweb.settings import PROJECT_PATH
from common.metaimage import *
import numpy as np
from annotationweb.models import Task, Image, ProcessedImage, Label


def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.filter(subject__dataset__task=task_id).exclude(processedimage__task=task_id)
    return unlabeled_images[random.randrange(0, len(unlabeled_images))]


def segment_image(request, task_id):
    context = {}
    context['dark_style'] = 'yes'
    context['javascript_files'] = ['segmentation/segmentation.js']
    try:
        task = Task.objects.get(pk=task_id, type=Task.SEGMENTATION)
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
        processed_image = ProcessedImage()
        processed_image.image_id = int(request.POST['image_id'])
        processed_image.task_id = int(request.POST['task_id'])
        processed_image.user = request.user
        processed_image.save()


        # Save segmentation image to disk
        base_path = PROJECT_PATH + '/segmentations/' + str(processed_image.task_id) + '/'
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
        image.save(base_path + str(processed_image.id) + '.png')

        # Convert color image to single channel label image
        # Get all labels for this task
        # Go through each pixel, match color with label and choose label id from that
        color_pixels = np.asarray(image)

        # Get positions of all non-background pixels
        grayscaleimage = image.convert('L')
        X, Y = np.nonzero(np.asarray(grayscaleimage))

        labels = Label.objects.filter(task__id=processed_image.task_id)
        width = color_pixels.shape[0]
        height = color_pixels.shape[1]
        pixels = np.zeros((width, height)).astype(np.uint8)
        for i in range(len(X)):
            x = X[i]
            y = Y[i]
            min_distance = 9999999
            min_label = 0
            for label in labels:
                color = np.asarray([label.color_red, label.color_green, label.color_blue])
                if np.linalg.norm(color_pixels[x, y, 0:3] - color) < min_distance:
                    min_distance = np.linalg.norm(color_pixels[x, y, 0:3] - color)
                    min_label = label.id
            pixels[x, y] = min_label


        # Store as metaimage
        writer = MetaImage(data=pixels)
        writer.write(base_path + str(processed_image.id) + '.mhd')

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

