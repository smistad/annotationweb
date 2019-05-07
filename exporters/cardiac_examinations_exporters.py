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
from common.label import get_all_labels, get_complete_label_name


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
    displayed_frames_only = forms.BooleanField(label='Only export the frames displayed in the task.', initial=False, required=False, help_text='If a task only shows the X frames before and after target frame, only those frames are exported.')
    categorical = forms.BooleanField(label='Categorical labels', initial=False, required=False)
    colormode = forms.ChoiceField(label='Color model',
                                  choices=(('L', 'Grayscale'), ('RGB', 'RGB')),
                                  required=False,
                                  widget=forms.RadioSelect(renderer=HorizontalRadioRenderer),
                                  initial='L'
                                  )
    width = forms.IntegerField(max_value=512, label='Width', initial=128) # TODO: Fix layout...
    height = forms.IntegerField(max_value=512, label='Height', initial=128)

    def __init__(self, task, data=None):
        super().__init__(data)
        labels = get_all_labels(task)
        self.fields['labels'] = forms.MultipleChoiceField(
            choices=((label['id'], label['name']) for label in labels),
            initial=[label['id'] for label in labels],
            help_text='When parent labels are selected, sublabels selected will be linked to the parent label '
                      '(and only those ones). '
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

        # Create a .txt file with the labels matching the sequence name
        sequence_label_file = open(join(path, 'sequence_to_label.txt'), 'w')

        # Find labels with parents
        labels = form.cleaned_data['labels']
        label_dict = {}
        has_parent_dict = {}
        label_file.write('All labels involved: \n\n')
        for label_id in labels:
            label = Label.objects.get(pk=label_id)
            label_name = get_complete_label_name(label)
            label_file.write(label_name + '\n')
            has_parent_dict[label_name] = False
            label_dict[label_name] = None

        for start_label in has_parent_dict:
            for full_label in has_parent_dict:
                if full_label.startswith(start_label) & (start_label != full_label):
                    has_parent_dict[full_label] = True

        # Assign children to the parent class
        label_file.write('\nClassification based on the following parent labels: \n\n')
        counter = 0
        for label in has_parent_dict:
            if has_parent_dict[label] == False:
                label_file.write(label + '\n')
                for label_name in label_dict:
                    if label_name.startswith(label):
                        label_dict[label_name] = counter
                counter += 1
        nb_parent_classes = counter

        label_file.close()

        # For each subject
        subjects = Subject.objects.filter(dataset__task=self.task)
        for subject in subjects:
            # Get labeled images
            labeled_images = ProcessedImage.objects.filter(task=self.task, image__subject=subject, rejected=False)
            if labeled_images.count() == 0:
                continue

            width = form.cleaned_data['width']
            height = form.cleaned_data['height']

            sequence_frames = []
            labels = []

            for labeled_image in labeled_images:
                label = ImageLabel.objects.get(image=labeled_image)

                if get_complete_label_name(label.label) in label_dict.keys():
                    # Get sequence
                    key_frame = KeyFrame.objects.get(image=labeled_image.image)
                    image_sequence = key_frame.image_sequence
                    nr_of_frames = image_sequence.nr_of_frames

                    start_frame = 0
                    end_frame = nr_of_frames
                    if form.cleaned_data['displayed_frames_only'] and not self.task.show_entire_sequence:
                        start_frame = max(0, key_frame.frame_nr - self.task.frames_before)
                        end_frame = min(nr_of_frames, key_frame.frame_nr + self.task.frames_after + 1)

                    for i in range(start_frame, end_frame):
                        # Get image
                        filename = image_sequence.format.replace('#', str(i))
                        if filename[-4:] == '.mhd':
                            metaimage = MetaImage(filename=filename)
                            image = metaimage.get_image()
                        else:
                            image = PIL.Image.open(filename)

                        # Setup assigned colormode
                        if form.cleaned_data['colormode'] != image.mode:
                            image = image.convert(form.cleaned_data['colormode'])

                        # Resize
                        image = image.resize((width, height), PIL.Image.BILINEAR)

                        # Convert to numpy array and normalize
                        image_array = np.array(image).astype(np.float32)
                        image_array /= 255

                        if len(image_array.shape) != 3:
                            image_array = image_array[..., None]

                        sequence_frames.append(image_array)
                        labels.append(label_dict[get_complete_label_name(label.label)])

                    if form.cleaned_data['sequence_wise'] and len(sequence_frames) > 0:
                        input = np.array(sequence_frames, dtype=np.float32)
                        output = np.array(labels, dtype=np.uint8)

                        sequence_label_file.write(join(subject.name, os.path.basename(os.path.dirname(image_sequence.format))) + '\t' + str(output[0]) + '\n')

                        if form.cleaned_data['image_dim_ordering'] == 'theano':
                            input = np.transpose(input, [0,3,1,2])

                        if form.cleaned_data['categorical']:
                            output = to_categorical(output, nb_classes=nb_parent_classes)

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

            if not form.cleaned_data['sequence_wise'] and len(sequence_frames) > 0:
                input = np.array(sequence_frames, dtype=np.float32)
                output = np.array(labels, dtype=np.uint8)

                if form.cleaned_data['image_dim_ordering'] == 'theano':
                    input = np.transpose(input, [0, 3, 1, 2])

                if form.cleaned_data['categorical']:
                    output = to_categorical(output, nb_classes=len(label_dict))

                f = h5py.File(join(path, subject.name + '.hd5'), 'w')
                f.create_dataset("data", data=input, compression="gzip", compression_opts=4, dtype='float32')
                f.create_dataset("label", data=output, compression="gzip", compression_opts=4, dtype='uint8')
                f.close()
        sequence_label_file.close()
