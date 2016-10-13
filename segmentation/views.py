from django.shortcuts import render, redirect
from .forms import *
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
import random
import os
from io import StringIO, BytesIO
import base64
import PIL
from annotationweb.settings import PROJECT_PATH
from common.metaimage import *
import numpy as np
from shutil import copyfile, rmtree


def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.filter(dataset__task=task_id).exclude(segmentedimage__task=task_id)
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

        # Convert color image to single channel label image
        # Get all labels for this task
        # Go through each pixel, match color with label and choose label id from that
        color_pixels = np.asarray(image)

        # Get positions of all non-background pixels
        grayscaleimage = image.convert('L')
        X, Y = np.nonzero(np.asarray(grayscaleimage))

        labels = Label.objects.filter(task__id=result.task_id)
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
        writer.write(base_path + str(result.id) + '.mhd')

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


# Export segmentation results for a given task
def export(request, task_id):
    context = {}
    # Validate form
    try:
        task = Task.objects.get(pk=task_id, type=Task.SEGMENTATION)
    except Task.DoesNotExist:
        raise Http404('Task does not exist')
    context['task'] = task

    # Get all possible tasks
    context['datasets'] = Dataset.objects.filter(task__id=task_id)

    if request.method == 'POST':
        datasets = request.POST.getlist('datasets')

        if len(datasets) == 0:
            messages.error(request, 'You must select at least 1 dataset')
            return render(request, 'segmentation/export.html', context)

        # Create dir, delete old if it exists
        path = request.POST['path']
        try:
            os.stat(path)
            rmtree(path)
        except:
            pass
        try:
            os.mkdir(path)
        except:
            messages.error(request, 'Invalid path')
            return render(request, 'segmentation/export.html', context)

        segmented_images = SegmentedImage.objects.filter(task=task_id, image__dataset__in=datasets)
        for segmented_image in segmented_images:
            name = segmented_image.image.filename
            image_filename = name[name.rfind('/')+1:]
            dataset_path = os.path.join(path, segmented_image.image.dataset.name)
            try:
                os.mkdir(dataset_path)  # Make dataset path if doesn't exist
            except:
                pass

            # Copy image
            metaimage = MetaImage(filename=name)
            image_id = segmented_image.image.pk
            metaimage.write(os.path.join(dataset_path, str(image_id) + '.mhd'))

            # Copy all segmentation files
            segmentation_filename = os.path.join(PROJECT_PATH, os.path.join('segmentations', os.path.join(str(task_id), str(segmented_image.id) + '.mhd')))
            new_segmentation_filename = os.path.join(dataset_path, str(image_id) + '_segmentation.mhd')
            metaimage = MetaImage(filename=segmentation_filename)
            metaimage.write(new_segmentation_filename)

        messages.success(request, 'The segmentation dataset was successfully exported to ' + path)
        return redirect('annotation:index')


    return render(request, 'segmentation/export.html', context)
