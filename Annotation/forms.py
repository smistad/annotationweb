from django import forms

class ImportLocalDatasetForm(forms.Form):
    name = forms.CharField(label='Dataset name', max_length=100)
    path = forms.CharField(label='Dataset path', max_length=1000)
