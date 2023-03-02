from math import sqrt, floor, ceil
from common.exporter import Exporter
from common.metaimage import MetaImage
from common.utility import create_folder, copy_image
from annotationweb.models import ImageAnnotation, Dataset, Task, Label, Subject, KeyFrameAnnotation, ImageMetadata
from image_quality.models import ImageQualityTask, Category, Ranking
from spline_segmentation.models import ControlPoint
from django import forms
import os
from os.path import join
from shutil import rmtree, copyfile
import numpy as np
from scipy.ndimage.morphology import binary_fill_holes
import PIL

class ImageQualityExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class ImageQualityExporter(Exporter):
    task_type = Task.IMAGE_QUALITY
    name = 'Default Image Quality Exporter'

    def get_form(self, data=None):
        return ImageQualityExporterForm(self.task, data=data)

    def export(self, form):
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

        # Create folder if it doesn't exist
        create_folder(path)

        self.add_subjects_to_path(path, form.cleaned_data['subjects'])

        return True, path

    def add_subjects_to_path(self, path, data):

        # For each subject
        for subject in data:
            subject_path = join(path, subject.dataset.name, subject.name)
            frames = KeyFrameAnnotation.objects.filter(image_annotation__task=self.task, image_annotation__image__subject=subject)
            for frame in frames:
                # Check if image was rejected
                if frame.image_annotation.rejected:
                    continue
                # Get image sequence
                image_sequence = frame.image_annotation.image

                # Copy image frames
                sequence_id = os.path.basename(os.path.dirname(image_sequence.format))
                subject_subfolder = join(subject_path, str(sequence_id))
                create_folder(subject_subfolder)

                target_name = os.path.basename(image_sequence.format).replace('#',str(frame.frame_nr))
                target_gt_name = os.path.splitext(target_name)[0]+"_image_quality.txt"

                filename = image_sequence.format.replace('#', str(frame.frame_nr))
                new_filename = join(subject_subfolder, target_name)
                copy_image(filename, new_filename)

                self.save_segmentation(frame, join(subject_subfolder, target_gt_name))

        return True, path

    def save_segmentation(self, frame, filename):
        with open(filename, 'w') as f:
            rankings = Ranking.objects.filter(annotation=frame)
            for ranking in rankings:
                f.write(f'{ranking.category.name} = {ranking.selection.name}\n')



