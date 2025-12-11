from django.apps import AppConfig
from common.config import TaskConfig


class SplineLinePoint(AppConfig, TaskConfig):
    name = 'spline_line_point'

    @property
    def task_name(self):
        return 'Spline, Line and Point'

