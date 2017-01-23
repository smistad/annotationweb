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
from django.utils.safestring import mark_safe
from common.label import get_all_labels


class CardiacExaminationsExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects_training'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))
        self.fields['subjects_validation'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class CardiacExaminationsExporter(Exporter):
    """
    This exporter will create a folder at the given path with two subfolders (training and validation)
    In each subfolder 2 files are created:
    labels.txt      - list of labels
    file_list.txt   - list of files and labels
    A folder is created for each dataset with the actual images
    """

    task_type = Task.CLASSIFICATION
    name = 'Cardiac examinations classification exporter'

    def get_form(self, data=None):
        return CardiacExaminationsExporterForm(self.task, data=data)

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
        try:
            os.stat(path)
        except:
            return False, 'Failed to create directory at ' + path


        # Create training folder
        training_path = join(path, 'training')
        create_folder(training_path)
        validation_path = join(path, 'validation')
        create_folder(validation_path)

        self.add_subjects_to_path(training_path, form.cleaned_data['subjects_training'])
        self.add_subjects_to_path(validation_path, form.cleaned_data['subjects_validation'])

        return True, path

    def add_subjects_to_path(self, path, data):
        # Create label file
        label_file = open(join(path, 'labels.txt'), 'w')
        labels = Label.objects.filter(task=self.task)
        label_dict = {}
        counter = 0
        for label in labels:
            label_file.write(label.name + '\n')
            label_dict[label.name] = counter
            counter += 1
        label_file.close()

        # Create file_list.txt file and copy images
        file_list = open(os.path.join(path, 'file_list.txt'), 'w')
        labeled_images = ProcessedImage.objects.filter(task=self.task, image__subject__in=data)
        for labeled_image in labeled_images:
            label = ImageLabel.objects.get(image=labeled_image)
            name = labeled_image.image.filename
            dataset_path = join(path, label.label.name)
            create_folder(dataset_path)

            image_id = labeled_image.image.id
            new_extension = 'png'
            new_filename = os.path.join(dataset_path, str(image_id) + '.' + new_extension)
            copy_image(name, new_filename)

            file_list.write(new_filename + ' ' + str(label_dict[label.label.name]) + '\n')

        file_list.close()


def to_categorical(y, nb_classes=None):
    y = np.array(y, dtype='uint8').ravel()
    if not nb_classes:
        nb_classes = np.max(y) + 1
    n = y.shape[0]
    categorical = np.zeros((n, nb_classes))
    categorical[np.arange(n), y] = 1
    return categorical


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    def render(self):
        return mark_safe(u'\n'.join([u'%s\n' % w for w in self]))


class CardiacHDFExaminationsExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)
    image_dim_ordering = forms.ChoiceField(label='Image dimension ordering',
                                           choices=(('tf', 'Tensorflow'), ('theano', 'Theano/Caffe')),
                                           required=False,
                                           widget=forms.RadioSelect(renderer=HorizontalRadioRenderer),
                                           initial='tf'
                                           )
    sequence_wise = forms.BooleanField(label='Export by sequence', initial=False, required=False)
    categorical = forms.BooleanField(label='Categorical labels', initial=False, required=False)
    width = forms.IntegerField(max_value=512, label='Width', initial=128) # TODO: Fix layout...
    height = forms.IntegerField(max_value=512, label='Height', initial=128)

    def __init__(self, task, data=None):
        super().__init__(data)
        labels = get_all_labels(task)
        self.fields['labels'] = forms.MultipleChoiceField(
            choices=((label['id'], label['name']) for label in labels),
            initial=[label['id'] for label in labels],
            help_text='Images assigned to sublabels which are not selected will be added '
                       'to first selected parent label. If no parent labels are '
                       'selected, the images will be excluded.'
        )


class CardiacHDFExaminationsExporter(Exporter):
    """
    This exporter will create a folder with 1 hdf5 file for each subject.
    A labels.txt file is also created.
    """

    task_type = Task.CLASSIFICATION
    name = 'Cardiac examinations classification exporter (HDF5)'

    def get_form(self, data=None):
        return CardiacHDFExaminationsExporterForm(self.task, data=data)

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
        try:
            os.stat(path)
        except:
            return False, 'Failed to create directory at ' + path

        self.add_subjects_to_path(path, form)

        return True, path

    def add_subjects_to_path(self, path, form):
        # Create label file
        label_file = open(join(path, 'labels.txt'), 'w')
        labels = form.cleaned_data['labels']
        label_dict = {}
        counter = 0 
        for label in labels:
            label_file.write(label.name + '\n')
            label_dict[label.name] = counter
            counter += 1
        label_file.close()

        # For each subject
        subjects = Subject.objects.filter(dataset__task=self.task)
        for subject in subjects:
            # Get labeled images
            labeled_images = ProcessedImage.objects.filter(task=self.task, image__subject=subject)
            if labeled_images.count() == 0:
                continue
            sequence_frames = []
            labels = []
            width = form.cleaned_data['width']
            height = form.cleaned_data['height']
            frames = 10
            for labeled_image in labeled_images:
                label = ImageLabel.objects.get(image=labeled_image)

                if label.label.name in label_dict.keys():
                    # Get sequence
                    key_frame = KeyFrame.objects.get(image=labeled_image.image)
                    image_sequence = key_frame.image_sequence
                    nr_of_frames = image_sequence.nr_of_frames
                    # Skip sequence if too small
                    if nr_of_frames < frames:
                        continue
                    for i in range(nr_of_frames):
                        # Get image
                        filename = image_sequence.format.replace('#', str(i))
                        image = PIL.Image.open(filename)
                        # Resize
                        image = image.resize((width, height), PIL.Image.BILINEAR)
                        # Convert to numpy array and normalize
                        image_array = np.array(image).astype(np.float32)
                        image_array /= 255
                        sequence_frames.append(image_array)
                        labels.append(label_dict[label.label.name])

                    if form.cleaned_data['sequence_wise']:
                        if form.cleaned_data['image_dim_ordering'] is 'theano':
                            input = np.ndarray((len(sequence_frames), 1, height, width))
                        else:
                            input = np.ndarray((len(sequence_frames), height, width, 1))

                        if form.cleaned_data['categorical']:
                            output = np.ndarray((len(sequence_frames), len(label_dict)))
                        for i in range(len(sequence_frames)):
                            if form.cleaned_data['image_dim_ordering'] is 'theano':
                                input[i, 0, :, :] = sequence_frames[i]
                            else:
                                input[i, :, :, 0] = sequence_frames[i]

                            if form.cleaned_data['categorical']:
                                output[i] = to_categorical(labels[i], nb_classes=len(label_dict))
                            else:
                                output[i] = labels[i]

                        subj_path = join(path, subject.name)
                        create_folder(subj_path)
                        try:
                            os.stat(subj_path)
                        except:
                            return False, 'Failed to create directory at ' + subj_path

                        f = h5py.File(join(subj_path, os.path.basename(os.path.dirname(image_sequence.format) + '.hd5')), 'w')
                        f.create_dataset("data", data=input, compression="gzip", compression_opts=4, dtype='float32')
                        f.create_dataset("label", data=output, compression="gzip", compression_opts=4, dtype='uint8')
                        f.close()

                        sequence_frames = []
                        labels = []

                if not form.cleaned_data['sequence_wise']:
                    if form.cleaned_data['image_dim_ordering'] is 'theano':
                        input = np.ndarray((len(sequence_frames), 1, height, width))
                    else:
                        input = np.ndarray((len(sequence_frames), height, width, 1))

                    if form.cleaned_data['categorical']:
                        output = np.ndarray((len(sequence_frames), len(label_dict)))
                    for i in range(len(sequence_frames)):
                        if form.cleaned_data['image_dim_ordering'] is 'theano':
                            input[i, 0, :, :] = sequence_frames[i]
                        else:
                            input[i, :, :, 0] = sequence_frames[i]

                        if form.cleaned_data['categorical']:
                            output[i] = to_categorical(labels[i], nb_classes=len(label_dict))
                        else:
                            output[i] = labels[i]

                    f = h5py.File(join(path, subject.name + '.hd5'), 'w')
                    f.create_dataset("data", data=input, compression="gzip", compression_opts=4, dtype='float32')
                    f.create_dataset("label", data=output, compression="gzip", compression_opts=4, dtype='uint8')
                    f.close()


class CardiacSequenceHDFExaminationsExporter(Exporter):
    """
    This exporter will create a folder with 1 hdf5 file for each subject.
    A labels.txt file is also created.
    """

    task_type = Task.CLASSIFICATION
    name = 'Cardiac examinations sequence classification exporter (HDF5)'

    def get_form(self, data=None):
        return CardiacHDFExaminationsExporterForm(self.task, data=data)

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
        try:
            os.stat(path)
        except:
            return False, 'Failed to create directory at ' + path

        self.add_subjects_to_path(path)

        return True, path

    def add_subjects_to_path(self, path):
        # Create label file
        label_file = open(join(path, 'labels.txt'), 'w')
        labels = Label.objects.filter(task=self.task)
        label_dict = {}
        counter = 0
        for label in labels:
            label_file.write(label.name + '\n')
            label_dict[label.name] = counter
            counter += 1
        label_file.close()

        # For each subject
        subjects = Subject.objects.filter(dataset__task=self.task)
        for subject in subjects:
            # Get labeled images
            labeled_images = ProcessedImage.objects.filter(task=self.task, image__subject=subject)
            if labeled_images.count() == 0:
                continue
            width = 128
            height = 128
            frames = 10
            samples = len(labeled_images)
            input = np.zeros((samples, frames, height, width))
            output = np.zeros((samples, len(label_dict)))
            current_sample = 0
            for labeled_image in labeled_images:
                label = ImageLabel.objects.get(image=labeled_image)

                # Get sequence
                key_frame = KeyFrame.objects.get(image=labeled_image.image)
                image_sequence = key_frame.image_sequence
                nr_of_frames = image_sequence.nr_of_frames
                for frame_nr in range(min(nr_of_frames, frames)):
                    # Get image
                    filename = image_sequence.format.replace('#', str(frame_nr))
                    image = PIL.Image.open(filename)
                    # Resize
                    image = image.resize((width, height), PIL.Image.BILINEAR)
                    # Convert to numpy array and normalize
                    image_array = np.array(image).astype(np.float32)
                    image_array /= 255
                    input[current_sample, frame_nr, :, :] = image_array

                output[current_sample, label_dict[label.label.name]] = 1
                current_sample += 1


            # Create hdf5 file for each subject
            f = h5py.File(join(path, subject.name + '.hd5'), 'w')
            f.create_dataset("data", data=input, compression="gzip", compression_opts=4)
            f.create_dataset("label", data=output, compression="gzip", compression_opts=4)
            f.close()
