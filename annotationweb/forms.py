from django import forms
from django.core.exceptions import ValidationError

from .models import *


class ImportLocalDatasetForm(forms.Form):
    name = forms.CharField(label='Dataset name', max_length=100)
    path = forms.CharField(label='Dataset path', max_length=1000)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'dataset', 'type',
                  'classification_type',
                  'show_entire_sequence', 'frames_before', 'frames_after', 'auto_play',
                  'user_frame_selection', 'annotate_single_frame', 'shuffle_videos',
                  'label', 'user', 'description']

    def clean_classification_type(self):
        data = self.cleaned_data['classification_type']
        if self.cleaned_data['type'] == 'classification':
            if data == '':
                raise ValidationError(
                    "You chose the task type classification, but have forgotten to choose classification type",
                    code='invalid'
                )
            else:
                pass
        else:
            data = None

        # Always return a value to use as the new cleaned data, even if
        # this method didn't change it.
        return data

    def clean(self):
        cleaned_data = super(TaskForm, self).clean()
    #     user_frame_selection = cleaned_data.get('user_frame_selection')
    #     annotate_single_frame = cleaned_data.get('annotate_single_frame')

        task_type = cleaned_data.get('type')
        classification_type = cleaned_data.get('classification_type')

        if task_type == 'classification':
            if classification_type == '':
                raise ValidationError(
                    "No classification type was chosen, but task type is Classification",
                    code='invalid'
                )


class DatasetForm(forms.ModelForm):
    class Meta:
        model = Dataset
        fields = ['name']


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['name']


class ImageSequenceForm(forms.ModelForm):
    class Meta:
        model = ImageSequence
        fields = ['format']


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ['name', 'color_red', 'color_blue', 'color_green', 'parent']


class ImageListForm(forms.Form):
    SORT_IMAGE_ID = 'image_id'
    SORT_DATE_DESC = 'date_desc'
    SORT_DATE_ASC = 'date_asc'
    SORT_NOT_ANNOTATED_IMAGE_ID = 'not_annotated_image_id'
    SORT_CHOICES = (
        (SORT_IMAGE_ID, 'All images'),
        (SORT_DATE_DESC, 'Annotated images (newest first)'),
        (SORT_DATE_ASC, 'Annotated images (oldest first)'),
        (SORT_NOT_ANNOTATED_IMAGE_ID, 'Non-annotated images'),
    )
    sort_by = forms.ChoiceField(
        label='Show',
        choices=SORT_CHOICES,
        required=False,
        initial=SORT_IMAGE_ID,
        widget=forms.Select(attrs={'onchange': 'this.form.submit();'})
    )
    image_quality = forms.MultipleChoiceField(
        label='Image quality',
        choices=ImageAnnotation.IMAGE_QUALITY_CHOICES,
        initial=[x for x, y in ImageAnnotation.IMAGE_QUALITY_CHOICES],
        widget=forms.SelectMultiple(attrs={'onchange': 'this.form.submit();'})
    )

    def __init__(self, subjects, users, metadata, data=None, labels=None, initial=None):
        super().__init__(data, initial=initial)

        if labels is not None:
            self.fields['label'] = forms.MultipleChoiceField(
                label='Labels',
                choices=((label['id'], label['name']) for label in labels),
                initial=[label['id'] for label in labels],
                widget=forms.SelectMultiple(attrs={'onchange': 'this.form.submit();'})
            )

        self.fields['subject'] = forms.MultipleChoiceField(
            label='Subjects',
            choices=((subject.id, subject.dataset.name + ': ' + subject.name) for subject in subjects),
            initial=[subject.id for subject in subjects],
            widget=forms.SelectMultiple(attrs={'onchange': 'this.form.submit();'})
        )

        if len(users) > 0:
            self.fields['user'] = forms.MultipleChoiceField(
                label='Users',
                choices=((user.id, user.username) for user in users),
                initial=[user.id for user in users],
                widget=forms.SelectMultiple(attrs={'onchange': 'this.form.submit();'})
            )

        if len(metadata) > 0:
            self.fields['metadata'] = forms.MultipleChoiceField(
                label='Metadata',
                required=False,
                choices=((item['name'] + ': ' + item['value'], item['name'] + ': ' + item['value']) for item in metadata),
                #initial=[item['name'] + ': ' + item['value'] for item in metadata],
                widget=forms.SelectMultiple(attrs={'onchange': 'this.form.submit();'})
            )


class CopyTaskForm(forms.Form):
    name = forms.CharField(label='Task name', max_length=1000)
    keep_image_quality = forms.BooleanField(label='Keep image quality', initial=False, required=False)

    def __init__(self, task, data=None):
        super().__init__(data=data)
        self.fields['name'].initial = task.name + " Copy"
