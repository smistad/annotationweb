from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, Http404

import fnmatch
import os
import random

import PIL, PIL.Image
from io import BytesIO
from shutil import copyfile, rmtree

from .forms import *
from .models import *

def index(request):
    context = {}
    tasks = Task.objects.all()
    for task in tasks:
        task.total_number_of_images = Image.objects.filter(dataset = task.dataset).count()
        task.percentage_finished = round(Image.objects.filter(labeledimage__label__task = task.id).count()*100 / task.total_number_of_images, 2)
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
                return HttpResponse('Success!')
            else:
                form.add_error(field='path', error='The path doesn\'t exist.')
    else:
        form = ImportLocalDatasetForm() # Create blank form

    return render(request, 'annotation/import_local_dataset.html', {'form': form})

def pick_random_image(task_id):
    # Want to get an image which is not labeled yet for a given task
    unlabeled_images = Image.objects.exclude(labeledimage__label__task = task_id)
    return unlabeled_images[random.randrange(0, len(unlabeled_images))]

def label_images(request, task_id):
    context = {}
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
    image = pick_random_image(task_id)
    context['image'] = image
    context['task'] = task
    context['number_of_labeled_images'] = Image.objects.filter(labeledimage__label__task = task_id).count()
    context['total_number_of_images'] = Image.objects.filter(dataset = task.dataset).count()
    context['percentage_finished'] = round(context['number_of_labeled_images']*100 / context['total_number_of_images'], 2)

    # Get all labels for this task
    context['labels'] = labels

    print('Got the following random image: ', image.filename)

    return render(request, 'annotation/label_image.html', context)

def show_image(request, image_id):
    try:
        image = Image.objects.get(pk=image_id)
    except Image.DoesNotExist:
        raise Http404('Image does not exist')

    buffer = BytesIO()
    pil_image = PIL.Image.open(image.filename)
    pil_image.save(buffer, "PNG")

    return HttpResponse(buffer.getvalue(), content_type="image/png")

def export_labeled_dataset(request):
    context = {}
    if request.method == 'POST':
        # Validate form
        try:
            task = Task.objects.get(pk=request.POST['task_id'])
        except Task.DoesNotExist:
            raise Http404('Task does not exist')

        # Create dir, delete old if it exists
        path = request.POST['path']
        try:
            os.stat(path)
            rmtree(path)
        except:
            pass
        os.mkdir(path)

        # Create label dirs
        labels = Label.objects.filter(task = task)
        for label in labels:
            os.mkdir(os.path.join(path, label.name))

        labeled_images = LabeledImage.objects.filter(label__task = task)
        for labeled_image in labeled_images:
            name = labeled_image.image.filename
            image_filename = name[name.rfind('/')+1:]
            print('Copying the file ', image_filename)
            copyfile(name, os.path.join(path, os.path.join(labeled_image.label.name, image_filename)))
        context['message'] = 'Done!'

    # Get all possible tasks
    context['tasks'] = Task.objects.all()

    return render(request, 'annotation/export_labeled_dataset.html', context)
