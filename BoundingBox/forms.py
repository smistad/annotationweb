from django import forms
from .models import *

class BoundingBoxTaskForm(forms.ModelForm):
    class Meta:
        model = BoundingBoxTask
        fields = ['name', 'dataset', 'label']
