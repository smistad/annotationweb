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

class CardiacPLAXPointExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class CardiacPLAXPointExporter(Exporter):
    task_type = Task.CARDIAC_PLAX_SEGMENTATION
    name = 'Cardiac PLAX point exporter'

    def get_form(self, data=None):
        return CardiacPLAXPointExporterForm(self.task, data=data)

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
                target_gt_name = os.path.splitext(target_name)[0]+"_points.txt"

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
        control_points0 = list(ControlPoint.objects.filter(image=frame, object=0).order_by('index'))
        control_points1 = list(ControlPoint.objects.filter(image=frame, object=1).order_by('index'))
        control_points2 = list(ControlPoint.objects.filter(image=frame, object=2).order_by('index'))
        control_points3 = list(ControlPoint.objects.filter(image=frame, object=3).order_by('index'))
        control_points4 = list(ControlPoint.objects.filter(image=frame, object=4).order_by('index'))
        control_points5 = list(ControlPoint.objects.filter(image=frame, object=5).order_by('index'))

        if x_scaling != 1:
            for point in control_points0:
                point.x *= x_scaling
            for point in control_points1:
                point.x *= x_scaling
            for point in control_points2:
                point.x *= x_scaling
            for point in control_points3:
                point.x *= x_scaling
            for point in control_points4:
                point.x *= x_scaling
            for point in control_points5:
                point.x *= x_scaling

        # Endpoints of object 2 (LA) are the same as object 0 (endo/LV)
        if len(control_points0) > 0 and len(control_points2) > 0:
            control_points2.insert(0, control_points0[-1])
            control_points2.append(control_points0[0])
        # Aorta (3) endpoints
        if len(control_points3) > 0 and len(control_points0) > 0:
            control_points3.insert(0, control_points0[-2])
            control_points3.append(control_points0[-1])
        # (LVOT) (5) endpoints
        if len(control_points0) > 0 and len(control_points5) > 0:
            control_points5.insert(0, control_points0[-1])
            control_points5.append(control_points0[-2])
        # (myocard/epi) (1) endpoints
        if len(control_points0) > 0 and len(control_points1) > 0:
            control_points1.insert(0, control_points0[0])
            control_points1.append(control_points0[-2])

        with open(filename, 'w') as f:
            f.write(f'FrameType {frame.frame_metadata}\n')
            f.write(f'ImageQuality {frame.image_annotation.image_quality}\n')
            f.write(f'# Label: {control_points0[3].label.name}\n')
            for point in control_points0:
                f.write(f'{point.x} {point.y}\n')
            f.write(f'# Label: {control_points1[3].label.name}\n')
            for point in control_points1:
                f.write(f'{point.x} {point.y}\n')
            f.write(f'# Label: {control_points2[3].label.name}\n')
            for point in control_points2:
                f.write(f'{point.x} {point.y}\n')
            f.write(f'# Label: {control_points3[3].label.name}\n')
            for point in control_points3:
                f.write(f'{point.x} {point.y}\n')
            f.write(f'# Label: {control_points4[3].label.name}\n')
            for point in control_points4:
                f.write(f'{point.x} {point.y}\n')
            f.write(f'# Label: {control_points5[3].label.name}\n')
            for point in control_points5:
                f.write(f'{point.x} {point.y}\n')




