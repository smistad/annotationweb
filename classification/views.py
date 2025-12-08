from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.http import Http404
import common.task
from .models import *
from annotationweb.models import Task, ImageAnnotation
from django.db import transaction


def label_next_image(request, task_id):
    return label_image(request, task_id, None)


def label_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.CLASSIFICATION, image_id)
        context['javascript_files'] = ['classification/classification.js']

        # Load labels
        #context['labels'] = Label.objects.filter(task=task_id)

        # Get label, if image has been already labeled
        try:
            processed = ImageLabel.objects.get(image__image_annotation__image_id=image_id, image__image_annotation__task_id=task_id)
            context['chosen_label'] = processed.label.id
        except:
            print('Not found..')
            pass

        return render(request, 'classification/label_image.html', context)
    except common.task.NoMoreImages:
        messages.info(request, 'This task is finished, no more images to annotate.')
        return redirect('index')
    except RuntimeError as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(request.headers.get('referer'))


def save_labels(request):
    try:
        rejected = request.POST['rejected'] == 'true'
        if rejected:
            annotations = common.task.save_annotation(request)
        else:
            with transaction.atomic():
                try:
                    label_id = int(request.POST['label_id'])
                    label = Label.objects.get(pk=label_id)
                except:
                    raise Exception('You must select a classification label.')

                annotations = common.task.save_annotation(request)
                for annotation in annotations:
                    labeled_image = ImageLabel()
                    labeled_image.image = annotation
                    labeled_image.label = label
                    labeled_image.task = annotation.image_annotation.task
                    labeled_image.save()

            response = {
                'success': 'true',
                'message': 'Completed'
            }
        messages.success(request, 'Classification saved')
    except Exception as e:
        response = {
            'success': 'false',
            'message': str(e)
        }

    return JsonResponse(response)

