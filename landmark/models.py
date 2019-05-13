from django.db import models
from annotationweb.models import Annotation, Label


class Landmark(models.Model):
    image = models.ForeignKey(Annotation, on_delete=models.CASCADE)
    x = models.PositiveIntegerField()
    y = models.PositiveIntegerField()
    label = models.ForeignKey(Label)
