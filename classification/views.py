from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.db.models import Max
from django.contrib.admin.views.decorators import staff_member_required

import random

from .models import *


def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.filter(dataset__task=task_id).exclude(classifiedimage__task=task_id)
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
        labeled_image = ClassifiedImage()
        labeled_image.image_id = request.POST['image_id']
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
        context['number_of_labeled_images'] = Image.objects.filter(classifiedimage__task=task_id).count()
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
        id_max = ClassifiedImage.objects.filter(task_id=task_id).aggregate(Max('id'))['id__max']
        ClassifiedImage.objects.get(pk=id_max).delete()
        return redirect('classification:label_image', task_id=task_id)
    except Task.DoesNotExist:
        raise Http404('Image label does not exist')


@staff_member_required
def export_labeled_dataset(request, task_id):
    context = {}
    # Validate form
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404('Task does not exist')
    context['task'] = task

    # Get all possible tasks
    context['datasets'] = Dataset.objects.filter(task__id = task_id)

    if request.method == 'POST':
        datasets = request.POST.getlist('datasets')

        if len(datasets) == 0:
            messages.error(request, 'You must select at least 1 dataset')
            return render(request, 'annotationweb/export_labeled_dataset.html', context)

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
            return render(request, 'annotationweb/export_labeled_dataset.html', context)


        # Create label file
        label_file = open(os.path.join(path, 'labels.txt'), 'w')
        labels = Label.objects.filter(task = task)
        labelDict = {}
        counter = 0
        for label in labels:
            label_file.write(label.name + '\n')
            labelDict[label.name] = counter
            counter += 1
        label_file.close()

        # Create file_list.txt file
        file_list = open(os.path.join(path, 'file_list.txt'), 'w')
        labeled_images = LabeledImage.objects.filter(label__task = task, image__dataset__in = datasets)
        for labeled_image in labeled_images:
            name = labeled_image.image.filename
            image_filename = name[name.rfind('/')+1:]
            dataset_path = os.path.join(path, labeled_image.image.dataset.name)
            try:
                os.mkdir(dataset_path) # Make dataset path if doesn't exist
            except:
                pass
            new_filename = os.path.join(dataset_path, image_filename)
            copyfile(name, new_filename)
            file_list.write(new_filename + ' ' + str(labelDict[labeled_image.label.name]) + '\n')

        file_list.close()

        messages.success(request, 'The labeled dataset was successfully exported to ' + path)
        return redirect('annotation:index')


    return render(request, 'annotationweb/export_labeled_dataset.html', context)
