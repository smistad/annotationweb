from common.importer import Importer
from django import forms
from annotationweb.models import Image, ImageSequence, KeyFrame, Dataset, Subject, Metadata
import os
from os.path import join


class CardiacExaminationsImporterForm(forms.Form):
    path = forms.CharField(label='Data path', max_length=1000)

    # TODO validate path

    def __init__(self, data=None):
        super().__init__(data)


class CardiacExaminationsImporter(Importer):
    """
    Data should be sorted in the following way in the root folder:
    Subject 1/
        Sequence 1/
            Image_0.png
            Image_1.png
            ...
        Sequence 2/
            ...
    Subject 2/
        ...

    This importer will create a subject for each subject folder and an image sequence for each subfolder.
    A key frame in the middle of the sequence will be added for each sequence.
    """

    name = 'Cardiac examinations importer'
    dataset = None

    def get_form(self, data=None):
        return CardiacExaminationsImporterForm(data)

    def import_data(self, form):
        if self.dataset is None:
            raise Exception('Dataset must be given to importer')

        path = form.cleaned_data['path']
        # Go through each subfolder and create a subject for each
        for file in os.listdir(path):
            subject_dir = join(path, file)
            if not os.path.isdir(subject_dir):
                continue

            subject = Subject()
            subject.name = file
            subject.dataset = self.dataset
            subject.save()

            for file2 in os.listdir(subject_dir):
                image_sequence_dir = join(subject_dir, file2)
                if not os.path.isdir(image_sequence_dir):
                    continue

                # Count nr of frames
                frames = []
                for file3 in os.listdir(image_sequence_dir):
                    if file3[-4:] == '.png':
                        image_filename = join(image_sequence_dir, file3)
                        frames.append(image_filename)

                if len(frames) == 0:
                    continue

                image_sequence = ImageSequence()
                image_sequence.format = join(image_sequence_dir, 'US-2D_#.png') # TODO How to determine this??
                image_sequence.subject = subject
                image_sequence.nr_of_frames = len(frames)
                image_sequence.save()

                # Create key frame
                key_frame_nr = int(len(frames)/2)
                image = Image()
                image.filename = frames[key_frame_nr]
                image.subject = subject
                image.save()

                key_frame = KeyFrame()
                key_frame.image_sequence = image_sequence
                key_frame.frame_nr = key_frame_nr
                key_frame.image = image
                key_frame.save()

                # Check if metadata.txt exists, and if so parse it and add
                metadata_filename = join(image_sequence_dir, 'metadata.txt')
                if os.path.exists(metadata_filename):
                    with open(metadata_filename, 'r') as f:
                        for line in f:
                            parts = line.split(':')
                            if len(parts) != 2:
                                raise Exception('Excepted 2 parts when spliting metadata in file ' + metadata_filename)

                            # Save to DB
                            metadata = Metadata()
                            metadata.image = image
                            metadata.name = parts[0].strip()
                            metadata.value = parts[1].strip()
                            metadata.save()

        return True, path
