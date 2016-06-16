from django import forms
from .models import *

class SegmentationTaskForm(forms.ModelForm):
    class Meta:
        model = SegmentationTask
        fields = ['name', 'dataset', 'label']
