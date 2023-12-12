from common.exporter import Exporter
from common.utility import copy_image, create_folder
from annotationweb.models import *
from classification.models import ImageLabel
from django import forms
import os
from os.path import join
from shutil import rmtree, copyfile
from common.metaimage import MetaImage
import PIL
import numpy as np
import h5py


class ClassificationExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)
    output_image_format = forms.ChoiceField(choices=(
        ('png', 'PNG'),
        ('mhd', 'MetaImage')
    ), initial='png', label='Output image format')

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['dataset'] = forms.ModelMultipleChoiceField(queryset=Dataset.objects.filter(task=task))


class ClassificationExporter(Exporter):
    """
    This exporter will create a folder at the given path and create 2 files:
    labels.txt      - list of labels
    file_list.txt   - list of files and labels
    A folder is created for each dataset with the actual images
    """

    task_type = Task.CLASSIFICATION
    name = 'Default image classification exporter'

    def get_form(self, data=None):
        return ClassificationExporterForm(self.task, data=data)

    def export(self, form):
        datasets = form.cleaned_data['dataset']
        delete_existing_data = form.cleaned_data['delete_existing_data']
        # Create dir, delete old if it exists
        path = form.cleaned_data['path']
        if delete_existing_data:
            # Delete path
            try:
                os.stat(path)
                rmtree(path)
            except:
                # Folder does not exist
                pass

            # Create folder again
            try:
                os.mkdir(path)
            except:
                return False, 'Failed to create directory at ' + path
        else:
            # Check that folder exist
            try:
                os.stat(path)
            except:
                return False, 'Path does not exist: ' + path

        # Create label file
        label_file = open(os.path.join(path, 'labels.txt'), 'w')
        labels = Label.objects.filter(task=self.task)
        labelDict = {}
        counter = 0
        for label in labels:
            label_file.write(str(counter) + ' ' + label.name + '\n')
            labelDict[label.name] = counter
            counter += 1
        label_file.close()

        # Create file_list.txt file
        file_list = open(os.path.join(path, 'file_list.txt'), 'w')
        labeled_images = KeyFrameAnnotation.objects.filter(image_annotation__task=self.task,
                                                           image_annotation__task__dataset__in=datasets,
                                                           image_annotation__rejected=False)
        for labeled_image in labeled_images:
            image_sequence = ImageSequence.objects.get(id=labeled_image.image_annotation.image_id)
            filepath = image_sequence.format.replace('#', str(image_sequence.id))
            dataset_path = os.path.join(path, labeled_image.image_annotation.task.dataset.get().name)
            try:
                os.mkdir(dataset_path) # Make dataset path if doesn't exist
            except:
                pass

            # Get image label
            label = ImageLabel.objects.get(image=labeled_image)

            image_id = labeled_image.image_annotation.image_id
            new_extension = form.cleaned_data['output_image_format']
            new_filename = os.path.join(dataset_path, str(image_id) + '.' + new_extension)
            copy_image(filepath, new_filename, label={'id': str(labelDict[label.label.name]), 'name': label.label.name})

            file_list.write(new_filename + ' ' + str(labelDict[label.label.name]) + '\n')

        file_list.close()

        return True, path


