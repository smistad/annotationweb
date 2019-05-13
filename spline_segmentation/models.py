from django.db import models
from annotationweb.models import Annotation, Label


class ControlPoint(models.Model):
    image = models.ForeignKey(Annotation, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    index = models.PositiveIntegerField()
    label = models.ForeignKey(Label)
    uncertain = models.BooleanField()
