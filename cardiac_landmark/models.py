from django.db import models
from annotationweb.models import ProcessedImage, Label

PHASES = (
    (0, 'End Diastole'),
    (1, 'End Systole'),
)

OBJECTS = (
    (0, 'Anterior'),
    (1, 'Apex'),
    (2, 'Inferior'),
)

class CardiacLandmark(models.Model):
    image = models.OneToOneField(ProcessedImage, on_delete=models.CASCADE)
    frame_ED = models.IntegerField()
    frame_ES = models.IntegerField()

class ControlPoint(models.Model):
    landmark = models.ForeignKey(CardiacLandmark, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    index = models.PositiveIntegerField()
    phase = models.PositiveIntegerField(choices=PHASES)
    object = models.PositiveIntegerField(choices=OBJECTS)
    uncertain = models.BooleanField()
