from abc import ABCMeta, abstractmethod


class SilKitPKG(metaclass=ABCMeta):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            callable(subclass.source_dir_name)
            and callable(subclass.setup_build_env)
            and callable(subclass.build)
            and callable(subclass.copy_artifacts)
            and callable(subclass.get_buildinfo)
        )

    @abstractmethod
    def source_dir_name(self):
        raise NotImplementedError

    @abstractmethod
    def setup_build_env(self):
        raise NotImplementedError

    @abstractmethod
    def build(self):
        raise NotImplementedError

    @abstractmethod
    def copy_artifacts(self):
        raise NotImplementedError

    @abstractmethod
    def get_buildinfo(self):
        raise NotImplementedError
