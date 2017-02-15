from django.db import models
from django.contrib.auth.models import User


class Dataset(models.Model):
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Subject(models.Model):
    name = models.CharField(max_length=200, help_text='Use anonymized id')
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    def __str__(self):
        return self.dataset.name + ' - ' + self.name

    class Meta:
        ordering = ['name']


class Image(models.Model):
    filename = models.CharField(max_length=255)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)

    def __str__(self):
        return self.filename


class Label(models.Model):
    name = models.CharField(max_length=200)

    # Color stored as R G B with values from 0 to 255
    color_red = models.PositiveSmallIntegerField()
    color_green = models.PositiveSmallIntegerField()
    color_blue = models.PositiveSmallIntegerField()

    parent = models.ForeignKey('Label', blank=True, null=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    SEGMENTATION = 'segmentation'
    CLASSIFICATION = 'classification'
    BOUNDING_BOX = 'boundingbox'
    LANDMARK = 'landmark'
    TASK_TYPES = (
        (CLASSIFICATION, 'Classification'),
        (SEGMENTATION, 'Segmentation'),
        (BOUNDING_BOX, 'Bounding box'),
        (LANDMARK, 'Landmark'),
    )

    name = models.CharField(max_length=200)
    dataset = models.ManyToManyField(Dataset)
    show_entire_sequence = models.BooleanField(help_text='Allow user to see entire sequence.', default=False)
    frames_before = models.PositiveIntegerField(help_text='How many frames to allow user to see before a key frame', default=0)
    frames_after = models.PositiveIntegerField(help_text='How many frames to allow user to see after a key frame', default=0)
    auto_play = models.BooleanField(help_text='Auto play image sequences', default=True)
    type = models.CharField(max_length=50, choices=TASK_TYPES)
    label = models.ManyToManyField(Label,
           help_text='<button onclick="'
                     'window.open(\'/new-label/\', \'Add new label\', \'width=400,height=200,scrollbars=no\');"'
                     ' type="button">Add new label</button>')
    user = models.ManyToManyField(User)
    description = models.TextField(default='', blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class ImageSequence(models.Model):
    format = models.CharField(max_length=1024, help_text='Should contain # which will be replaced with an integer, '
                                                         'increasing with 1 for each frame. E.g. /path/to/frame_#.png')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    nr_of_frames = models.PositiveIntegerField()
    start_frame_nr = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.format


class KeyFrame(models.Model):
    frame_nr = models.PositiveIntegerField()
    image_sequence = models.ForeignKey(ImageSequence, on_delete=models.CASCADE)
    image = models.OneToOneField(Image, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.frame_nr)


# TODO: Rename this model to Annotation
class ProcessedImage(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)

    QUALITY_POOR = 'poor'
    QUALITY_OK = 'ok'
    QUALITY_GOOD = 'good'
    IMAGE_QUALITY_CHOICES = (
        (QUALITY_POOR, 'Poor'),
        (QUALITY_OK, 'OK'),
        (QUALITY_GOOD, 'Good'),
    )
    image_quality = models.CharField(max_length=50, choices=IMAGE_QUALITY_CHOICES)


# Used to attach metadata to images, such as acquisition parameters
class Metadata(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=256)

    def __str__(self):
        return self.name + ': ' + self.value

