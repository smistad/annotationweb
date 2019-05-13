import random

from django.http import Http404

from annotationweb.models import Task, Annotation, Subject, Label, ImageSequence, KeyFrame
from annotationweb.forms import ImageListForm
from django.db.models.aggregates import Count
from common.search_filters import SearchFilter


def get_next_unprocessed_image(task):
    """
    Get the next unprocessed image related to a task (in random order)
    :param task:
    :return image:
    """
    count = ImageSequence.objects.filter(subject__dataset__task=task).exclude(keyframe__annotation__task=task).aggregate(count=Count('id'))['count']
    if task.shuffle_videos:
        index = random.randint(0, count - 1)
    else:
        index = 0

    return ImageSequence.objects.filter(subject__dataset__task=task).exclude(keyframe__annotation__task=task).order_by("subject", "format")[index]


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

    # Delete return URL
    if 'return_to_url' in request.session:
        del request.session['return_to_url']

    # Check if image belongs to an image sequence
    context['image_sequence'] = image
    context['frames'] = KeyFrame.objects.filter(image_sequence=image)

    context['image'] = image
    context['task'] = task
    context['number_of_labeled_images'] = Annotation.objects.filter(task=task_id).count()
    context['total_number_of_images'] = ImageSequence.objects.filter(subject__dataset__task=task_id).count()
    context['percentage_finished'] = round(context['number_of_labeled_images']*100 / context['total_number_of_images'], 1)
    context['image_quality_choices'] = Annotation.IMAGE_QUALITY_CHOICES

    # Check if image has been annotated
    processed = Annotation.objects.filter(keyframe__image_sequence=image, task=task)
    if processed.exists():
        context['chosen_quality'] = processed[0].image_quality
        context['comments'] = processed[0].comments
    else:
        context['chosen_quality'] = -1

    return context


def save_annotation(request):
    if request.method != 'POST':
        raise Exception('ERROR: Must use POST when saving processed image.')

    # Image quality is required
    if 'quality' not in request.POST:
        raise Exception('ERROR: You must select image quality.')

    image_id = int(request.POST['image_id'])
    task_id = int(request.POST['task_id'])
    rejected = request.POST['rejected'] == 'true'
    comments = request.POST['comments']

    # Delete old annotations if it exists
    annotations = ProcessedImage.objects.filter(image_id=image_id, task_id=task_id)
    annotations.delete()

    # Save to DB
    annotation = ProcessedImage()
    annotation.rejected = rejected
    annotation.comments = comments
    annotation.image_id = image_id
    annotation.task_id = task_id
    annotation.user = request.user
    annotation.image_quality = request.POST['quality']
    annotation.save()

    return annotation


