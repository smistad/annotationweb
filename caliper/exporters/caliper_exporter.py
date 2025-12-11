from math import sqrt, floor, ceil
from common.exporter import Exporter
from common.metaimage import MetaImage
from common.utility import create_folder, copy_image
from annotationweb.models import ImageAnnotation, Dataset, Task, Label, Subject, KeyFrameAnnotation, ImageMetadata
from spline_segmentation.models import ControlPoint
from django import forms
import os
from os.path import join
from shutil import rmtree, copyfile
import numpy as np
from scipy.ndimage.morphology import binary_fill_holes
import PIL
import json

class CaliperExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class CaliperExporter(Exporter):
    name = 'Caliper json exporter'

    def get_form(self, data=None):
        return CaliperExporterForm(self.task, data=data)

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
                target_gt_name = os.path.splitext(target_name)[0]+"_calipers.json"

                filename = image_sequence.format.replace('#', str(frame.frame_nr))
                new_filename = join(subject_subfolder, target_name)
                copy_image(filename, new_filename)

                # Get control points to create segmentation
                x_scaling = 1
                if new_filename.endswith('.mhd'):
                    image_mhd = MetaImage(filename=new_filename)
                    image_size = image_mhd.get_size()
                    spacing = image_mhd.get_spacing()

                    if spacing[0] != spacing[1]:
                        # In this case we have to compensate for a change in with
                        real_aspect = image_size[0] * spacing[0] / (image_size[1] * spacing[1])
                        current_aspect = float(image_size[0]) / image_size[1]
                        new_width = int(image_size[0] * (real_aspect / current_aspect))
                        new_height = image_size[1]
                        x_scaling = float(image_size[0]) / new_width
                        print(image_size[0], new_width, image_size[1], new_height)
                    image = np.asarray(image_mhd.get_pixel_data())
                else:
                    image_pil = PIL.Image.open(new_filename)
                    image_size = image_pil.size
                    spacing = [1, 1]
                    image = np.asarray(image_pil)
                self.save_segmentation(frame, image_size, join(subject_subfolder, target_gt_name), spacing, x_scaling, image)

        return True, path

    def save_segmentation(self, frame, image_size, filename, spacing, x_scaling, image):
        print('X scaling is', x_scaling)
        image_size = [image_size[1], image_size[0]]
        # Get control points for all objects
        control_points = list(ControlPoint.objects.filter(image=frame).order_by('object', 'index'))

        objects = []
        calipers = []
        object = {
            'object': control_points[0].object,
            'label': control_points[0].label.name,
        }
        for i in range(len(control_points)-1):
            point1 = control_points[i]
            print(point1.object, point1.index)
            point2 = control_points[i+1]
            if point1.object != point2.object: # endpoint
                object['calipers'] = calipers
                objects.append(object)
                calipers = []
                object = {
                    'object': point2.object,
                    'label': point2.label.name,
                }
                continue
            # Get points in true image coordinate system
            scaledPointX1 = point1.x*x_scaling
            scaledPointX2 = point2.x*x_scaling
            # Get length in mm
            length = sqrt((point1.x-point2.x)*(point1.x-point2.x) + (point1.y-point2.y)*(point1.y-point2.y))*spacing[1]
            caliper = {
                'x1': int(round(scaledPointX1)),
                'y1': int(round(point1.y)),
                'x2': int(round(scaledPointX2)),
                'y2': int(round(point2.y)),
                'length': length,
                'index': point1.index,
            }
            calipers.append(caliper)

        # Add final object
        object['calipers'] = calipers
        objects.append(object)

        json_dict = {
            'annotator': frame.image_annotation.user.username,
            'date': frame.image_annotation.date,
            'image_quality': frame.image_annotation.image_quality,
            'objects': objects,
        }
        with open(filename, 'w') as f:
            json.dump(json_dict, f, indent=4, default=str)
