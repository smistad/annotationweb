from annotationweb.models import Task, Label, Subject, ProcessedImage, Metadata
from annotationweb.forms import ImageListForm
from django.contrib.auth.models import User
from common.label import get_all_labels


class SearchFilter:
    def __init__(self, request, task):
        self.request = request
        self.task = task

        # Get task labels if classification
        self.labels = None
        labels_selected = None
        if task.type == Task.CLASSIFICATION:
            # Get all labels, including sublabels
            self.labels = get_all_labels(task)
            labels_selected = [label['id'] for label in self.labels]

        self.image_quality = [x for x, y in ProcessedImage.IMAGE_QUALITY_CHOICES]
        self.subjects = Subject.objects.filter(dataset__task=task)
        self.users = User.objects.filter(processedimage__task=task).distinct()

        # Get metadata for task
        self.metadata = Metadata.objects.values('value', 'name').filter(image__subject__dataset__task=task).distinct()

        if 'search_filters'+str(task.id) not in request.session:
            request.session['search_filters'+str(task.id)] = {}

            # Set initial values
            sort_by = ImageListForm.SORT_DATE_DESC # Default sort
            self.set_value('sort_by', sort_by)
            self.set_value('image_quality', self.image_quality)
            subjects_selected = [subject.id for subject in self.subjects]
            self.set_value('subject', subjects_selected)
            self.set_value('label', labels_selected)
            users_selected = [user.id for user in self.users]
            self.set_value('user', users_selected)
            metadata_selected = []
            self.set_value('metadata', metadata_selected)

    def set_value(self, name, value):
        self.request.session['search_filters'+str(self.task.id)][name] = value

    def create_form(self, data=None):
        if data is None:
            form = ImageListForm(self.subjects, self.users, self.metadata, data=self.request.session['search_filters'+str(self.task.id)], labels=self.labels)
        else:
            form = ImageListForm(self.subjects, self.users, self.metadata, data=data, labels=self.labels)
            # Update search filters with contents of form if it is valid
            if form.is_valid():
                for key, value in form.cleaned_data.items():
                    if key in self.request.session['search_filters'+str(self.task.id)]:
                        self.set_value(key, value)
        return form

    def get_value(self, name):
        return self.request.session['search_filters'+str(self.task.id)][name]

    def delete(self):
        del self.request.session['search_filters'+str(self.task.id)]
