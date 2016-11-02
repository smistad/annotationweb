from django import forms
from .models import *


class ImportLocalDatasetForm(forms.Form):
    name = forms.CharField(label='Dataset name', max_length=100)
    path = forms.CharField(label='Dataset path', max_length=1000)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'dataset', 'show_entire_sequence', 'frames_before',
                  'frames_after', 'auto_play', 'type', 'label', 'user', 'description']


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
        fields = ['format', 'nr_of_frames']


class LabelForm(forms.ModelForm):
    class Meta:
        model = Label
        fields = ['name', 'color_red', 'color_blue', 'color_green']


class ImageListForm(forms.Form):
    SORT_IMAGE_ID = 'image_id'
    SORT_DATE_DESC = 'date_desc'
    SORT_DATE_ASC = 'date_asc'
    SORT_CHOICES = (
        (SORT_IMAGE_ID, 'All images'),
        (SORT_DATE_DESC, 'Annotated images (newest first)'),
        (SORT_DATE_ASC, 'Annotated images (oldest first)'),
    )
    sort_by = forms.ChoiceField(
        label='Show',
        choices=SORT_CHOICES,
        initial=SORT_IMAGE_ID,
        widget=forms.Select(attrs={'onchange': 'this.form.submit();'})
    )
