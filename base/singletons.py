from abc import ABCMeta


class SingletonABCMeta(ABCMeta):
    """
    Abstract Metaclass that allows creating
    only one instance of each children class
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls.__abstractmethods__:
            raise TypeError("Can't instantiate abstract class")
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]
