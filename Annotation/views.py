from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.db.models import Max

import fnmatch
import os
import random

import PIL, PIL.Image
from io import BytesIO
from shutil import copyfile, rmtree

from .forms import *
from .models import *

import numpy as np

def index(request):
    context = {}
    tasks = Task.objects.all()
    for task in tasks:
        task.total_number_of_images = Image.objects.filter(dataset__task = task.id).count()
        if(task.total_number_of_images == 0):
            task.percentage_finished = 0
        else:
            task.percentage_finished = round(Image.objects.filter(labeledimage__label__task = task.id).count()*100 / task.total_number_of_images, 1)
    context['tasks'] = tasks
    return render(request, 'annotation/index.html', context)

# Crawl recursively in path to find all images and add them to db
def import_images(path, dataset):
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, '*.png'):
            image = Image()
            image.filename = os.path.join(root, filename)
            image.dataset = dataset
            image.save()
            print('Saved image ', image.filename)

def import_local_dataset(request):
    if request.method == 'POST':
        # Process form
        form = ImportLocalDatasetForm(request.POST)
        if form.is_valid():
            # Check if path exists
            path = form.cleaned_data['path']
            if os.path.isdir(path):
                dataset = Dataset()
                dataset.name = form.cleaned_data['name']
                dataset.save()
                import_images(path, dataset)
                messages.success(request, 'Successfully imported dataset')
                return redirect('annotation:index')
            else:
                form.add_error(field='path', error='The path doesn\'t exist.')
    else:
        form = ImportLocalDatasetForm() # Create blank form

    return render(request, 'annotation/import_local_dataset.html', {'form': form})

def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.filter(dataset__task = task_id).exclude(labeledimage__label__task = task_id)
    return unlabeled_images[random.randrange(0, len(unlabeled_images))]

def label_images(request, task_id):
    context = {}
    context['dark_style'] = 'yes'
    try:
        task = Task.objects.get(pk=task_id)
        labels = Label.objects.filter(task = task)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    if request.method == 'POST':
        # Save new label
        labeled_image = LabeledImage()
        labeled_image.image_id = request.POST['image_id']
        for label in labels:
            if request.POST.__contains__(label.name):
                labeled_image.label = label

        labeled_image.save()

    # Get random unlabeled image
    try:
        image = pick_random_image(task_id)
        context['image'] = image
        context['task'] = task
        context['number_of_labeled_images'] = Image.objects.filter(labeledimage__label__task = task_id).count()
        context['total_number_of_images'] = Image.objects.filter(dataset__task = task_id).count()
        context['percentage_finished'] = round(context['number_of_labeled_images']*100 / context['total_number_of_images'], 1)

        # Get all labels for this task
        context['labels'] = labels
        print('Got the following random image: ', image.filename)
        return render(request, 'annotation/label_image.html', context)
    except ValueError:
        messages.info(request, 'This task is finished, no more images to label.')
        return redirect('annotation:index')


def show_image(request, image_id):
    try:
        image = Image.objects.get(pk=image_id)
    except Image.DoesNotExist:
        raise Http404('Image does not exist')

    buffer = BytesIO()
    pil_image = PIL.Image.open(image.filename)
    pil_image.save(buffer, "PNG")

    return HttpResponse(buffer.getvalue(), content_type="image/png")


def scale(array, factor):
    array = array.astype('float')
    for i in range(3):
        array[..., i] *= factor

    array[array > 255] = 255
    array[array < 0] = 0
    return array

def intensityScaling(image, factor):
    arr = np.array(image)
    return PIL.Image.fromarray(scale(arr, factor).astype('uint8'), 'RGB')

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
        mirror = request.POST.get('mirror', False)
        intensityScale = request.POST.get('intensity_scale', False)
        scalingFactors = [0.9, 1.1]

        if len(datasets) == 0:
            messages.error(request, 'You must select at least 1 dataset')
            return render(request, 'annotation/export_labeled_dataset.html', context)

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
            return render(request, 'annotation/export_labeled_dataset.html', context)


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

            if mirror:
                flippedImage = PIL.Image.open(new_filename).transpose(PIL.Image.FLIP_LEFT_RIGHT)
                # Save flipped image
                flippedFilename = os.path.join(dataset_path, 'flipped_' + image_filename)
                flippedImage.save(flippedFilename)
                file_list.write(flippedFilename + ' ' + str(labelDict[labeled_image.label.name]) + '\n')
            if intensityScale:
                originalImage = PIL.Image.open(new_filename)
                if len(scalingFactors) > 0:
                    for scalingFactor in scalingFactors:
                        newImage = originalImage.copy()
                        newImage = intensityScaling(newImage, scalingFactor)
                        filename = os.path.join(dataset_path, 'intensity_' + str(scalingFactor) + image_filename)
                        newImage.save(filename)
                        file_list.write(filename + ' ' + str(labelDict[labeled_image.label.name]) + '\n')

                        if mirror:
                            newImage = flippedImage.copy()
                            newImage = intensityScaling(newImage, scalingFactor)
                            filename = os.path.join(dataset_path, 'intensity_' + str(scalingFactor) + '_flipped_' + image_filename)
                            newImage.save(filename)
                            file_list.write(filename + ' ' + str(labelDict[labeled_image.label.name]) + '\n')
        file_list.close()

        messages.success(request, 'The labeled dataset was successfully exported to ' + path)
        return redirect('annotation:index')


    return render(request, 'annotation/export_labeled_dataset.html', context)

def new_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('annotation:index')
    else:
        form = TaskForm()
    context = {'form': form}

    return render(request, 'annotation/new_task.html', context)

def delete_task(request, task_id):
    if request.method == 'POST':
        Task.objects.get(pk = task_id).delete()
        return redirect('annotation:index')
    else:
        return render(request, 'annotation/delete_task.html', {'task_id': task_id})

def undo_image_label(request, task_id):
    try:
        id_max = LabeledImage.objects.filter(label__task_id=task_id).aggregate(Max('id'))['id__max']
        LabeledImage.objects.get(pk=id_max).delete()
        return redirect('annotation:label_image', task_id=task_id)
    except Task.DoesNotExist:
        raise Http404('Image label does not exist')

