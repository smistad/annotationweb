from django.db import models
from django.contrib.auth.models import User


class Dataset(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Image(models.Model):
    filename = models.CharField(max_length=255)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    def __str__(self):
        return self.filename


class Label(models.Model):
    name = models.CharField(max_length=200)

    # Color stored as R G B with values from 0 to 255
    color_red = models.PositiveSmallIntegerField()
    color_green = models.PositiveSmallIntegerField()
    color_blue = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name


class Task(models.Model):
    SEGMENTATION = 'segmentation'
    CLASSIFICATION = 'classification'
    BOUNDING_BOX = 'boundingbox'
    TASK_TYPES = (
        (CLASSIFICATION, 'Classification'),
        (SEGMENTATION, 'Segmentation'),
        (BOUNDING_BOX, 'Bounding box'),
    )

    name = models.CharField(max_length=200)
    dataset = models.ManyToManyField(Dataset)
    show_entire_sequence = models.BooleanField(help_text='Allow user to see entire sequence.', default=False)
    frames_before = models.PositiveIntegerField(help_text='How many frames to allow user to see before a key frame', default=0)
    frames_after = models.PositiveIntegerField(help_text='How many frames to allow user to see after a key frame', default=0)
    type = models.CharField(max_length=50, choices=TASK_TYPES)
    label = models.ManyToManyField(Label)
    user = models.ManyToManyField(User)

    def __str__(self):
        return self.name


class ImageSequence(models.Model):
    format = models.CharField(max_length=1024)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    nr_of_frames = models.PositiveIntegerField()

    def __str__(self):
        return self.format


class KeyFrame(models.Model):
    frame_nr = models.PositiveIntegerField()
    image_sequence = models.ForeignKey(ImageSequence, on_delete=models.CASCADE)
    image = models.OneToOneField(Image, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.frame_nr)