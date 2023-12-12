import json
import random
from django.contrib import messages
from django.http import Http404
from annotationweb.models import Task, ImageAnnotation, Subject, Label, ImageSequence, KeyFrameAnnotation
from annotationweb.forms import ImageListForm
from django.db.models.aggregates import Count
from common.search_filters import SearchFilter
from django.db import transaction
from django.db.models import Q, Exists, OuterRef


class NoMoreImages(Exception):
    """"Raise when no more images to annotate for a given task"""
    pass


def get_next_unprocessed_image(task):
    """
    Get the next unprocessed image related to a task (in random order)
    :param task:
    :return image:
    """
    queryset = ImageSequence.objects.filter(subject__dataset__task=task) # Get all sequences for this task
    # Exclude does that are marked as finished, or not opened at all
    queryset = queryset.exclude(imageannotation__in=ImageAnnotation.objects.filter(task=task, finished=True))
    if not task.user_frame_selection:
        # If user cannot select their own key frames, skip those without a key frame
        queryset = queryset.exclude(imageannotation__keyframeannotation__isnull=True)

    count = queryset.aggregate(count=Count('id'))['count']
    if count == 0:
        raise NoMoreImages
    if task.shuffle_videos:
        index = random.randint(0, count - 1)
    else:
        index = 0

    return queryset.order_by("subject", "format")[index]


# TODO These two functions get_previous and get_next_image are not up to date and thus just return None
# TODO cleanup these to functions, extract common functionality
def get_previous_image(request, task, image):
    try:
        search_filters = SearchFilter(request, task)

        sort_by = search_filters.get_value('sort_by')
        image_quality = search_filters.get_value('image_quality')
        selected_subjects = search_filters.get_value('subject')
        selected_labels = search_filters.get_value('label')
        users_selected = search_filters.get_value('user')
        metadata = search_filters.get_value('metadata')

        queryset = Image.objects.all()

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
            return queryset.filter(
                subject__dataset__task=task,
                subject__in=selected_subjects,
            ).exclude(id__gte=image.id).order_by('-id')[0].id
        else:
            # Get current annotated image
            annotated_image = ProcessedImage.objects.get(task=task, image=image)
            if sort_by == ImageListForm.SORT_DATE_DESC:
                if task.type != Task.CLASSIFICATION:
                    queryset = queryset.filter(
                        processedimage__task=task,
                        processedimage__date__gt=annotated_image.date,
                        processedimage__image_quality__in=image_quality,
                        processedimage__user__in=users_selected,
                        subject__in=selected_subjects,
                    )
                else:
                    queryset = queryset.filter(
                        processedimage__task=task,
                        processedimage__date__gt=annotated_image.date,
                        processedimage__image_quality__in=image_quality,
                        processedimage__imagelabel__label__in=selected_labels,
                        processedimage__user__in=users_selected,
                        subject__in=selected_subjects,
                    )
                return queryset.order_by('processedimage__date')[0].id
            elif sort_by == ImageListForm.SORT_DATE_ASC:
                if task.type != Task.CLASSIFICATION:
                    queryset = queryset.filter(
                        processedimage__task=task,
                        processedimage__date__lt=annotated_image.date,
                        processedimage__image_quality__in=image_quality,
                        processedimage__user__in=users_selected,
                        subject__in=selected_subjects,
                    )
                else:
                    queryset = queryset.filter(
                        processedimage__task=task,
                        processedimage__date__lt=annotated_image.date,
                        processedimage__image_quality__in=image_quality,
                        processedimage__imagelabel__label__in=selected_labels,
                        processedimage__user__in=users_selected,
                        subject__in=selected_subjects,
                    )
                return queryset.order_by('-processedimage__date')[0].id
    except:
        return None


def get_next_image(request, task, image):
    try:
        search_filters = SearchFilter(request, task)

        sort_by = search_filters.get_value('sort_by')
        image_quality = search_filters.get_value('image_quality')
        selected_subjects = search_filters.get_value('subject')
        selected_labels = search_filters.get_value('label')
        users_selected = search_filters.get_value('user')
        metadata = search_filters.get_value('metadata')

        queryset = Image.objects.all()

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
            return queryset.filter(
                subject__dataset__task=task,
                subject__in=selected_subjects,
            ).exclude(id__lte=image.id).order_by('id')[0].id
        else:
            # Get current annotated image
            annotated_image = ProcessedImage.objects.get(task=task, image=image)
            if sort_by == ImageListForm.SORT_DATE_DESC:
                if task.type != Task.CLASSIFICATION:
                    queryset = queryset.filter(
                        processedimage__task=task,
                        processedimage__date__lt=annotated_image.date,
                        processedimage__image_quality__in=image_quality,
                        processedimage__user__in=users_selected,
                        subject__in=selected_subjects,
                    )
                else:
                    queryset = queryset.filter(
                        processedimage__task=task,
                        processedimage__date__lt=annotated_image.date,
                        processedimage__image_quality__in=image_quality,
                        processedimage__imagelabel__label__in=selected_labels,
                        processedimage__user__in=users_selected,
                        subject__in=selected_subjects,
                    )
                return queryset.order_by('-processedimage__date')[0].id
            elif sort_by == ImageListForm.SORT_DATE_ASC:
                if task.type != Task.CLASSIFICATION:
                    queryset = queryset.filter(
                        processedimage__task=task,
                        processedimage__date__gt=annotated_image.date,
                        processedimage__image_quality__in=image_quality,
                        processedimage__user__in=users_selected,
                        subject__in=selected_subjects,
                    )
                else:
                    queryset = queryset.filter(
                        processedimage__task=task,
                        processedimage__date__gt=annotated_image.date,
                        processedimage__image_quality__in=image_quality,
                        processedimage__imagelabel__label__in=selected_labels,
                        processedimage__user__in=users_selected,
                        subject__in=selected_subjects,
                    )
                return queryset.order_by('processedimage__date')[0].id
    except:
        return None


def setup_task_context(request, task_id, type, image_id):
    context = {}
    context['dark_style'] = 'yes'
    try:
        task = Task.objects.get(pk=task_id, type=type)
    except Task.DoesNotExist:
        raise Http404("Task does not exist")

    # TODO Get label hierarchy
    # Top labels first
    toplabels = task.label.all()
    # Find each sublabel group
    sublabels = []
    label_stack = []
    labels = [] # all labels
    for label in toplabels:
        label_stack.append(label)
        labels.append(label)

    # Process stack
    while len(label_stack) > 0:
        current_label = label_stack.pop()

        # Add all children
        children = []
        for label in Label.objects.filter(parent=current_label):
            label_stack.append(label)
            children.append(label)
            labels.append(label)

        if len(children) > 0:
            sublabel = {'id': current_label.id, 'labels': children}
            sublabels.append(sublabel)

    context['toplabels'] = toplabels
    context['sublabels'] = sublabels
    context['labels'] = labels

    if image_id is None:
        image = get_next_unprocessed_image(task)
    else:
        image = ImageSequence.objects.get(pk=image_id)

        # Only show next and previous buttons if we processing specific images
        context['next_image_id'] = get_next_image(request, task, image)
        context['previous_image_id'] = get_previous_image(request, task, image)

        # Give return URL to template if it exists
        if 'return_to_url' in request.session:
            context['return_url'] = request.session['return_to_url']

    if task.user_frame_selection_valid() and not task.user_frame_selection:
        # Check if image has key frames for this task
        if KeyFrameAnnotation.objects.filter(image_annotation__task=task, image_annotation__image=image).count() == 0:
            raise RuntimeError('This image sequence has no key frames. An admin must select key frames before annotating.')

    # Delete return URL
    if 'return_to_url' in request.session:
        del request.session['return_to_url']

    # Check if image belongs to an image sequence
    context['image_sequence'] = image
    context['frames'] = KeyFrameAnnotation.objects.filter(image_annotation__image=image, image_annotation__task=task)

    context['image'] = image
    context['task'] = task
    context['image_quality_choices'] = ImageAnnotation.IMAGE_QUALITY_CHOICES

    # Check if image has been annotated
    processed = ImageAnnotation.objects.filter(image=image, task=task)
    if processed.exists():
        context['chosen_quality'] = processed[0].image_quality
        context['comments'] = processed[0].comments
    else:
        context['chosen_quality'] = -1

    return context


def save_annotation(request):
    with transaction.atomic():
        if request.method != 'POST':
            raise Exception('ERROR: Must use POST when saving processed image.')

        # Image quality is required
        if 'quality' not in request.POST:
            raise Exception('ERROR: You must select image quality.')

        image_id = int(request.POST['image_id'])
        task_id = int(request.POST['task_id'])
        new_key_frames = json.loads(request.POST['target_frames'])
        rejected = request.POST['rejected'] == 'true'
        comments = request.POST['comments']

        # Delete old key frames if they exist, this will also delete old annotations
        key_frames = KeyFrameAnnotation.objects.filter(image_annotation__task_id=task_id, image_annotation__image_id=image_id)
        key_frames.delete()

        # Save to DB
        try:
            annotation = ImageAnnotation.objects.get(task_id=task_id, image_id=image_id)
        except ImageAnnotation.DoesNotExist:
            annotation = ImageAnnotation()
            annotation.image_id = image_id
            annotation.task_id = task_id

        annotation.rejected = rejected
        annotation.comments = comments
        annotation.user = request.user
        annotation.finished = True
        annotation.image_quality = request.POST['quality']
        annotation.save()

        annotations = []
        for frame in new_key_frames:
            keyframe = KeyFrameAnnotation()
            keyframe.frame_nr = int(frame)
            keyframe.image_annotation = annotation
            keyframe.save()
            annotations.append(keyframe)

    return annotations


