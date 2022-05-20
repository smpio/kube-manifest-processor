from . import registry


class Filter:
    def __init_subclass__(cls, /, name=None, **kwargs):
        super().__init_subclass__(**kwargs)
        if name is not None:
            registry[name] = cls

    def process(self, obj):
        raise NotImplementedError
