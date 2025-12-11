from abc import ABC, abstractmethod


class TaskConfig(ABC):
    """
    Abstract base class for AW task apps. All task apps configs have to inherit from this and AppConfig.
    """

    @property
    def task_id(self):
        return self.name

    @property
    @abstractmethod
    def task_name(self):
        ...