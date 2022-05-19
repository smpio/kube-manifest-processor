import os

from .yaml import yaml


def get_reader(spec):
    if hasattr(spec, 'read') or not os.path.isdir(spec):
        return FileReader(spec)
    else:
        return DirReader(spec)


class DirReader:
    def __init__(self, path):
        self.root = path

    def __iter__(self):
        for root, dirs, files in os.walk(self.root, followlinks=True, onerror=reraise):
            for file in files:
                path = os.path.join(root, file)
                yield from read_file(path)


class FileReader:
    def __init__(self, spec):
        self.spec = spec

    def __iter__(self):
        yield from read_file(self.spec)


def read_file(spec):
    if hasattr(spec, 'read'):
        fp = spec
    else:
        fp = open(spec, 'r')
    return exclude_empty_documents(yaml.load_all(fp))


def exclude_empty_documents(docs):
    return (doc for doc in docs if doc is not None)


def reraise(err):
    raise err
