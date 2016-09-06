from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
import random
import json
import os
from shutil import rmtree
from common.metaimage import *
from common.utility import *
from AnnotationWeb.settings import PROJECT_PATH


def new_task(request):
    if request.method == 'POST':
        form = BoundingBoxTaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New task was created.')
            return redirect('annotation:index')
    else:
        form = BoundingBoxTaskForm()

    return render(request, 'boundingbox/new_task.html', {'form': form})


def delete_task(request, task_id):
    pass


def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.filter(dataset__boundingboxtask=task_id).exclude(completedimage__task=task_id)
    return unlabeled_images[random.randrange(0, len(unlabeled_images))]


def process_image(request, task_id):
    context = {}
    context['dark_style'] = 'yes'
    context['javascript_files'] = ['boundingbox/boundingbox.js']
    try:
        task = BoundingBoxTask.objects.get(pk=task_id)
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
        context['number_of_labeled_images'] = Image.objects.filter(completedimage__task=task_id).count()
        context['total_number_of_images'] = Image.objects.filter(dataset__boundingboxtask=task_id).count()
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
        image = CompletedImage()
        image.image_id = int(request.POST['image_id'])
        image.task_id = int(request.POST['task_id'])
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


def export(request, task_id):
    context = {}
    # Validate form
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404('Task does not exist')
    context['task'] = task

    # Get all possible tasks
    context['datasets'] = Dataset.objects.filter(boundingboxtask__id=task_id)

    if request.method == 'POST':
        datasets = request.POST.getlist('datasets')

        if len(datasets) == 0:
            messages.error(request, 'You must select at least 1 dataset')
            return render(request, 'boundingbox/export.html', context)

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
            return render(request, 'boundingbox/export.html', context)

        images = CompletedImage.objects.filter(task=task_id, image__dataset__in=datasets)
        for image in images:
            name = image.image.filename
            image_filename = name[name.rfind('/')+1:]
            create_folder(path)
            create_folder(os.path.join(path, 'images'))
            create_folder(os.path.join(path, 'labels'))

            # Copy image
            metaimage = MetaImage(filename=name)
            image_id = image.image.pk
            pil_image = metaimage.get_image()
            pil_image.save(os.path.join(path, os.path.join('images', str(image_id) + '.png')))

            # Write bounding boxes to labels folder
            boxes = BoundingBox.objects.filter(image=image)
            with open(os.path.join(path, os.path.join('labels', str(image_id) + '.txt')), 'w') as f:
                for box in boxes:
                    object_name = box.label.name
                    x_max = box.x + box.width
                    y_max = box.y + box.height
                    # KITTI format (https://github.com/NVIDIA/DIGITS/blob/digits-4.0/digits/extensions/data/objectDetection/README.md#label-format)
                    f.write('{} 0.0 0 0.0 {} {} {} {} 0.0 0.0 0.0 0.0 0.0 0.0 0.0\n'.format(object_name, box.x, box.y, x_max, y_max, ))


        messages.success(request, 'The bounding box dataset was successfully exported to ' + path)
        return redirect('annotation:index')


    return render(request, 'boundingbox/export.html', context)
