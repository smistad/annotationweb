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
            label_file.write(label.name + '\n')
            labelDict[label.name] = counter
            counter += 1
        label_file.close()

        # Create file_list.txt file
        file_list = open(os.path.join(path, 'file_list.txt'), 'w')
        labeled_images = ProcessedImage.objects.filter(task=self.task, image__dataset__in=datasets)
        for labeled_image in labeled_images:
            name = labeled_image.image.filename
            dataset_path = os.path.join(path, labeled_image.image.dataset.name)
            try:
                os.mkdir(dataset_path) # Make dataset path if doesn't exist
            except:
                pass

            image_id = labeled_image.image.id
            new_extension = form.cleaned_data['output_image_format']
            new_filename = os.path.join(dataset_path, str(image_id) + '.' + new_extension)
            copy_image(name, new_filename)

            # Get image label
            label = ImageLabel.objects.get(image=labeled_image)

            file_list.write(new_filename + ' ' + str(labelDict[label.label.name]) + '\n')

        file_list.close()

        return True, path


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


class CardiacHDFExaminationsExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)
    # TODO add how many frames
    # TODO set image size


class CardiacHDFExaminationsExporter(Exporter):
    """
    This exporter will create a folder with 1 hdf5 file for each subject.
    A labels.txt file is also created.
    """

    task_type = Task.CLASSIFICATION
    name = 'Cardiac examinations classification exporter (HDF5)'

    def get_form(self, data=None):
        return CardiacHDFExaminationsExporterForm(data=data)

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
            minisequences = []
            labels = []
            width = 128
            height = 128
            frames = 10
            for labeled_image in labeled_images:
                label = ImageLabel.objects.get(image=labeled_image)

                # Get sequence
                key_frame = KeyFrame.objects.get(image=labeled_image.image)
                image_sequence = key_frame.image_sequence
                nr_of_frames = image_sequence.nr_of_frames
                # Skip sequence if too small
                if nr_of_frames < frames:
                    continue
                sequence_frames = []
                for i in range(nr_of_frames):
                    # Get image
                    filename = image_sequence.format.replace('#', str(i))
                    image = PIL.Image.open(filename)
                    # Resize
                    image = image.resize((width, height), PIL.Image.BILINEAR)
                    # Convert to numpy array
                    image_array = np.array(image)
                    sequence_frames.append(image_array)

                # Sample minisequences from sequence
                for i in range(nr_of_frames-frames):
                    minisequence = np.ndarray((frames, height, width))
                    for j in range(frames):
                        minisequence[j, :, :] = sequence_frames[i+j]
                    minisequences.append(minisequence)
                    labels.append(label_dict[label.label.name])


            # TODO Create hdf5 files and insert data
            # Collect data as ndarrays
            input = np.ndarray((len(minisequences), 10, height, width))
            output = np.ndarray((len(minisequences), 1, 1, 1))
            for i in range(len(minisequences)):
                input[i,:,:,:] = minisequences[i]
                output[i,0,0,0] = labels[i]

            f = h5py.File(join(path, subject.name + '.hd5'), 'w')
            f.create_dataset("data", data=input, compression="gzip", compression_opts=4)
            f.create_dataset("label", data=output, compression="gzip", compression_opts=4)
            f.close()



