from django.db import models

from annotationweb.models import ProcessedImage

PHASES = (
    (0, 'End Diastole'),
    (1, 'End Systole'),
)

OBJECTS = (
    (0, 'Endocardium'),
    (1, 'Epicardium'),
    (2, 'Left atrium'),
)


class Segmentation(models.Model):
    image = models.OneToOneField(ProcessedImage, on_delete=models.CASCADE)
    frame_ED = models.PositiveIntegerField()
    frame_ES = models.PositiveIntegerField()
    motion_mode_line = models.PositiveIntegerField()


class ControlPoint(models.Model):
    segmentation = models.ForeignKey(Segmentation, on_delete=models.CASCADE)
    x = models.FloatField()
    y = models.FloatField()
    index = models.PositiveIntegerField()
    phase = models.PositiveIntegerField(choices=PHASES)
    object = models.PositiveIntegerField(choices=OBJECTS)
    uncertain = models.BooleanField()
