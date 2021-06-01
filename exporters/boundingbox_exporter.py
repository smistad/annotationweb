from common.exporter import Exporter
from common.metaimage import MetaImage
from common.utility import create_folder, copy_image
from annotationweb.models import ImageAnnotation, Dataset, Task, Label, Subject, KeyFrameAnnotation
from boundingbox.models import BoundingBox
from django import forms
import os
from os.path import join
from shutil import rmtree, copyfile


class BoundingBoxExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class BoundingBoxExporter(Exporter):
    """
    asdads
    """

    task_type = Task.BOUNDING_BOX
    name = 'Default bounding box exporter'

    def get_form(self, data=None):
        return BoundingBoxExporterForm(self.task, data=data)

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

        # Get labels for this task and write it to labels.txt
        label_file = open(join(path, 'labels.txt'), 'w')
        labels = Label.objects.filter(task=self.task)
        label_dict = {}
        counter = 0
        for label in labels:
            label_file.write(label.name + '\n')
            label_dict[label.id] = counter
            counter += 1
        label_file.close()

        # For each subject
        for subject in data:
            subject_path = join(path, subject.name)
            create_folder(subject_path)
            frames = KeyFrameAnnotation.objects.filter(image_annotation__task=self.task, image_annotation__image__subject=subject, image_annotation__rejected=False)
            for frame in frames:
                image_sequence = frame.image_annotation.image

                # Copy image
                filename = image_sequence.format.replace('#', str(frame.frame_nr))
                target_name = os.path.basename(image_sequence.format).replace('#',str(frame.frame_nr))
                new_filename = join(subject_path, target_name)
                copy_image(filename, new_filename)

                # Write bounding boxes txt file
                boxes = BoundingBox.objects.filter(image=frame)
                with open(join(subject_path, str(frame.frame_nr) + '.txt'), 'w') as f:
                    for box in boxes:
                        center_x = round(box.x + box.width*0.5)
                        center_y = round(box.y + box.height*0.5)
                        label = label_dict[box.label.id]
                        f.write('{} {} {} {} {}\n'.format(label, center_x, center_y, box.width, box.height))

        return True, path

