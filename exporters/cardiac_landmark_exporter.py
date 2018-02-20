from common.exporter import Exporter
from common.metaimage import MetaImage
from common.utility import create_folder
from annotationweb.models import ProcessedImage, Task, Subject
from cardiac_landmark.models import CardiacLandmark, ControlPoint
from django import forms
import os
from os.path import join
from shutil import rmtree
import numpy as np
import glob
import PIL
import re
from ast import literal_eval
import h5py


def natural_keys(text):
    def atoi(text):
        return int(text) if text.isdigit() else text

    return [atoi(c) for c in re.split('(\d+)', text)]


class CardiacLandmarkExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class CardiacSegmentationExporter(Exporter):
    """
    """

    task_type = Task.CARDIAC_LANDMARK
    name = 'Default cardiac landmark exporter'

    def get_form(self, data=None):
        return CardiacLandmarkExporterForm(self.task, data=data)

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
            processed_sequences = ProcessedImage.objects.filter(task=self.task, image__subject=subject)

            import matplotlib.pyplot as plt

            for seq in processed_sequences:
                # Get segmentation
                landmark = CardiacLandmark.objects.get(image=seq)
                ed_frame = landmark.frame_ED
                es_frame = landmark.frame_ES

                control_point_ed = ControlPoint.objects.filter(landmark=landmark, phase=0).order_by('index')
                landmarks_pts_ed = np.array([[pt.x, pt.y] for pt in control_point_ed])

                control_point_es = ControlPoint.objects.filter(landmark=landmark, phase=1).order_by('index')
                landmarks_pts_es = np.array([[pt.x, pt.y] for pt in control_point_es])

                data_folder = os.path.dirname(seq.image.filename)
                seq_tag = os.path.basename(data_folder)

                f = h5py.File(os.path.join(subject_path, seq_tag)+'.hd5', 'w')
                if "MR" in data_folder:
                    images = self.load_images(data_folder)
                    images_full = self.load_images(data_folder.replace('MR', 'MR_Full'))
                    spacing, view, crop_corner, crop_size = self.load_mr_meta(data_folder)
                    f.create_dataset("data_full", data=images_full[...,None], compression="gzip", compression_opts=4, dtype='float32')
                    f.create_dataset("view", data=np.string_(view))
                    f.create_dataset("crop_corner", data=crop_corner, compression="gzip", compression_opts=4, dtype='uint16')
                    f.create_dataset("crop_size", data=crop_size, compression="gzip", compression_opts=4, dtype='uint16')
                elif "US" in data_folder:
                    images = self.load_images(data_folder)
                    spacing, view = self.load_us_meta(data_folder)
                    f.create_dataset("view", data=np.string_(view))

                f.create_dataset("data", data=images[...,None], compression="gzip", compression_opts=4, dtype='float32')
                f.create_dataset("data_ed", data=images[ed_frame], compression="gzip", compression_opts=4, dtype='float32')
                f.create_dataset("data_es", data=images[es_frame], compression="gzip", compression_opts=4, dtype='float32')
                f.create_dataset("label_ed", data=landmarks_pts_ed, compression="gzip", compression_opts=4, dtype='float32')
                f.create_dataset("label_es", data=landmarks_pts_es, compression="gzip", compression_opts=4, dtype='float32')
                f.create_dataset("ed_frame", data=ed_frame, dtype='uint16')
                f.create_dataset("es_frame", data=es_frame, dtype='uint16')
                f.create_dataset("spacing", data=spacing, compression="gzip", compression_opts=4, dtype='float32')
                f.close()

        return True, path

    def load_images(self, folder):
        # loads all .png's into list
        files = [os.path.join(folder, f) for f in glob.glob(os.path.join(folder, '*.png'))]
        files.sort(key=natural_keys)
        images = np.array([np.array(PIL.Image.open(f), dtype=np.float32).T/255 for f in files])

        return images

    def load_mr_meta(self, folder):

        metadata = open(os.path.join(folder, "Metafile.txt"), 'r')
        _, spacing, view, _, corners, _, _ = metadata.readlines()

        translator = {'4-CHAMBER': '4ch', '3-CHAMBER': 'lax', '2-CHAMBER': '2ch'}
        view = translator[view.replace('\n','')]
        spacing = list(literal_eval(spacing.split(': ')[1]))

        corners = list(map(int, corners.split(',')))
        crop_size = [corners[2]-corners[0], corners[3]-corners[1]]
        crop_corner = corners[:2]

        return spacing, view, crop_corner, crop_size

    def load_us_meta(self, folder):
        metadata = open(os.path.join(folder, "metadata.txt"), 'r')
        _, spacing, view = metadata.readlines()
        spacing = list(literal_eval(spacing.split(': ')[1]))
        translator = {'a4c': 'a4ch', 'alax': 'alax', 'a2c': 'a2ch', 'a5c': 'a5ch'}
        view = translator[view.split(': ')[1].replace('\n','')]

        return spacing, view
