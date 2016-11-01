from django.conf import settings
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
from common.utility import get_image_as_http_response
import common.task


def segment_next_image(request, task_id):
    return segment_image(request, task_id, None)


def segment_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(task_id, Task.SEGMENTATION, image_id)
        context['javascript_files'] = ['segmentation/segmentation.js']

        return render(request, 'segmentation/segment_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')


def save_segmentation(request):
    if request.method != 'POST':
        raise Http404('')

    # Save the image

    try:
        if 'quality' not in request.POST:
            raise Exception('ERROR: You must select image quality.')

        image_id = int(request.POST['image_id'])
        task_id = int(request.POST['task_id'])

        # Delete old segmentation if it exists
        processed_images = ProcessedImage.objects.filter(image_id=image_id, task_id=task_id)
        processed_images.delete()

        # Save to DB
        processed_image = ProcessedImage()
        processed_image.image_id = image_id
        processed_image.task_id = task_id
        processed_image.user = request.user
        processed_image.image_quality = request.POST['quality']
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


def show_segmentation(request, task_id, image_id):
    try:
        processed_image = ProcessedImage.objects.get(task_id=task_id, image_id=image_id)
    except ProcessedImage.DoesNotExist:
        return Http404('')

    filename = os.path.join(os.path.join(os.path.join(settings.PROJECT_PATH, 'segmentations'), str(task_id)), str(processed_image.id) + '.png')
    print(filename)
    return get_image_as_http_response(filename)
