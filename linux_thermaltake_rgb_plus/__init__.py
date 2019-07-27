import logging
import os


logger = logging.getLogger(__name__)
DEBUG = bool(os.environ.get('DEBUG', False))


class ClassifiedObject:

    @classmethod
    def inheritors(cls):
        subclasses = set()
        work = [cls]
        while work:
            parent = work.pop()

            for child in parent.__subclasses__():
                if child not in subclasses:
                    print(child.__name__)
                    subclasses.add(child)
                    work.append(child)

        return subclasses


class Model(ClassifiedObject):
    def __init__(self, config):
        raise NotImplementedError

    @classmethod
    def factory(cls, config: dict):
        raise NotImplementedError


class Manager(ClassifiedObject):
    def __init__(self, initial_model: Model = None, name: str = None):
        self._name = name
        self._devices = []
        self.set_model(initial_model)

    def attach_device(self, device):
        self._devices.append(device)

    def set_model(self, model: Model):
        raise NotImplementedError

    def start(self):
        raise NotImplementedError

    def stop(self):
        raise NotImplementedError

