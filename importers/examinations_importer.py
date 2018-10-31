from common.importer import Importer
from django import forms
from annotationweb.models import Image, ImageSequence, KeyFrame, Dataset, Subject, Metadata
import os
from os.path import join, basename
import glob

class ExaminationsImporterForm(forms.Form):
    path = forms.CharField(label='Data path', max_length=1000)
    file_extension = forms.ChoiceField(choices=(('.png', 'PNG'), ('.mhd', 'MetaImage')),
                                       initial='.png', label='Output image format')

    # TODO validate path

    def __init__(self, data=None):
        super().__init__(data)


class ExaminationsImporter(Importer):
    """
    Data should be sorted in the following way in the root folder:
    Subject 1/
        US_Acq/
            Sequence 1/
                Image_0.mhd
                Image_0.raw/zraw
                ...
            Sequence 2/
                ...
    Subject 2/
        ...

    This importer will create a subject for each subject folder and an image sequence for each subfolder.
    A key frame in the middle of the sequence will be added for each sequence.
    """

    name = 'Examinations importer'
    dataset = None

    def get_form(self, data=None):
        return ExaminationsImporterForm(data)

    def import_data(self, form):
        if self.dataset is None:
            raise Exception('Dataset must be given to importer')

        parent_folder = form.cleaned_data['path']
        file_extension = form.cleaned_data['file_extension']

        # Go through each subfolder and create a subject for each
        for subject_folder in os.listdir(parent_folder):
            subject_folder_path = join(parent_folder,subject_folder)
            if not os.path.isdir(subject_folder_path):
                continue

            subject = Subject()
            subject.name = subject_folder
            subject.dataset = self.dataset
            subject.save()

            if os.path.isdir(join(subject_folder_path, "US_Acq")):
                acq_folder_parent = join(subject_folder_path, "US_Acq")
            else:
                acq_folder_parent = subject_folder_path

            try:
                for acq_folder in os.listdir(acq_folder_parent):
                    image_sequence_dir = join(acq_folder_parent, acq_folder)
                    if not os.path.isdir(image_sequence_dir):
                        continue

                    # Count nr of frames
                    frames = []
                    for file in os.listdir(image_sequence_dir):
                        if file.endswith(file_extension):
                            image_filename = join(image_sequence_dir, file)
                            frames.append(image_filename)

                    if len(frames) == 0:
                        continue

                    image_sequence = ImageSequence()
                    filenames = [basename(file) for file in glob.glob(join(image_sequence_dir, '*' + file_extension))]
                    image_sequence.format = join(image_sequence_dir, longest_common_substring(filenames[0], filenames[1]) +'#'+file_extension) # TODO How to determine this??
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
            except:
                pass

        return True, parent_folder

def longest_common_substring(S1, S2):
    M = [[0]*(1+len(S2)) for i in range(1+len(S1))]
    longest, x_longest = 0, 0
    for x in range(1,1+len(S1)):
        for y in range(1,1+len(S2)):
            if S1[x-1] == S2[y-1]:
                M[x][y] = M[x-1][y-1] + 1
                if M[x][y]>longest:
                    longest = M[x][y]
                    x_longest  = x
            else:
                M[x][y] = 0
    return S1[x_longest-longest: x_longest]