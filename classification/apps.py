from django.apps import AppConfig
from common.config import TaskConfig


class ClassificationConfig(AppConfig, TaskConfig):
    name = 'classification'

    @property
    def task_name(self):
        return 'Classification'
