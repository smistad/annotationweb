from common.exporter import Exporter
from common.metaimage import MetaImage
from common.utility import create_folder, copy_image
from annotationweb.models import ImageAnnotation, Dataset, Task, Label, Subject, KeyFrameAnnotation
from django import forms
import os
from os.path import join
from shutil import rmtree, copyfile
from landmark.models import Landmark


class LandmarkExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['subjects'] = forms.ModelMultipleChoiceField(
            queryset=Subject.objects.filter(dataset__task=task))


class LandmarkExporter(Exporter):
    """
    asdads
    """

    task_type = Task.LANDMARK
    name = 'Default landmark exporter'

    def get_form(self, data=None):
        return LandmarkExporterForm(self.task, data=data)

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
            annotations = ImageAnnotation.objects.filter(task=self.task, image__subject=subject, rejected=False)
            for annotation in annotations:
                frames = KeyFrameAnnotation.objects.filter(image_annotation=annotation)
                storage_path = join(path, subject.name)
                create_folder(storage_path)
                with open(join(storage_path, str(annotation.id) + '.txt'), 'w') as f:
                    f.write(subject.name + '\n')
                    f.write(annotation.image.format + '\n')
                    f.write((annotation.comments).encode('ascii', 'ignore').decode('ascii').replace('\n', '<br>') + '\n') # Encoding fix
                    # Get aspect ratio to correct x landmarks, because they are stored with isotropic spacing, while images
                    # are often not stored in isotropic spacing
                    metaimage = MetaImage(filename=annotation.image.format.replace('#', str(0)))
                    spacingX = metaimage.get_spacing()[0]
                    spacingY = metaimage.get_spacing()[1]
                    aspect = (spacingY / spacingX)
                    for frame in frames:
                        # Write bounding boxes txt file
                        landmarks = Landmark.objects.filter(image=frame)
                        for landmark in landmarks:
                            label = label_dict[landmark.label.id]
                            f.write(f'{frame.frame_nr} {label} {int(round(landmark.x*aspect))} {landmark.y}\n')

        return True, path

