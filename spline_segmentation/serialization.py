from typing import Dict
from annotationweb.serialization import SerializationObject, Serialization, KeyFrameAnnotation, Label
from annotationweb.models import KeyFrameAnnotation as KeyFrameAnnotationModel
from spline_segmentation.models import ControlPoint


def serialize(serialization:Serialization, key_frame_model:KeyFrameAnnotationModel, key_frame:KeyFrameAnnotation, label_mapping:Dict[int, Label]):
    serialization_objects = []
    for point in ControlPoint.objects.filter(image=key_frame_model).order_by('index'):
        serialization_objects.append(SplineSegmentationControlPoint(serialization, point.x, point.y, point.index, point.object, point.uncertain, label_mapping[point.label.id], key_frame))
    return serialization_objects


class SplineSegmentationControlPoint(SerializationObject):
    counter = 1

    def __init__(self, serialization:Serialization, x:float, y:float, index:int, object:int, uncertain:bool, label:Label, image:KeyFrameAnnotation):
        super().__init__(serialization, SplineSegmentationControlPoint.counter)
        SplineSegmentationControlPoint.counter += 1
        serialization.add({
            'model': 'spline_segmentation.controlpoint',
            'pk': f'$spline_segmentation$controlpoint${self.id}$',
            'fields': {
                'image': f'$annotationweb$keyframeannotation${image.id}$',
                'label': f'$annotationweb$label${label.id}$',
                'x': x,
                'y': y,
                'index': index,
                'object': object,
                'uncertain': uncertain,
            },
        })