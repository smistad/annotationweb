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

class CardiacPLAXSegmentationExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class CardiacPLAXSegmentationExporter(Exporter):
    """
    asdads
    """

    task_type = Task.CARDIAC_ALAX_SEGMENTATION
    name = 'Default cardiac ALAX segmentation exporter'

    def get_form(self, data=None):
        return CardiacPLAXSegmentationExporterForm(self.task, data=data)

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

    def get_object_segmentation(self, image_size, control_points, x_scaling, straight_lines=[]):
        segmentation = np.zeros(image_size, dtype=np.uint8)
        tension = 0.5

        for i in range(len(straight_lines)):
            if straight_lines[i][0] < 0:
                straight_lines[i][0] = len(control_points) + straight_lines[i][0]
            if straight_lines[i][1] < 0:
                straight_lines[i][1] = len(control_points) + straight_lines[i][1]

        if len(straight_lines) > 0:
            max_index = len(control_points)-1
        else:
            max_index = len(control_points)
        for i in range(max_index):
            # Draw between i and i+1
            if [i, i+1] in straight_lines: continue # Skip, this should be drawn as straight line

            if len(straight_lines) > 0:
                a = control_points[max(0, i-1)]
                b = control_points[i]
                c = control_points[min(max_index, i+1)]
                d = control_points[min(max_index, i+2)]
                # Check if d point is any straight line pairs
                asd = min(max_index, i+2)
                found = False
                for line in straight_lines:
                    if line[0] == asd or line[1] == asd:
                        found = True
                if found:
                    d = control_points[min(max_index, i + 1)]
            else:
                if i == 0:
                    first = max_index-1
                else:
                    first = i-1
                a = control_points[first]
                b = control_points[i]
                c = control_points[(i+1) % max_index]
                d = control_points[(i+2) % max_index]


            print('Control points', image_size, a.x, a.y, b.x, b.y, c.x, c.y, d.x, d.y)
            length = sqrt((b.x - c.x)*(b.x - c.x) + (b.y - c.y)*(b.y - c.y))
            step_size = min(0.01, 1.0 / (length*4))
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

        # Draw straight lines
        for start, end in straight_lines:
            a = np.array([control_points[start].x, control_points[start].y])
            b = np.array([control_points[end].x, control_points[end].y])
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

    def save_segmentation(self, frame, image_size, filename, spacing, x_scaling, image):
        print('X scaling is', x_scaling)
        image_size = [image_size[1], image_size[0]]
        # Get control points for all objects
        control_points0 = list(ControlPoint.objects.filter(image=frame, object=0).order_by('index'))
        control_points1 = list(ControlPoint.objects.filter(image=frame, object=1).order_by('index'))
        control_points2 = list(ControlPoint.objects.filter(image=frame, object=2).order_by('index'))
        control_points3 = list(ControlPoint.objects.filter(image=frame, object=3).order_by('index'))

        if x_scaling != 1:
            for point in control_points0:
                point.x *= x_scaling
            for point in control_points1:
                point.x *= x_scaling
            for point in control_points2:
                point.x *= x_scaling
            for point in control_points3:
                point.x *= x_scaling

        # Endpoints of object 2 (LA) are the same as object 0 (endo/LV)
        if len(control_points0) > 0 and len(control_points2) > 0:
            control_points2.insert(0, control_points0[-1])
            control_points2.append(control_points0[0])
        # Aorta (3) endpoints
        if len(control_points3) > 0 and len(control_points0) > 0:
            control_points3.insert(0, control_points0[-2])
            control_points3.append(control_points0[-1])
        # (myocard/epi) (1) endpoints
        if len(control_points0) > 0 and len(control_points1) > 0:
            control_points1.insert(0, control_points0[0])
            control_points1.append(control_points0[-2])

        # Create compounded segmentation object
        #image_size[1] = int(round(image_size[1]/x_scaling))
        #spacing[1] = spacing[0]
        segmentation = np.zeros(image_size, dtype=np.uint8)
        if len(control_points1) > 0:
            object_segmentation = self.get_object_segmentation(image_size, control_points1, x_scaling, straight_lines=[[0, -1], [-2, -1], [0, 1]])
            segmentation[object_segmentation == 1] = 2  # Draw epi before endo
        if len(control_points2) > 0:
            object_segmentation = self.get_object_segmentation(image_size, control_points2, x_scaling, straight_lines=[[0, -1]])
            segmentation[object_segmentation == 1] = 3
        if len(control_points0) > 0:
            object_segmentation = self.get_object_segmentation(image_size, control_points0, x_scaling, straight_lines=[[0, -1], [-2, -1]])
            segmentation[object_segmentation == 1] = 1
        if len(control_points3) > 0:
            object_segmentation = self.get_object_segmentation(image_size, control_points3, x_scaling, straight_lines=[[0, -1]])
            segmentation[object_segmentation == 1] = 4

        segmentation_mhd = MetaImage(data=segmentation)
        segmentation_mhd.set_attribute('ImageQuality', frame.image_annotation.image_quality)
        segmentation_mhd.set_attribute('FrameType', frame.frame_metadata)
        segmentation_mhd.set_spacing(spacing)
        metadata = ImageMetadata.objects.filter(image=frame.image_annotation.image)
        for item in metadata:
            segmentation_mhd.set_attribute(item.name, item.value)
        segmentation_mhd.write(filename)

