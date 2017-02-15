from django.contrib import messages
from django.http import QueryDict
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.template.defaulttags import register
from django.utils.safestring import mark_safe

from common.exporter import find_all_exporters
from common.utility import get_image_as_http_response
from common.importer import find_all_importers
from common.search_filters import SearchFilter
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

import fnmatch
import os

from .forms import *
from .models import *
from common.user import is_annotater


def get_task_statistics(tasks, user):
    for task in tasks:
        task.total_number_of_images = Image.objects.filter(subject__dataset__task=task.id).count()
        task.number_of_annotated_images = ProcessedImage.objects.filter(task=task.id).count()
        if task.total_number_of_images == 0:
            task.percentage_finished = 0
        else:
            task.percentage_finished = round(task.number_of_annotated_images*100 /
                                             task.total_number_of_images, 1)
        # Check if user has processed any
        task.started = ProcessedImage.objects.filter(task=task, user=user).count() > 0
        task.finished = task.number_of_annotated_images == task.total_number_of_images


def index(request):
    context = {}

    if is_annotater(request.user):
        # Show only tasks assigned to this user
        tasks = Task.objects.filter(user=request.user)
        get_task_statistics(tasks, request.user)
        context['tasks'] = tasks
        return render(request, 'annotationweb/index_annotater.html', context)
    else:
        # Admin page
        # Classification tasks
        tasks = Task.objects.all()
        get_task_statistics(tasks, request.user)
        context['tasks'] = tasks

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
        available_exporters = find_all_exporters(task.type)
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

    available_exporters = find_all_exporters(task.type)
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


@staff_member_required
def import_data(request, dataset_id):
    try:
        dataset = Dataset.objects.get(pk=dataset_id)
    except Dataset.DoesNotExist:
        raise Http404('Dataset does not exist')

    if request.method == 'POST':
        importer_index = int(request.POST['importer'])
        return redirect('import_options', dataset_id=dataset.id, importer_index=importer_index)
    else:
        available_importers = find_all_importers()
        return render(request, 'annotationweb/choose_importer.html', {'importers': available_importers, 'dataset': dataset})


@staff_member_required
def import_options(request, dataset_id, importer_index):
    try:
        dataset = Dataset.objects.get(pk=dataset_id)
    except Dataset.DoesNotExist:
        raise Http404('Dataset does not exist')

    available_importers = find_all_importers()
    importer = available_importers[int(importer_index)]()
    importer.dataset = dataset

    if request.method == 'POST':
        form = importer.get_form(data=request.POST)
        if form.is_valid():
            success, message = importer.import_data(form)
            if success:
                messages.success(request, 'Import finished: ' + message)
            else:
                messages.error(request, 'Import failed: ' + message)

            return redirect('index')
    else:
        # Get unbound form
        form = importer.get_form()

    return render(request, 'annotationweb/import_options.html', {'form': form, 'importer_index': importer_index, 'dataset': dataset})


def show_image(request, image_id):
    try:
        image = Image.objects.get(pk=image_id)
    except Image.DoesNotExist:
        raise Http404('Image does not exist')

    return get_image_as_http_response(image.filename)


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
def new_label(request):
    if request.method == 'POST':
        form = LabelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = LabelForm()
    context = {'form': form}

    return render(request, 'annotationweb/new_label.html', context)


@staff_member_required
def delete_task(request, task_id):
    # TODO do cleanup after deleting task?
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return Http404('Task not found')

    if request.method == 'POST':
        if request.POST['choice'] == 'Yes':
            task.delete()
            messages.success(request, 'The task ' + task.name + ' was deleted.')
        return redirect('index')
    else:
        return render(request, 'annotationweb/delete_task.html', {'task': task})


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
def delete_dataset(request, dataset_id):
    try:
        dataset = Dataset.objects.get(pk=dataset_id)
    except Dataset.DoesNotExist:
        return Http404('Dataset not found')

    if request.method == 'POST':
        if request.POST['choice'] == 'Yes':
            dataset.delete()
            messages.success(request, 'Dataset ' + dataset.name + ' was deleted.')
        return redirect('datasets')
    else:
        return render(request, 'annotationweb/delete_dataset.html', {'dataset': dataset})


def get_start_and_total_frames(file_format):
    # Find start_number and total number of frames automatically
    i = 0
    # Start frame can either be 0 or 1
    start_frame = None
    nr_of_frames = 0
    while True:
        exists = False
        if os.path.isfile(file_format.replace('#', str(i))):
            exists = True
            nr_of_frames += 1
        if start_frame is None:
            if exists:
                start_frame = i
            elif i > 1:
                break
        else:
            if not exists:
                break
        i += 1

    return start_frame, nr_of_frames


@staff_member_required
def add_image_sequence(request, subject_id):
    try:
        subject = Subject.objects.get(pk=subject_id)
    except Subject.DoesNotExist:
        raise Http404('Subject does not exist')

    if request.method == 'POST':
        form = ImageSequenceForm(request.POST)
        if form.is_valid():
            new_image_sequence = form.save(commit=False)  # Create new model, but don't save to DB
            start_frame, total_nr_of_frames = get_start_and_total_frames(new_image_sequence.format)
            print(start_frame, total_nr_of_frames)
            if start_frame is None:
                messages.error(request, 'No data existed with the provided filename format.')
            else:
                new_image_sequence.nr_of_frames = total_nr_of_frames
                new_image_sequence.start_frame_nr = start_frame
                new_image_sequence.subject = subject

                if request.POST['frame_selection'] == 'manual':
                    new_image_sequence.save()  # Save to db
                    return redirect('add_key_frames', new_image_sequence.id)
                elif request.POST['frame_selection'] == 'every_n_frame':
                    try:
                        frame_step = int(request.POST['frame_step'])
                        frame_start = int(request.POST['frame_start'])
                    except:
                        messages.error(request, 'No input given to every X frame.')
                    if frame_step <= 0 or frame_step >= new_image_sequence.nr_of_frames or frame_start < 0 \
                            or frame_start >= new_image_sequence.nr_of_frames:
                        messages.error(request, 'Incorrect frame step or start nr.')
                    else:
                        new_image_sequence.save()  # Save to db

                        # Add every frame_step
                        for frame_nr in range(frame_start, new_image_sequence.nr_of_frames, frame_step):
                            # Create image
                            image = Image()
                            image.filename = new_image_sequence.format.replace('#', str(frame_nr))
                            image.subject = subject
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

    return render(request, 'annotationweb/add_image_sequence.html', {'form': form, 'subject': subject})


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
                image.subject = image_sequence.subject
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

    return get_image_as_http_response(filename)


@staff_member_required()
def dataset_details(request, dataset_id):
    try:
        dataset = Dataset.objects.get(pk=dataset_id)
    except Dataset.DoesNotExist:
        return Http404('The dataset does not exist')

    return render(request, 'annotationweb/dataset_details.html', {'dataset': dataset})


@staff_member_required()
def new_subject(request, dataset_id):
    try:
        dataset = Dataset.objects.get(pk=dataset_id)
    except Dataset.DoesNotExist:
        return Http404('The dataset does not exist')

    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save(commit=False)
            subject.dataset = dataset
            subject.save()
            messages.success(request, 'Subject added')
            return redirect('dataset_details', dataset.id)
    else:
        form = SubjectForm()

    return render(request, 'annotationweb/new_subject.html', {'dataset': dataset, 'form': form})


@staff_member_required()
def delete_subject(request, subject_id):
    try:
        subject = Subject.objects.get(pk=subject_id)
    except Subject.DoesNotExist:
        return Http404('The subject does not exist')

    if request.method == 'POST':
        if request.POST['choice'] == 'Yes':
            subject.delete()
            messages.success(request, 'The subject ' + subject.name + ' was deleted.')
        return redirect('dataset_details', subject.dataset.id)
    else:
        return render(request, 'annotationweb/delete_subject.html', {'subject': subject})


def task_description(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return Http404('The task does not exist')

    if task.type == task.CLASSIFICATION:
        url = reverse('classification:label_image', args=[task_id])
    elif task.type == task.SEGMENTATION:
        url = reverse('segmentation:segment_image', args=[task_id])
    elif task.type == task.BOUNDING_BOX:
        url = reverse('boundingbox:process_image', args=[task_id])
    elif task.type == task.LANDMARK:
        url = reverse('landmark:process_image', args=[task_id])
    else:
        raise NotImplementedError()

    return render(request, 'annotationweb/task_description.html', {'task': task, 'continue_url': url})


@register.simple_tag
def url_replace(request, field, value):

    dict_ = request.GET.copy()

    dict_[field] = value

    return dict_.urlencode()


def reset_filters(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return Http404('The task does not exist')

    search_filters = SearchFilter(request, task)
    search_filters.delete()
    return redirect('task', task_id)


def task(request, task_id):
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return Http404('The task does not exist')

    search_filters = SearchFilter(request, task)

    if request.method == 'POST':
        form = search_filters.create_form(data=request.POST)
    else:
        form = search_filters.create_form()

    queryset = Image.objects.all()

    # Get all processed images for given task
    sort_by = search_filters.get_value('sort_by')
    subjects_selected = search_filters.get_value('subject')
    users_selected = search_filters.get_value('user')
    image_quality = search_filters.get_value('image_quality')
    metadata = search_filters.get_value('metadata')

    if len(metadata) > 0:
        metadata_dict = {}
        for item in metadata:
            parts = item.split(': ')
            if len(parts) != 2:
                raise Exception('Error: must be 2 parts')
            name = parts[0]
            value = parts[1]
            if name in metadata_dict.keys():
                metadata_dict[name].append(value)
            else:
                metadata_dict[name] = [value]

        for name, values in metadata_dict.items():
            queryset = queryset.filter(
                metadata__name=name,
                metadata__value__in=values
            )

    if sort_by == ImageListForm.SORT_IMAGE_ID:
        queryset = queryset.filter(
            subject__dataset__task=task,
            subject__in=subjects_selected
        )
    elif sort_by == ImageListForm.SORT_NOT_ANNOTATED_IMAGE_ID:
        queryset = queryset.filter(
            subject__dataset__task=task,
            subject__in=subjects_selected
        ).exclude(processedimage__task=task)
    else:
        if task.type == Task.CLASSIFICATION:
            labels_selected = search_filters.get_value('label')
            queryset = queryset.filter(
                processedimage__image_quality__in=image_quality,
                processedimage__task=task,
                processedimage__imagelabel__label__in=labels_selected,
                processedimage__user__in=users_selected,
                subject__in=subjects_selected,
            )
        else:
            queryset = queryset.filter(
                processedimage__image_quality__in=image_quality,
                processedimage__task=task,
                processedimage__user__in=users_selected,
                subject__in=subjects_selected
            )
        if sort_by == ImageListForm.SORT_DATE_DESC:
            queryset = queryset.order_by('-processedimage__date')
        else:
            queryset = queryset.order_by('processedimage__date')

    paginator = Paginator(queryset, 12)
    page = request.GET.get('page')
    try:
        images = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        images = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        images = paginator.page(paginator.num_pages)

    for image in images:
        # Check if image is annotated
        try:
            annotation = ProcessedImage.objects.get(image=image, task=task)
            image.annotation = annotation
        except:
            pass

    return_url = reverse('task', kwargs={'task_id': task_id})
    if page is not None:
        return_url += '?page=' + str(page)
    request.session['return_to_url'] = return_url

    return render(request, 'annotationweb/task.html', {'images': images, 'task': task, 'form': form})


def get_redirection(task):
    if task.type == Task.CLASSIFICATION:
        return 'classification:label_image'
    elif task.type == Task.BOUNDING_BOX:
        return 'boundingbox:process_image'
    elif task.type == Task.SEGMENTATION:
        return 'segmentation:segment_image'
    elif task.type == Task.LANDMARK:
        return 'landmark:process_image'


# @register.simple_tag
# def urlencode_dict(dict):
#     print(dict)
#     url = ''
#     if len(dict) > 0:
#         first = True
#         for key, value_list in dict.items():
#             print(value_list)
#             if type(value_list) is not list:
#                 value_list = [value_list]
#             for value in value_list:
#                 if first:
#                     url += '?'
#                     first = False
#                 else:
#                     url += '&'
#
#                 url += key + '=' + str(value)
#
#     return mark_safe(url)


def annotate_next_image(request, task_id):
    # Find the task type and redirect
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return Http404('The task does not exist')

    url = reverse(get_redirection(task), kwargs={'task_id': task.id})
    return redirect(url + '?' + request.GET.urlencode())


def annotate_image(request, task_id, image_id):
    # Find the task type and redirect
    try:
        task = Task.objects.get(pk=task_id)
    except Task.DoesNotExist:
        return Http404('The task does not exist')

    url = reverse(get_redirection(task), kwargs={'task_id': task.id, 'image_id': image_id})
    return redirect(url + '?' + request.GET.urlencode())
