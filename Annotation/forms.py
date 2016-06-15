from django import forms
from .models import *

class ImportLocalDatasetForm(forms.Form):
    name = forms.CharField(label='Dataset name', max_length=100)
    path = forms.CharField(label='Dataset path', max_length=1000)

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['name', 'dataset']

class ImageSequenceForm(forms.ModelForm):
    class Meta:
        model = ImageSequence
        fields = ['format']
