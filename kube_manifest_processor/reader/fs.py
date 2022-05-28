import os

from ..yaml import YAML


class DirReader:
    def __init__(self, path):
        self.root = path

    def __iter__(self):
        for root, dirs, files in os.walk(self.root, followlinks=True, onerror=reraise):
            for file in files:
                path = os.path.join(root, file)
                with open(path, 'r') as fp:
                    yield from read_fp(fp)


class StreamReader:
    def __init__(self, spec):
        self.spec = spec

    def __iter__(self):
        return read_fp(self.spec)


def read_fp(fp):
    return exclude_empty_documents(YAML().load_all(fp))


def exclude_empty_documents(docs):
    return (doc for doc in docs if doc is not None)


def reraise(err):
    raise err
