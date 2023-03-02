from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from annotationweb.models import Task, KeyFrameAnnotation
import common.task
import json
from .models import *
from django.db import transaction


def rank_next_image(request, task_id):
    return rank_image(request, task_id, None)


def rank_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.IMAGE_QUALITY, image_id)
        context['javascript_files'] = ['image_quality/rank.js']
        context['css_files'] = ['image_quality/style.css']
        context['image_quality_task'] = ImageQualityTask.objects.get(task=task_id)
        context['categories'] = Category.objects.filter(iq_task=context['image_quality_task'])

        # Check if image is already segmented, if so get data and pass to template
        try:
            annotations = KeyFrameAnnotation.objects.filter(image_annotation__task_id=task_id, image_annotation__image_id=image_id)
            context['rankings'] = Ranking.objects.filter(annotation__in=annotations)
        except KeyFrameAnnotation.DoesNotExist:
            pass

        return render(request, 'image_quality/rank_image.html', context)
    except common.task.NoMoreImages:
        messages.info(request, 'This task is finished, no more images to rank.')
        return redirect('index')
    except RuntimeError as e:
        messages.error(request, str(e))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def save(request):
    error_messages = ''

    rankings = json.loads(request.POST['rankings'])
    print(request.POST)

    try:
        # Use atomic transaction here so if something crashes the annotations are restored..
        with transaction.atomic():
            annotations = common.task.save_annotation(request)

            # Save segmentation
            # Save control points
            for annotation in annotations:
                frame_nr = str(annotation.frame_nr)
                for key, value in rankings[frame_nr].items():
                    ranking = Ranking()
                    ranking.annotation = annotation
                    ranking.category = Category.objects.get(id=key)
                    try:
                        ranking.selection = Rank.objects.get(id=value)
                    except Rank.DoesNotExist:
                        raise Exception(f'You must select image quality for all categories. Missing for frame {frame_nr}')
                    ranking.save()

            response = {
                'success': 'true',
                'message': 'Annotation saved',
            }
    except Exception as e:
        response = {
            'success': 'false',
            'message': str(e),
        }

    return JsonResponse(response)


def show(request, task_id, image_id):
    pass
