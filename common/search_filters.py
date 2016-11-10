from annotationweb.models import Task, Label, Subject, ProcessedImage
from annotationweb.forms import ImageListForm


class SearchFilter:
    def __init__(self, request, task):
        self.request = request
        self.task = task

        # Get task labels if classification
        self.labels = None
        labels_selected = None
        if task.type == Task.CLASSIFICATION:
            self.labels = Label.objects.filter(task=task)
            labels_selected = [label.id for label in self.labels]

        sort_by = ImageListForm.SORT_DATE_DESC # Default sort
        self.image_quality = [x for x, y in ProcessedImage.IMAGE_QUALITY_CHOICES]
        self.subjects = Subject.objects.filter(dataset__task=task)
        subjects_selected = [subject.id for subject in self.subjects]

        if 'search_filters'+str(task.id) not in request.session:
            request.session['search_filters'+str(task.id)] = {}

            # Set initial values
            self.set_value('sort_by', sort_by)
            self.set_value('image_quality', self.image_quality)
            self.set_value('subject', subjects_selected)
            self.set_value('label', labels_selected)

    def set_value(self, name, value):
        self.request.session['search_filters'+str(self.task.id)][name] = value

    def create_form(self, data=None):
        if data is None:
            form = ImageListForm(self.subjects, data=self.request.session['search_filters'+str(self.task.id)], labels=self.labels)
        else:
            form = ImageListForm(self.subjects, data=data, labels=self.labels)
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
