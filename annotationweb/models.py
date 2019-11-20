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


class Label(models.Model):
    name = models.CharField(max_length=200)

    # Color stored as R G B with values from 0 to 255
    color_red = models.PositiveSmallIntegerField(default=255)
    color_green = models.PositiveSmallIntegerField(default=0)
    color_blue = models.PositiveSmallIntegerField(default=0)

    parent = models.ForeignKey('Label', blank=True, null=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Task(models.Model):
    SEGMENTATION = 'segmentation'
    CLASSIFICATION = 'classification'
    BOUNDING_BOX = 'boundingbox'
    LANDMARK = 'landmark'
    CARDIAC_SEGMENTATION = 'cardiac_segmentation'
    CARDIAC_LANDMARK = 'cardiac_landmark'
    SPLINE_SEGMENTATION = 'spline_segmentation'
    TASK_TYPES = (
        (CLASSIFICATION, 'Classification'),
        (SEGMENTATION, 'Segmentation'),
        (BOUNDING_BOX, 'Bounding box'),
        (LANDMARK, 'Landmark'),
        (CARDIAC_SEGMENTATION, 'Cardiac segmentation'),
        (CARDIAC_LANDMARK, 'Cardiac landmark'),
        (SPLINE_SEGMENTATION, 'Spline segmentation')
    )

    name = models.CharField(max_length=200)
    dataset = models.ManyToManyField(Dataset)
    show_entire_sequence = models.BooleanField(help_text='Allow user to see entire sequence.', default=False)
    frames_before = models.PositiveIntegerField(help_text='How many frames to allow user to see before a key frame', default=0)
    frames_after = models.PositiveIntegerField(help_text='How many frames to allow user to see after a key frame', default=0)
    auto_play = models.BooleanField(help_text='Auto play image sequences', default=True)
    shuffle_videos = models.BooleanField(help_text='Shuffle videos for annotation task', default=True)
    user_frame_selection = models.BooleanField(help_text='Annotaters can select which frames to annotate in a video', default=False)
    annotate_single_frame = models.BooleanField(help_text='Annotate a single frame at a time in videos', default=True)
    type = models.CharField(max_length=50, choices=TASK_TYPES)
    label = models.ManyToManyField(Label,
           help_text='<button onclick="'
                     'window.open(\'/new-label/\', \'Add new label\', \'width=400,height=400,scrollbars=no\');"'
                     ' type="button">Add new label</button>')
    user = models.ManyToManyField(User)
    description = models.TextField(default='', blank=True)
    large_image_layout = models.BooleanField(default=False, help_text='Use a large image layout for annotation')
    post_processing_method = models.CharField(default='', help_text='Name of post processing method to use', max_length=255)

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


class ImageAnnotation(models.Model):
    """
    Represents an annotation of an entire image sequence
    """

    image = models.ForeignKey(ImageSequence, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    QUALITY_POOR = 'poor'
    QUALITY_OK = 'ok'
    QUALITY_GOOD = 'good'
    IMAGE_QUALITY_CHOICES = (
        (QUALITY_POOR, 'Poor'),
        (QUALITY_OK, 'OK'),
        (QUALITY_GOOD, 'Good'),
    )
    image_quality = models.CharField(max_length=50, choices=IMAGE_QUALITY_CHOICES)
    comments = models.TextField()
    rejected = models.BooleanField()


class KeyFrameAnnotation(models.Model):
    """
    Represents an annotation of a frame of an image_sequence
    """

    frame_nr = models.PositiveIntegerField()
    image_annotation = models.ForeignKey(ImageAnnotation, on_delete=models.CASCADE)
    frame_metadata = models.CharField(default='', max_length=512, help_text='A text field for storing arbitrary metadata on the current frame')

    def __str__(self):
        return str(self.frame_nr)


# Used to attach metadata to images, such as acquisition parameters
class ImageMetadata(models.Model):
    image = models.ForeignKey(ImageSequence, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    value = models.CharField(max_length=256)

    def __str__(self):
        return self.name + ': ' + self.value