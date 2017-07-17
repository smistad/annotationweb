from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
import random
from io import StringIO, BytesIO
import base64
from annotationweb.settings import BASE_DIR
from common.metaimage import *
import numpy as np
from annotationweb.models import Task, Image, ProcessedImage, Label
from common.utility import get_image_as_http_response
import common.task


def segment_next_image(request, task_id):
    return segment_image(request, task_id, None)


def segment_image(request, task_id, image_id):
    try:
        context = common.task.setup_task_context(request, task_id, Task.CARDIAC_SEGMENTATION, image_id)
        context['javascript_files'] = ['cardiac/segmentation.js']

        return render(request, 'cardiac/segment_image.html', context)
    except IndexError:
        messages.info(request, 'This task is finished, no more images to segment.')
        return redirect('index')


def save_segmentation(request):
    pass


def show_segmentation(request, task_id, image_id):
    pass
