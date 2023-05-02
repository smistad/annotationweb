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
import io
import codecs
from PIL import Image
import base64

class SplineSegmentationExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)
    json_annotations = forms.BooleanField(label='Export annotations as geoJSON files for instance segmentation', initial=False,
                                          required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


def img_b64_to_arr(img_b64):
    """convert image data to image array"""

    f = io.BytesIO()
    f.write(base64.b64decode(img_b64))
    img_arr = np.array(PIL.Image.open(f))
    return img_arr

def img_arr_to_b64(img_arr):
    """convert image array to image data (base 64) according to labelme format"""

    img_pil = Image.fromarray(img_arr)
    f = io.BytesIO()
    img_pil.save(f, format='PNG')
    data = f.getvalue()
    encData = codecs.encode(data, 'base64').decode()
    encData = encData.replace('\n', '')
    return encData


def create_json(coord, image_size, filename, image_data):
    """This function creates a JSON dictionary according to labelme format"""

    data = []
    coordinates = coord

    for i in range(len(coordinates)):
        if i % 2 == 0:
            data.append(
                {
                    "label": str(coordinates[i + 1]),
                    "points": coordinates[i],
                    "group_id": 'null',
                    "shape_type": "polygon",
                    "flags": {},
                }
            )

    json_dict = {
        "version": "4.5.6",
        "flags": {},
        "shapes": data,
        "imagePath": os.path.basename(os.path.normpath(filename[:-7])) + '.png',
        "imageData": image_data,
        "imageHeight": image_size[0],
        "imageWidth": image_size[1]

    }

    return json_dict



class SplineSegmentationExporter(Exporter):
    """
    asdads
    """

    task_type = Task.SPLINE_SEGMENTATION
    name = 'Spline segmentation exporter'

    def get_form(self, data=None):
        return SplineSegmentationExporterForm(self.task, data=data)

    def export(self, form):
        delete_existing_data = form.cleaned_data['delete_existing_data']
        json_annotations = form.cleaned_data['json_annotations']
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

        self.add_subjects_to_path(path, form.cleaned_data['subjects'], json_annotations)

        return True, path

    def add_subjects_to_path(self, path, data, json_annotations):

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
                self.save_segmentation(frame, image_size, join(subject_subfolder, target_gt_name), spacing, json_annotations)

        return True, path

    def get_object_segmentation(self, image_size, frame):
        segmentation = np.zeros(image_size, dtype=np.uint8)
        tension = 0.5
        coordinates = []
        labels = Label.objects.filter(task=frame.image_annotation.task).order_by('id')
        counter = 1
        xy_new_temp =0

        for label in labels:
            objects = ControlPoint.objects.filter(label=label, image=frame).only('object').distinct()
            for object in objects:
                previous_x = None
                previous_y = None
                xy = []
                control_points = ControlPoint.objects.filter(label=label, image=frame, object=object.object).order_by('index')
                max_index = len(control_points)
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

                        xy.append(previous_x)
                        xy.append(previous_y)

                        segmentation[y, x] = counter

                    xy_new = [xy[j:j + 2] for j in range(0, len(xy), 2)]

                    if i == max_index-1 and xy_new_temp != xy_new:
                        coordinates.append(xy_new)
                        coordinates.append(a.label)
                        xy_new_temp = xy_new

            # Fill the hole
            segmentation[binary_fill_holes(segmentation == counter)] = counter

            counter += 1

        return segmentation, coordinates


    def save_segmentation(self, frame, image_size, filename, spacing, json_annotations):
        image_size = [image_size[1], image_size[0]]

        # Create compounded segmentation object
        segmentation, coords = self.get_object_segmentation(image_size, frame)

        if json_annotations:
            image_filename = frame.image_annotation.image.format.replace('#', str(frame.frame_nr))
            if image_filename.endswith('.mhd'):
                image_mhd = MetaImage(filename=image_filename)
                image_array = image_mhd.get_pixel_data()
            else:
                image_pil = PIL.Image.open(image_filename)
                image_array = np.asarray(image_pil)
            image_data = img_arr_to_b64(image_array)
            json_dict = create_json(coords, image_size, filename, image_data)
            with open(filename[:-7] + '.json', "w") as f:
                print("The json file is created")
                jason_str = json.dumps(json_dict)
                f.write(jason_str)

        else:
            segmentation_mhd = MetaImage(data=segmentation)
            segmentation_mhd.set_attribute('ImageQuality', frame.image_annotation.image_quality)
            segmentation_mhd.set_spacing(spacing)
            metadata = ImageMetadata.objects.filter(image=frame.image_annotation.image)
            for item in metadata:
                segmentation_mhd.set_attribute(item.name, item.value)
            segmentation_mhd.write(filename)

