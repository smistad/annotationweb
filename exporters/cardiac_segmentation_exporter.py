from math import sqrt, floor, ceil
from common.exporter import Exporter
from common.metaimage import MetaImage
from common.utility import create_folder, copy_image
from annotationweb.models import ProcessedImage, Dataset, Task, Label, Subject, KeyFrame, Metadata
from cardiac.models import Segmentation, ControlPoint, OBJECTS
from django import forms
import os
from os.path import join
from shutil import rmtree, copyfile
import numpy as np
from scipy.ndimage.morphology import binary_fill_holes


class CardiacSegmentationExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class CardiacSegmentationExporter(Exporter):
    """
    asdads
    """

    task_type = Task.CARDIAC_SEGMENTATION
    name = 'Default cardiac segmentation exporter'

    def get_form(self, data=None):
        return CardiacSegmentationExporterForm(self.task, data=data)

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
            subject_path = join(path, subject.name)
            create_folder(subject_path)
            images = ProcessedImage.objects.filter(task=self.task, image__subject=subject, rejected=False)
            for image in images:
                # Check if image was rejected
                if image.rejected:
                    continue
                # Get image sequence
                key_frame = KeyFrame.objects.get(image=image.image)
                image_sequence = key_frame.image_sequence

                # Get segmentation
                segmentation = Segmentation.objects.get(image=image)

                # Copy image frames
                image_id = image.image.pk
                create_folder(join(subject_path, str(image_id)))

                filename = image_sequence.format.replace('#', str(segmentation.frame_ED))
                new_filename_ED = join(subject_path, str(image_id), 'ED.mhd')
                copy_image(filename, new_filename_ED)

                filename = image_sequence.format.replace('#', str(segmentation.frame_ES))
                new_filename_ES = join(subject_path, str(image_id), 'ES.mhd')
                copy_image(filename, new_filename_ES)

                # Get control points to create segmentation
                image_mhd = MetaImage(filename=new_filename_ED)
                control_points = ControlPoint.objects.filter(segmentation=segmentation, phase=0).order_by('index')
                self.save_segmentation(image, image_mhd.get_size(), control_points, join(subject_path, str(image_id), 'ED_segmentation.mhd'))

                image_mhd = MetaImage(filename=new_filename_ES)
                control_points = ControlPoint.objects.filter(segmentation=segmentation, phase=1).order_by('index')
                self.save_segmentation(image, image_mhd.get_size(), control_points, join(subject_path, str(image_id), 'ES_segmentation.mhd'))
                

        return True, path

    def get_object_segmentation(self, image_size, control_points):
        segmentation = np.zeros(image_size, dtype=np.uint8)
        tension = 0.5

        for i in range(len(control_points)-1):
            a = control_points[max(0, i-1)]
            b = control_points[i]
            c = control_points[min(len(control_points)-1, i+1)]
            d = control_points[min(len(control_points)-1, i+2)]
            length = sqrt((b.x - c.x)*(b.x - c.x) + (b.y - c.y)*(b.y - c.y))
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

                segmentation[int(round(y)), int(round(x))] = 1

        # Draw AV plane line over endpoints
        a = np.array([control_points[0].x, control_points[0].y])
        b = np.array([control_points[len(control_points)-1].x, control_points[len(control_points)-1].y])
        length = np.linalg.norm(a - b)
        direction = (b - a) / length
        for t in np.arange(0, ceil(length), 0.1):
            position = a + t*direction
            segmentation[int(round(position[1])), int(round(position[0]))] = 1

        segmentation = binary_fill_holes(segmentation).astype(np.uint8)

        return segmentation

    def calculate_new_endpoints(self, control_points0, point):
        x = point.x
        y = point.y
        x1 = control_points0[0].x
        y1 = control_points0[0].y
        x2 = control_points0[-1].x
        y2 = control_points0[-1].y

        a = (y2 - y1)
        b = -(x2 - x1)
        c = x2*y1 - y2*x1
        distance = abs(a*x + b*y + c) / sqrt(a*a + b*b)
        # Calculate new position
        x = (b*(b*x - a*y) - a*c) / (a*a + b*b)
        y = (a*(-b*x + a*y) - b*c) / (a*a + b*b)

        point = lambda: None
        point.x = x
        point.y = y

        return point

    def save_segmentation(self, annotation, image_size, control_points, filename):
        image_size = [image_size[1], image_size[0]]
        # Get control points for all objects
        control_points0 = list(control_points.filter(object=0))
        control_points1 = list(control_points.filter(object=1))
        control_points2 = list(control_points.filter(object=2))

        # Endpoints of object 2 are the same as object 1
        control_points2.insert(0, control_points0[-1])
        control_points2.append(control_points0[0])

        # Create new endpoints for object 1
        point = self.calculate_new_endpoints(control_points0, control_points1[0])
        control_points1.insert(0, point)
        point = self.calculate_new_endpoints(control_points0, control_points1[-1])
        control_points1.append(point)

        # Create compounded segmentation object
        segmentation = np.zeros(image_size, dtype=np.uint8)
        object_segmentation = self.get_object_segmentation(image_size, control_points1)
        segmentation[object_segmentation == 1] = 2  # Draw epi before endo
        object_segmentation = self.get_object_segmentation(image_size, control_points2)
        segmentation[object_segmentation == 1] = 3
        object_segmentation = self.get_object_segmentation(image_size, control_points0)
        segmentation[object_segmentation == 1] = 1

        segmentation_mhd = MetaImage(data=segmentation)
        segmentation_mhd.set_attribute('ImageQuality', annotation.image_quality)
        segmentation_mhd.set_attribute('OriginalFilename', annotation.image.filename)
        metadata = Metadata.objects.filter(image=annotation.image)
        for item in metadata:
            segmentation_mhd.set_attribute(item.name, item.value)
        segmentation_mhd.write(filename)

