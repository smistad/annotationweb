import datetime
from typing import overload, List
import yaml
import sys


class Serialization():
    def __init__(self):
        self.data = []
        # Reset counters:
        SerializationObject.reset()

    def add(self, data:dict):
        self.data.append(data)

    def save(self, filename):
        with open(filename, 'w') as file:
            yaml.dump(self.data, file, sort_keys=False)

    def print(self):
        yaml.dump(self.data, sys.stdout, sort_keys=False)


class SerializationObject():
    OBJECTS_SEEN = set()

    def __init__(self, serialization:Serialization, cls):
        self.serialization = serialization
        if cls not in SerializationObject.OBJECTS_SEEN:
            # Reset counter to 1
            cls.counter = 1
            SerializationObject.OBJECTS_SEEN.add(cls)
        else:
            cls.counter += 1
        print(SerializationObject.OBJECTS_SEEN, cls.counter)
        self.id = cls.counter

    @classmethod
    def reset(cls):
        cls.OBJECTS_SEEN.clear()


class ImageSequence(SerializationObject):
    def __init__(self, serialization: Serialization, format:str, nr_of_frames:int, start_frame_nr:int, subject):
        super().__init__(serialization, ImageSequence)
        serialization.add({
            'model': 'annotationweb.imagesequence',
            'pk': f'$annotationweb$imagesequence${self.id}$',
            'fields': {
                'format': format,
                'subject': f'$annotationweb$subject${subject.id}$',
                'nr_of_frames': nr_of_frames,
                'start_frame_nr': start_frame_nr,
            },
        })


class Subject(SerializationObject):
    counter = 1

    def __init__(self, serialization: Serialization, name, dataset):
        super().__init__(serialization, Subject)
        serialization.add({
            'model': 'annotationweb.subject',
            'pk': f'$annotationweb$subject${self.id}$',
            'fields': {
                'name': name,
                'dataset': f'$annotationweb$dataset${dataset.id}$',
            },
        })

    def add_image_sequence(self, format:str, nr_of_frames:int, start_frame_nr:int):
        return ImageSequence(self.serialization, format, nr_of_frames, start_frame_nr, self)


class Dataset(SerializationObject):
    counter = 1

    def __init__(self, serialization: Serialization, name: str):
        super().__init__(serialization, Dataset)
        serialization.add({
            'model': 'annotationweb.dataset',
            'pk': f'$annotationweb$dataset${self.id}$',
            'fields': {'name': name},
        })

    def add_subject(self, name):
        return Subject(self.serialization, name, self)


class Label(SerializationObject):
    counter = 1

    def __init__(self, serialization: Serialization, name: str, color_red:int, color_green:int, color_blue:int):
        super().__init__(serialization, Label)
        serialization.add({
            'model': 'annotationweb.label',
            'pk': f'$annotationweb$label${self.id}$',
            'fields': {
                'name': name,
                'color_red': color_red,
                'color_green': color_green,
                'color_blue': color_blue,
            },
        })


class Task(SerializationObject):
    counter = 1

    def __init__(self,
                 serialization: Serialization,
                 name: str,
                 type: str,
                 labels:List[Label],
                 datasets:List[Dataset] = None,
                 description: str = '',
                 show_entire_sequence:bool = True,
                 frames_before:int = 0,
                 frames_after:int = 0,
                 auto_play:bool = True,
                 shuffle_videos:bool = True,
                 user_frame_selection:bool = True,
                 annotate_single_frame:bool = True,
                 large_image_layout:bool = False,
                 post_processing_method:str = '',
             ):
        super().__init__(serialization, Task)
        label_ids = []
        for label in labels:
            label_ids.append(f'$annotationweb$label${label.id}$')
        dataset_ids = []
        for dataset in datasets:
            dataset_ids.append(f'$annotationweb$dataset${dataset.id}$')
        serialization.add({
            'model': 'annotationweb.task',
            'pk': f'$annotationweb$task${self.id}$',
            'fields': {
                'name': name,
                'type': type,
                'label': label_ids,
                'dataset': dataset_ids,
                'description': description,
                'show_entire_sequence': show_entire_sequence,
                'frames_before': frames_before,
                'frames_after': frames_after,
                'auto_play': auto_play,
                'shuffle_videos': shuffle_videos,
                'user_frame_selection': user_frame_selection,
                'annotate_single_frame': annotate_single_frame,
                'large_image_layout': large_image_layout,
                'post_processing_method': post_processing_method,
            },
        })

    def add_image_annotation(self,
                             image:ImageSequence,
                             image_quality:str,
                             comments:str,
                             finished:bool,
                             user=None,
                             date:datetime.datetime=datetime.datetime.now(),
                             rejected:bool=False
                         ):
        return ImageAnnotation(self.serialization, image, image_quality, comments, finished, user, date, rejected, self)


class ImageAnnotation(SerializationObject):
    counter = 1

    def __init__(self,
                 serialization: Serialization,
                 image:ImageSequence,
                 image_quality:str,
                 comments:str,
                 finished:bool,
                 user,
                 date:datetime.datetime,
                 rejected:bool,
                 task:Task
                 ):
        super().__init__(serialization, ImageAnnotation)
        serialization.add({
            'model': 'annotationweb.imageannotation',
            'pk': f'$annotationweb$imageannotation${self.id}$',
            'fields': {
                'image': f'$annotationweb$imagesequence${image.id}$',
                'task': f'$annotationweb$task${task.id}$',
                'user': None, # TODO
                'date': date,
                'image_quality': image_quality,
                'comments': comments,
                'rejected': rejected,
                'finished': finished,
            },
        })

    def add_key_frame_annotation(self, frame_nr:int, frame_metadata:str):
        return KeyFrameAnnotation(self.serialization, frame_nr, frame_metadata, self)


class KeyFrameAnnotation(SerializationObject):
    counter = 1

    def __init__(self, serialization: Serialization, frame_nr:int, frame_metadata:str, annotation:ImageAnnotation):
        super().__init__(serialization, KeyFrameAnnotation)
        serialization.add({
            'model': 'annotationweb.keyframeannotation',
            'pk': f'$annotationweb$keyframeannotation${self.id}$',
            'fields': {
                'image_annotation': f'$annotationweb$imageannotation${annotation.id}$',
                'frame_nr': frame_nr,
                'frame_metadata': frame_metadata,
            },
        })

