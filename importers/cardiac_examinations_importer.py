from importers.importer import Importer
from django import forms
from annotationweb.models import Image, ImageSequence, KeyFrame, Dataset, Subject
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
            if not os.path.isdir(file):
                continue

            subject = Subject()
            subject.name = file
            subject.dataset = self.dataset
            subject.save()

            for file2 in os.listdir(os.path.join(path, file)):
                if not os.path.isdir(file2):
                    continue

                frames = []
                for file3 in os.listdir(join(join(path, file), file2)):
                    if not os.path.isfile(file3):
                        continue

                    image = Image()
                    image.subject = subject
                    image.filename = join(join(join(path, file), file2), file3)
                    image.save()
                    frames.append(image)

                image_sequence = ImageSequence()
                image_sequence.format = 'US_2D_#.png' # TODO How to determine this??
                image_sequence.subject = subject
                image_sequence.nr_of_frames = len(frames)
                image_sequence.save()

                # Create key frame
                key_frame_nr = len(frames)/2
                key_frame = KeyFrame()
                key_frame.image_sequence = image_sequence
                key_frame.frame_nr = key_frame_nr
                key_frame.image = frames[key_frame_nr]
                key_frame.save()


        return True, path
