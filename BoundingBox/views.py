from django.shortcuts import render, redirect
from .models import *
from .forms import *
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse


def new_task(request):
    if request.method == 'POST':
        form = BoundingBoxTaskForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'New task was created.')
            return redirect('annotation:index')
    else:
        form = BoundingBoxTaskForm()

    return render(request, 'boundingbox/new_task.html', {'form': form})


def delete_task(request, task_id):
    pass


def process_image(request, task_id):
    pass


def save_boxes(request):
    pass


def export(request):
    pass


