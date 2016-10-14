from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.db.models import Max
from django.contrib.admin.views.decorators import staff_member_required
import common.exporter

import fnmatch
import os
import random

import PIL, PIL.Image
from io import BytesIO
from shutil import copyfile, rmtree

from .forms import *
from .models import *
from common.metaimage import MetaImage
from common.user import is_annotater

import numpy as np


def get_task_statistics(tasks):
    for task in tasks:
        task.total_number_of_images = Image.objects.filter(dataset__task=task.id).count()
        if(task.total_number_of_images == 0):
            task.percentage_finished = 0
        else:
            task.percentage_finished = round(ProcessedImage.objects.filter(task=task.id).count()*100 / task.total_number_of_images, 1)


def index(request):
    context = {}

    if is_annotater(request.user):
        # Show only tasks own by this user
        tasks = Task.objects.filter(user=request.user)
        get_task_statistics(tasks)
        context['tasks'] = tasks
        return render(request, 'annotationweb/index_annotater.html', context)
    else:
        # Admin page
        # Classification tasks
        tasks = Task.objects.filter(type=Task.CLASSIFICATION)
        get_task_statistics(tasks)
        context['tasks'] = tasks

        # Segmentation tasks
        segmentation_tasks = Task.objects.filter(type=Task.SEGMENTATION)
        get_task_statistics(segmentation_tasks)
        context['segmentation_tasks'] = segmentation_tasks

        # Bounding box tasks
        bb_tasks = Task.objects.filter(type=Task.BOUNDING_BOX)
        get_task_statistics(bb_tasks)
        context['boundingbox_tasks'] = bb_tasks

        return render(request, 'annotationweb/index_admin.html', context)


@staff_member_required
def export(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404('Task does not exist')

    if request.method == 'POST':
        exporter_index = int(request.POST['exporter'])
        return redirect('export_options', task_id=task.id, exporter_index=exporter_index)
    else:
        available_exporters = common.exporter.find_all_exporters(task.type)
        # If only 1 exporter exists for this type, use that one
        if len(available_exporters) == 1:
            return redirect('export_options', task_id=task.id, exporter_index=0)
        else:
            return render(request, 'annotationweb/choose_exporter.html', {'exporters': available_exporters, 'task': task})


@staff_member_required
def export_options(request, task_id, exporter_index):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        raise Http404('Task does not exist')

    available_exporters = common.exporter.find_all_exporters(task.type)
    exporter = available_exporters[int(exporter_index)]()
    exporter.task = task

    if request.method == 'POST':
        form = exporter.get_form(data=request.POST)
        if form.is_valid():
            success, message = exporter.export(form)
            if success:
                messages.success(request, 'Export finished: ' + message)
            else:
                messages.error(request, 'Export failed: ' + message)

            return redirect('index')
    else:
        # Get unbound form
        form = exporter.get_form()

    return render(request, 'annotationweb/export_options.html', {'form': form, 'exporter_index': exporter_index, 'task': task})


# Crawl recursively in path to find all images and add them to db
def import_images(path, dataset):
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, '*.png'):
            image = Image()
            image.filename = os.path.join(root, filename)
            image.dataset = dataset
            image.save()
            print('Saved image ', image.filename)


@staff_member_required
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
                return redirect('index')
            else:
                form.add_error(field='path', error='The path doesn\'t exist.')
    else:
        form = ImportLocalDatasetForm() # Create blank form

    return render(request, 'annotationweb/import_local_dataset.html', {'form': form})


def show_image(request, image_id):
    try:
        image = Image.objects.get(pk=image_id)
    except Image.DoesNotExist:
        raise Http404('Image does not exist')

    buffer = BytesIO()
    pil_image = PIL.Image.open(image.filename)
    pil_image.save(buffer, "PNG")

    return HttpResponse(buffer.getvalue(), content_type="image/png")





@staff_member_required
def new_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = TaskForm()
    context = {'form': form}

    return render(request, 'annotationweb/new_task.html', context)


@staff_member_required
def delete_task(request, task_id):
    if request.method == 'POST':
        Task.objects.get(pk = task_id).delete()
        return redirect('index')
    else:
        return render(request, 'annotationweb/delete_task.html', {'task_id': task_id})


@staff_member_required
def datasets(request):
    # Show all datasets
    context = {}
    context['datasets'] = Dataset.objects.all()

    return render(request, 'annotationweb/datasets.html', context)

@staff_member_required
def new_dataset(request):
    if request.method == 'POST':
        form = DatasetForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New dataset created')
            return redirect('datasets')
    else:
        form = DatasetForm()

    return render(request, 'annotationweb/new_dataset.html', {'form': form})


@staff_member_required
def delete_dataset(request):
    pass

@staff_member_required
def add_image_sequence(request, dataset_id):
    try:
        dataset = Dataset.objects.get(pk=dataset_id)
    except Dataset.DoesNotExist:
        raise Http404('Dataset does not exist')

    if request.method == 'POST':
        form = ImageSequenceForm(request.POST)
        if form.is_valid():
            new_image_sequence = form.save(commit=False)  # Create new model, but don't save to DB
            new_image_sequence.dataset = dataset  # Set dataset

            if request.POST['frame_selection'] == 'manual':
                new_image_sequence.save()  # Save to db
                return redirect('add_key_frames', new_image_sequence.id)
            elif request.POST['frame_selection'] == 'every_n_frame':
                try:
                    frame_step = int(request.POST['frame_step'])
                except:
                    messages.error(request, 'No input given to every X frame.')
                if frame_step <= 0 or frame_step >= new_image_sequence.nr_of_frames:
                    messages.error(request, 'Incorrect frame step nr.')
                else:
                    new_image_sequence.save()  # Save to db

                    # Add every frame_step
                    for frame_nr in range(0, new_image_sequence.nr_of_frames, frame_step):
                        # Create image
                        image = Image()
                        image.filename = new_image_sequence.format.replace('#', str(frame_nr))
                        image.dataset = new_image_sequence.dataset
                        image.save()

                        # Create associated key frame
                        key_frame = KeyFrame()
                        key_frame.frame_nr = frame_nr
                        key_frame.image_sequence = new_image_sequence
                        key_frame.image = image
                        key_frame.save()

                    messages.success(request, 'The image sequence and frames were stored.')
                    return redirect('datasets')

    else:
        form = ImageSequenceForm()

    return render(request, 'annotationweb/add_image_sequence.html', {'form': form, 'dataset': dataset})

@staff_member_required
def add_key_frames(request, image_sequence_id):
    try:
        image_sequence = ImageSequence.objects.get(pk=image_sequence_id)
    except ImageSequence.DoesNotExist:
        raise Http404('Image sequence does not exist')

    if request.method == 'POST':
        frame_list = request.POST.getlist('frames')
        if len(frame_list) == 0:
            messages.error(request, 'You must select at least 1 frame')
        else:
            # Add frames to db
            for frame_nr in frame_list:
                # Create image
                image = Image()
                image.filename = image_sequence.format.replace('#', str(frame_nr))
                image.dataset = image_sequence.dataset
                image.save()

                # Create associated key frame
                key_frame = KeyFrame()
                key_frame.frame_nr = int(frame_nr)
                key_frame.image_sequence = image_sequence
                key_frame.image = image
                key_frame.save()

            messages.success(request, 'The image sequence and frames were stored.')
            return redirect('datasets')

    return render(request, 'annotationweb/add_key_frames.html', {'image_sequence': image_sequence})


def show_frame(request, image_sequence_id, frame_nr):
    # Get image sequence the key frame belongs to
    try:
        image_sequence = ImageSequence.objects.get(pk=image_sequence_id)
    except ImageSequence.DoesNotExist:
        raise Http404('Image sequence does not exist')

    filename = image_sequence.format.replace('#', str(frame_nr))

    reader = MetaImage(filename=filename)


    # Convert raw data to image, and then to a http response
    buffer = BytesIO()
    pil_image = reader.get_image()
    pil_image.save(buffer, "PNG")

    return HttpResponse(buffer.getvalue(), content_type="image/png")
