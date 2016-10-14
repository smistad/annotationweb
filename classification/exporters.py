from common.exporter import Exporter
from annotationweb.models import ProcessedImage, Dataset, Task, Label
from classification.models import ImageLabel
from django import forms
import os
from shutil import rmtree, copyfile


class ClassificationExporterForm(forms.Form):
    path = forms.CharField(label='Storage path', max_length=1000)
    delete_existing_data = forms.BooleanField(label='Delete any existing data at storage path', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data)
        self.fields['dataset'] = forms.ModelMultipleChoiceField(queryset=Dataset.objects.filter(task=task))


"""
This exporter will create a folder at the given path and create 2 files:
labels.txt      - list of labels
file_list.txt   - list of files and labels
A folder is created for each dataset with the actual images
"""
class ClassificationExporter(Exporter):
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
            image_filename = name[name.rfind('/')+1:]
            dataset_path = os.path.join(path, labeled_image.image.dataset.name)
            try:
                os.mkdir(dataset_path) # Make dataset path if doesn't exist
            except:
                pass
            new_filename = os.path.join(dataset_path, image_filename)
            copyfile(name, new_filename)

            # Get image label
            label = ImageLabel.objects.get(image=labeled_image)

            # TODO metaimage support
            file_list.write(new_filename + ' ' + str(labelDict[label.label.name]) + '\n')

        file_list.close()

        return True, path


