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
import json
from scipy.ndimage.morphology import binary_fill_holes
import PIL


class SplineLinePointExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class SplineLinePointExporter(Exporter):
    """
    asdads
    """

    task_type = Task.SPLINE_LINE_POINT
    name = 'Splines, lines & point segmentation exporter'

    def get_form(self, data=None):
        return SplineLinePointExporterForm(self.task, data=data)

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
                target_gt_name = os.path.splitext(target_name)[0]+"_gt.mhd"

                filename = image_sequence.format.replace('#', str(frame.frame_nr))
                new_filename = join(subject_subfolder, target_name)
                copy_image(filename, new_filename)

                # Get control points to create segmentation
                if new_filename.endswith('.mhd'):
                    image_mhd = MetaImage(filename=new_filename)
                    image_size = image_mhd.get_size()
                    spacing = image_mhd.get_spacing()
                else:
                    image_pil = PIL.Image.open(new_filename)
                    image_size = image_pil.size
                    spacing = [1, 1]
                self.save_segmentation(frame, image_size, join(subject_subfolder, target_gt_name), spacing)

        return True, path

    def get_object_segmentation(self, image_size, frame):
        segmentation = np.zeros(image_size, dtype=np.uint8)
        tension = 0.5

        labels = Label.objects.filter(task=frame.image_annotation.task).order_by('id')
        counter = 1
        for label in labels:
            objects = ControlPoint.objects.filter(label=label, image=frame).only('object').distinct()
            for object in objects:
                previous_x = None
                previous_y = None
                control_points = ControlPoint.objects.filter(label=label, image=frame, object=object.object).order_by('index')
                max_index = len(control_points)

                if max_index == 1:
                    x = int(round(control_points[0].x))
                    y = int(round(control_points[0].y))
                    segmentation[y, x] = counter
                else:
                    for i in range(max_index):
                        if i == 0:
                            first = max_index-1
                        else:
                            first = i-1
                        a = control_points[first]
                        b = control_points[i]
                        c = control_points[(i+1) % max_index]
                        d = control_points[(i+2) % max_index]
                        length = sqrt((b.x - c.x)*(b.x - c.x) + (b.y - c.y)*(b.y - c.y))
                        # Not a very elegant solution ... could try to estimate the spline length instead
                        # or draw straight lines between consecutive points instead
                        step_size = min(0.01, 1.0 / (length*2))
                        for t in np.arange(0, 1, step_size):
                            x = (2 * t * t * t - 3 * t * t + 1) * b.x + \
                                (1 - tension) * (t * t * t - 2.0 * t * t + t) * (c.x - a.x) + \
                                (-2 * t * t * t + 3 * t * t) * c.x + \
                                (1 - tension) * (t * t * t - t * t) * (d.x - b.x)
                            y = (2 * t * t * t - 3 * t * t + 1) * b.y + \
                                (1 - tension) * (t * t * t - 2.0 * t * t + t) * (c.y - a.y) + \
                                (-2 * t * t * t + 3 * t * t) * c.y + \
                                (1 - tension) * (t * t * t - t * t) * (d.y - b.y)

                            # Round and snap to borders
                            x = int(round(x))
                            x = min(image_size[1]-1, max(0, x))
                            y = int(round(y))
                            y = min(image_size[0]-1, max(0, y))

                            if previous_x is not None and (abs(previous_x - x) > 1 or abs(previous_y - y) > 1):
                                # Draw a straight line between the points
                                end_pos = np.array([x,y])
                                start_pos = np.array([previous_x,previous_y])
                                direction = end_pos - start_pos
                                segment_length = np.linalg.norm(end_pos - start_pos)
                                direction = direction / segment_length # Normalize
                                for i in np.arange(0.0, np.ceil(segment_length), 0.5):
                                    current = start_pos + direction * (float(i)/np.ceil(segment_length))
                                    current = np.round(current).astype(np.int32)
                                    current[0] = min(image_size[1]-1, max(0, current[0]))
                                    current[1] = min(image_size[0]-1, max(0, current[1]))
                                    segmentation[current[1], current[0]] = counter

                            previous_x = x
                            previous_y = y

                            segmentation[y, x] = counter

            # Fill the hole
            segmentation[binary_fill_holes(segmentation == counter)] = counter

            counter += 1

        return segmentation

    def save_segmentation(self, frame, image_size, filename, spacing):
        image_size = [image_size[1], image_size[0]]

        # Create compounded segmentation object
        segmentation = self.get_object_segmentation(image_size, frame)

        segmentation_mhd = MetaImage(data=segmentation)
        segmentation_mhd.set_attribute('ImageQuality', frame.image_annotation.image_quality)
        segmentation_mhd.set_attribute('FrameType', frame.frame_metadata)
        segmentation_mhd.set_spacing(spacing)
        metadata = ImageMetadata.objects.filter(image=frame.image_annotation.image)
        for item in metadata:
            segmentation_mhd.set_attribute(item.name, item.value)
        segmentation_mhd.write(filename)

